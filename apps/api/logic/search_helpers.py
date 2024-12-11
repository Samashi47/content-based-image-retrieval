from pymongo import MongoClient
from logic.descriptors import *
from PIL import Image
import os
import dotenv
import pymc3 as pm


def compute_distances(query_desc, db_desc):
    """Calculate distances between query image and database images for each feature"""
    c_hist1 = np.array(query_desc["color_histogram"], dtype=np.float32)
    e_hist1 = np.array(query_desc["edge_histogram"], dtype=np.float32)

    distances = []
    for doc in db_desc:
        c_hist2 = np.array(doc["color_histogram"], dtype=np.float32)
        dist_metrics = {
            "gabor": np.linalg.norm(
                np.array(query_desc["gabor"]) - np.array(doc["gabor"])
            ),
            "edge_histogram": cv2.compareHist(
                e_hist1,
                np.array(doc["edge_histogram"], dtype=np.float32),
                cv2.HISTCMP_CHISQR,
            ),
            "dominant_colors": np.linalg.norm(
                np.array(query_desc["dominant_colors"])
                - np.array(doc["dominant_colors"])
            ),
            "color_histogram": sum(
                cv2.compareHist(c1, c2, cv2.HISTCMP_CHISQR)
                for c1, c2 in zip(c_hist1, c_hist2)
            )
            / 3,
            "hu_moments": np.linalg.norm(
                np.array(query_desc["hu_moments"]) - np.array(doc["hu_moments"])
            ),
            "fourier_descriptors": np.linalg.norm(
                np.array(query_desc["fourier_descriptors"])
                - np.array(doc["fourier_descriptors"])
            ),
        }
        distances.append((doc, dist_metrics))
    return distances


def simple_similarity_calc(distances):
    general_weights = {"color": 1 / 3, "texture": 1 / 3, "shape": 1 / 3}
    weights = {
        "dominant_colors": 0.5,
        "color_histogram": 0.5,
        "fourier_descriptors": 0.5,
        "hu_moments": 0.5,
        "edge_histogram": 0.5,
        "gabor": 0.5,
    }

    total_weight = sum(general_weights.values())
    similarities = []

    for doc, dist_metrics in distances:
        texture_similarity = weights["gabor"] * (
            1 / (1 + dist_metrics["gabor"])
        ) + weights["edge_histogram"] * (1 / (1 + dist_metrics["edge_histogram"]))

        color_similarity = weights["dominant_colors"] * (
            1 / (1 + dist_metrics["dominant_colors"])
        ) + weights["color_histogram"] * (1 / (1 + dist_metrics["color_histogram"]))

        shape_similarity = weights["hu_moments"] * (
            1 / (1 + dist_metrics["hu_moments"])
        ) + weights["fourier_descriptors"] * (
            1 / (1 + dist_metrics["fourier_descriptors"])
        )

        similarity = (
            general_weights["color"] * color_similarity
            + general_weights["texture"] * texture_similarity
            + general_weights["shape"] * shape_similarity
        ) / total_weight

        similarities.append((doc, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities


def advanced_similarity_calc(distances, weights=None):
    if weights is None:
        weights = {
            "dominant_colors": 0.5,
            "color_histogram": 0.5,
            "fourier_descriptors": 0.5,
            "hu_moments": 0.5,
            "edge_histogram": 0.5,
            "gabor": 0.5,
        }

    total_weight = sum(weights.values())
    similarities = []
    individual_sims = []

    for doc, dist_metrics in distances:
        texture_similarity = weights["gabor"] * (
            1 / (1 + dist_metrics["gabor"])
        ) + weights["edge_histogram"] * (1 / (1 + dist_metrics["edge_histogram"]))

        color_similarity = weights["dominant_colors"] * (
            1 / (1 + dist_metrics["dominant_colors"])
        ) + weights["color_histogram"] * (1 / (1 + dist_metrics["color_histogram"]))

        shape_similarity = weights["hu_moments"] * (
            1 / (1 + dist_metrics["hu_moments"])
        ) + weights["fourier_descriptors"] * (
            1 / (1 + dist_metrics["fourier_descriptors"])
        )

        similarity = (
            color_similarity + texture_similarity + shape_similarity
        ) / total_weight

        similarities.append((doc, similarity))
        individual_sims.append(
            {
                "image_name": doc["image_name"],
                "color_histogram": 1 / (1 + dist_metrics["color_histogram"]),
                "dominant_colors": 1 / (1 + dist_metrics["dominant_colors"]),
                "edge_histogram": 1 / (1 + dist_metrics["edge_histogram"]),
                "gabor": 1 / (1 + dist_metrics["gabor"]),
                "hu_moments": 1 / (1 + dist_metrics["hu_moments"]),
                "fourier_descriptors": 1 / (1 + dist_metrics["fourier_descriptors"]),
            }
        )

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities, individual_sims


def process_query_image(image_path):
    image = Image.open(image_path)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    if img is None:
        return None
    img = cv2.resize(img, (400, 400))
    dominant_colors = get_dominant_colors(img)
    gabor = get_gabor_texture(img)
    color_hist = get_color_histogram(img)
    hu_moments = get_hu_moments(img)
    edge_hist = get_edge_histogram(img)
    fourier_desc = get_fourier_descriptors(img)
    return {
        "image_name": image_path.filename,
        "dominant_colors": dominant_colors,
        "gabor": gabor,
        "color_histogram": color_hist,
        "hu_moments": hu_moments,
        "edge_histogram": edge_hist,
        "fourier_descriptors": fourier_desc,
    }


def get_top_images(similarities, x=15):
    top = similarities[:x]
    return [
        (os.path.join("RSSCN7", doc["category"], doc["image_name"]), sim)
        for doc, sim in top
    ]


def connect_to_db():
    dotenv.load_dotenv()
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client["RSSCN7"]
    collection = db["descriptors"]
    return collection


def normalize_weights(weights):
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def constrain_weights(weights, min_val=0.0, max_val=1.0):
    return {k: max(min_val, min(v, max_val)) for k, v in weights.items()}


def update_weights_smoothly(old_weights, new_weights, learning_rate=0.1):
    return {
        k: old_weights[k] + learning_rate * (new_weights[k] - old_weights[k])
        for k in old_weights
    }


def update_weights(feedback_data, initial_weights):
    features = [list(feed["features"].values())[1:] for feed in feedback_data]
    labels = [feed["label"] for feed in feedback_data]

    features = np.array(features)
    labels = np.array(labels)
    print(features.shape, labels.shape)
    num_features = features.shape[1]

    with pm.Model() as model:
        weights = pm.Normal(
            "weights", mu=initial_weights, sigma=1.0, shape=num_features
        )
        mu = pm.math.dot(features, weights)
        p = pm.invlogit(mu)
        likelihood = pm.Bernoulli("likelihood", p=p, observed=labels)

        trace = pm.sample(draws=2000, tune=1000, return_inferencedata=False)

    updated_weights = trace["weights"].mean(axis=0)
    return updated_weights


def process_feedback(feedback_data, individual_sims):
    feedback = []
    for i in range(len(feedback_data)):
        feedback.append({"features": individual_sims[i], "label": feedback_data[i]})
    return feedback


def SimpleSearch(query_desc, n=15):
    if query_desc is None:
        print("Invalid query image.")
    else:
        collection = connect_to_db()
        db_desc = list(collection.find())
        distances = compute_distances(query_desc, db_desc)
        similarities = simple_similarity_calc(distances)
        top_images = get_top_images(similarities, n)

        return top_images


def AdvancedSearch(query_desc, n=15):
    weights = {
        "dominant_colors": 0.5,
        "color_histogram": 0.5,
        "fourier_descriptors": 0.5,
        "hu_moments": 0.5,
        "edge_histogram": 0.5,
        "gabor": 0.5,
    }
    if query_desc is None:
        print("Invalid query image.")
    else:
        collection = connect_to_db()
        db_desc = list(collection.find())
        distances = compute_distances(query_desc, db_desc)
        similarities, individual_sims = advanced_similarity_calc(distances, weights)
        top_images = get_top_images(similarities, n)

        return top_images, weights, individual_sims


def RelevanceFeedbackSearch(query_desc, feedback_data, individual_sims, weights, n=15):

    feedback = process_feedback(feedback_data, individual_sims)
    weight_keys = [
        "color_histogram",
        "dominant_colors",
        "edge_histogram",
        "gabor",
        "hu_moments",
        "fourier_descriptors",
    ]

    initial_weights = np.array([weights[key] for key in weight_keys])
    updated_weights = update_weights(feedback, initial_weights)

    weights_dict = weights.copy()
    for key, value in zip(weight_keys, updated_weights):
        weights_dict[key] = value

    weights = update_weights_smoothly(weights, weights_dict, 0.5)
    weights = normalize_weights(weights)
    weights = constrain_weights(weights)

    db_desc = list(connect_to_db().find())
    distances = compute_distances(query_desc, db_desc)
    similarities, individual_sims = advanced_similarity_calc(distances, weights)
    top_images = get_top_images(similarities, n)

    return top_images, weights, individual_sims
