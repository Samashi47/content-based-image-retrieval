from email.mime import image
import re
from turtle import color
from urllib import response
import cv2
from flask import Response, request, Flask
from flask_cors import CORS
import json
import random
import datetime
import hashlib
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import jwt
import os
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from logic.descriptors import get_dominant_colors, get_color_histogram, get_hu_moments
from logic.search_helpers import (
    process_query_image,
    SimpleSearch,
    AdvancedSearch,
    RelevanceFeedbackSearch,
)
from PIL import Image
import numpy as np
import cv2
import base64
import dotenv


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


app = Flask(__name__)
CORS(app)


@app.route("/", methods=["POST"])
def home():
    print(request.json)
    return "Hello, World!"


@app.route("/auth/login", methods=["POST"])
def login():
    hash_func = hashlib.sha256()
    data = request.json
    hash_func.update(data["password"].encode())
    hashed_password = hash_func.hexdigest()
    hash_func = hashlib.sha256()
    hash_func.update("12345678".encode())
    test_hashed_password = hash_func.hexdigest()

    if data["email"] == "test@test.com" and hashed_password == test_hashed_password:
        private_key = open(".ssh/jwt-key", "rb").read()
        key = load_pem_private_key(
            private_key, password=None, backend=default_backend()
        )
        payload = {
            "email": "test@test.com",
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        }
        token = jwt.encode(payload, key, algorithm="RS256")

        return Response(
            json.dumps({"token": token}), mimetype="application/json", status=200
        )
    else:
        return Response(
            json.dumps({"message": "Login Failed"}),
            mimetype="application/json",
            status=401,
        )


@app.route("/image/simple-search", methods=["POST"])
def simple_search():
    if "image" not in request.files:
        return Response(
            json.dumps({"message": "No file part"}),
            mimetype="application/json",
            status=400,
        )

    image = request.files["image"]
    if image.filename == "":
        return Response(
            json.dumps({"message": "No selected file"}),
            mimetype="application/json",
            status=400,
        )

    print(f"Received image: {image.filename}")
    query_desc = process_query_image(image)
    top_images = SimpleSearch(query_desc, n=15)

    response_dict = [
        {
            "title": img_path.replace("RSSCN7/", ""),
            "image": encode_image_to_base64(img_path),
            "similarity": sim,
        }
        for img_path, sim in top_images
    ]

    response = Response(
        json.dumps(response_dict), mimetype="application/json", status=200
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Credentials"] = True

    return response


@app.route("/image/advanced-search", methods=["POST"])
def advanced_search():
    if "image" not in request.files:
        return Response(
            json.dumps({"message": "No file part"}),
            mimetype="application/json",
            status=400,
        )

    image = request.files["image"]
    if image.filename == "":
        return Response(
            json.dumps({"message": "No selected file"}),
            mimetype="application/json",
            status=400,
        )

    print(f"Received image: {image.filename}")
    query_desc = process_query_image(image)
    top_images, weights, individual_sims = AdvancedSearch(query_desc, n=15)

    query_desc["individual_sims"] = individual_sims
    query_desc["top_image_names"] = [
        re.sub(r"RSSCN7\\\w+\\", "", img_path) for img_path, _ in top_images
    ]
    print(query_desc["top_image_names"])
    query_desc["weights"] = weights
    dotenv.load_dotenv()
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client["RSSCN7"]
    collection = db["temp_queries_desc"]
    res = collection.insert_one(query_desc)

    _id = res.inserted_id

    response_dict = {
        "images": [
            {
                "title": img_path.replace("RSSCN7/", ""),
                "image": encode_image_to_base64(img_path),
                "similarity": sim,
            }
            for img_path, sim in top_images
        ],
        "query_id": str(_id),
    }

    response = Response(
        json.dumps(response_dict), mimetype="application/json", status=200
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Credentials"] = True

    return response


@app.route("/image/relevance-feedback", methods=["POST"])
def relevance_feedback():
    data = request.json
    feedback_data = json.loads(data["relevance"])
    query_id = data["query_id"]
    print(f"Received feedback for query: {query_id}")
    print(type(feedback_data[0]))
    dotenv.load_dotenv()
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client["RSSCN7"]
    collection = db["temp_queries_desc"]
    query_desc = collection.find({"_id": ObjectId(query_id)})
    query_desc = list(query_desc)

    if not query_desc or len(query_desc) == 0:
        return Response(
            json.dumps({"message": "Query not found"}),
            mimetype="application/json",
            status=404,
        )

    top_image_names = query_desc[0]["top_image_names"]
    print(top_image_names)
    weights = query_desc[0]["weights"]

    individual_sims = sorted(
        [
            sim
            for sim in query_desc[0]["individual_sims"]
            if sim["image_name"] in top_image_names
        ],
        key=lambda sim: top_image_names.index(sim["image_name"]),
    )

    top_images, weights, individual_sims = RelevanceFeedbackSearch(
        query_desc[0], feedback_data, individual_sims, weights, n=15
    )

    collection.update_one(
        {"_id": ObjectId(query_id)},
        {
            "$set": {
                "individual_sims": individual_sims,
                "top_image_names": top_image_names,
                "weights": weights,
            }
        },
    )

    response_dict = {
        "images": [
            {
                "title": img_path.replace("RSSCN7/", ""),
                "image": encode_image_to_base64(img_path),
                "similarity": sim,
            }
            for img_path, sim in top_images
        ],
        "query_id": query_id,
    }

    response = Response(
        json.dumps(response_dict), mimetype="application/json", status=200
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Credentials"] = True

    return response


@app.route("/image/descriptors", methods=["POST"])
def image_descriptors():
    if "image" not in request.files:
        return Response(
            json.dumps({"message": "No file part"}),
            mimetype="application/json",
            status=400,
        )

    image = request.files["image"]
    if image.filename == "":
        return Response(
            json.dumps({"message": "No selected file"}),
            mimetype="application/json",
            status=400,
        )

    image = Image.open(image)
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    dominant_colors = get_dominant_colors(image)
    color_histogram = get_color_histogram(image)
    hu_moments = get_hu_moments(image)

    response = Response(
        json.dumps(
            {
                "dominant_colors": dominant_colors,
                "color_histogram": color_histogram,
                "hu_moments": hu_moments,
            }
        ),
        mimetype="application/json",
        status=200,
    )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Credentials"] = True

    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
