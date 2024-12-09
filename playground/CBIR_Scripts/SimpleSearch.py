import os
import cv2
import numpy as np
from sklearn.cluster import KMeans
from pymongo import MongoClient
import matplotlib.pyplot as plt
import random
import shutil

def create_query_db(source_folder, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    else:
        shutil.rmtree(dest_folder)
        os.makedirs(dest_folder)
        
    for category in os.listdir(source_folder):
        category_path = os.path.join(source_folder, category)
        if not os.path.isdir(category_path):
            continue
        
        images = [img for img in os.listdir(category_path) if img.endswith(('.jpg', '.jpeg', '.png'))]
        random_images = random.sample(images, min(10, len(images)))
        
        for img_name in random_images:
            src_path = os.path.join(category_path, img_name)
            dest_path = os.path.join(dest_folder, img_name)
            shutil.copy(src_path, dest_path)

def get_dominant_colors(image, k=16):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image.reshape(-1, 3)
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)
    return kmeans.cluster_centers_.tolist()

def get_gabor_texture(image):
    def build_gabor_filters():
        filters = []
        for theta in range(4):
            theta = theta * 45
            for sigma in (3, 5):
                for frequency in (0.01, 0.05):
                    kernel = cv2.getGaborKernel((5, 5), sigma, theta, frequency, 0.5, 0, ktype=cv2.CV_32F)
                    filters.append(kernel)
        return filters
    filters = build_gabor_filters()
    responses = []
    for kernel in filters:
        filtered = cv2.filter2D(image, cv2.CV_8UC3, kernel)
        responses.append(filtered.mean())
    return responses

def get_color_histogram(image, bins=256):
    channels = cv2.split(image)
    histograms = []
    for channel in channels:
        hist = cv2.calcHist([channel], [0], None, [bins], [0, 256])
        cv2.normalize(hist, hist)
        histograms.append(hist.flatten().tolist())
    return histograms


def get_hu_moments(image):
    epsilon = 1e-10
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [0.0] * 7
    contour = max(contours, key=cv2.contourArea)
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments)
    hu = [-np.log10(np.abs(h) + epsilon).item() for h in hu]
    return hu


def get_edge_histogram(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    hist = cv2.calcHist([edges], [0], None, [256], [0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten().tolist()

def get_fourier_descriptors(image, n=20):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [0.0] * (2 * n)
    contour = max(contours, key=cv2.contourArea)
    contour = contour.reshape(-1, 2).T
    fourier = np.fft.fft(contour, n=n, axis=1)
    magnitudes = np.abs(fourier)
    return magnitudes.flatten().tolist()

def connect_to_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['RSSCN7']
    collection = db['descriptors']
    return collection


def process_database_images(root_folder, not_indexed):
    
    collection = connect_to_db()
    
    for category in os.listdir(root_folder):
        category_path = os.path.join(root_folder, category)
        if not os.path.isdir(category_path):
            continue
        for img_name in os.listdir(category_path):
            img_path = os.path.join(category_path, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            if img_name in not_indexed:
                continue
            img = cv2.resize(img, (400, 400))
            dominant_colors = get_dominant_colors(img)
            gabor = get_gabor_texture(img)
            color_hist = get_color_histogram(img)
            hu_moments = get_hu_moments(img)
            edge_hist = get_edge_histogram(img)
            fourier_desc = get_fourier_descriptors(img)
            # Store in MongoDB
            doc = {
                'image_name': img_name,
                'category': category,
                'dominant_colors': dominant_colors,
                'gabor': gabor,
                'color_histogram': color_hist,
                'hu_moments': hu_moments,
                'edge_histogram': edge_hist,
                'fourier_descriptors': fourier_desc
            }
            collection.insert_one(doc)

def compute_distances(query_desc, db_desc):
    """Calculate distances between query image and database images for each feature"""
    c_hist1 = np.array(query_desc['color_histogram'], dtype=np.float32)
    e_hist1 = np.array(query_desc['edge_histogram'], dtype=np.float32)
    
    distances = []
    for doc in db_desc:
        c_hist2 = np.array(doc['color_histogram'], dtype=np.float32)
        dist_metrics = {
            'gabor': np.linalg.norm(np.array(query_desc['gabor']) - np.array(doc['gabor'])),
            'edge_histogram': cv2.compareHist(e_hist1, 
                                            np.array(doc['edge_histogram'], dtype=np.float32), 
                                            cv2.HISTCMP_CHISQR),
            'dominant_colors': np.linalg.norm(np.array(query_desc['dominant_colors']) - 
                                            np.array(doc['dominant_colors'])),
            'color_histogram': sum(cv2.compareHist(c1, c2, cv2.HISTCMP_CHISQR) for c1, c2 in zip(c_hist1, c_hist2))/3,
            'hu_moments': np.linalg.norm(np.array(query_desc['hu_moments']) - 
                                       np.array(doc['hu_moments'])),
            'fourier_descriptors': np.linalg.norm(np.array(query_desc['fourier_descriptors']) - 
                                                np.array(doc['fourier_descriptors']))
        }
        distances.append((doc, dist_metrics))
    return distances

def calculate_similarities(distances, general_weights=None, weights=None):
    """Calculate final similarity scores using the pre-computed distances"""
    if general_weights is None:
        general_weights = {
            'color': 1/3,
            'texture': 1/3,
            'shape': 1/3
        }
    
    if weights is None:
        weights = {
            'dominant_colors': 0.3,
            'color_histogram': 0.5,
            'fourier_descriptors': 0.5,
            'hu_moments': 0.5,
            'edge_histogram': 0.3,
            'gabor': 0.7
        }

    total_weight = sum(general_weights.values())
    similarities = []
    
    for doc, dist_metrics in distances:
        texture_similarity = (weights['gabor'] * (1 / (1 + dist_metrics['gabor'])) + 
                            weights['edge_histogram'] * (1 / (1 + dist_metrics['edge_histogram'])))
        
        color_similarity = (weights['dominant_colors'] * (1 / (1 + dist_metrics['dominant_colors'])) +
                          weights['color_histogram'] * (1 / (1 + dist_metrics['color_histogram'])))
        
        shape_similarity = (weights['hu_moments'] * (1 / (1 + dist_metrics['hu_moments'])) +
                          weights['fourier_descriptors'] * (1 / (1 + dist_metrics['fourier_descriptors'])))

        similarity = (general_weights['color'] * color_similarity + 
                     general_weights['texture'] * texture_similarity +
                     general_weights['shape'] * shape_similarity) / total_weight
        
        similarities.append((doc, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities

def get_top_images(similarities, x=5):
    top = similarities[:x]
    return [ (doc['image_name'], sim) for doc, sim in top ]

def process_query_image(rand_img, dest_folder):
    query_path = os.path.join(dest_folder, rand_img)
    img = cv2.imread(query_path)
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
        'dominant_colors': dominant_colors,
        'gabor': gabor,
        'color_histogram': color_hist,
        'hu_moments': hu_moments,
        'edge_histogram': edge_hist,
        'fourier_descriptors': fourier_desc
    }
    
def plot_images(source_folder, dest_folder, rand_img, top_images, similarities, n=15):
    rows = 4
    cols = (n + 1) // rows + ((n + 1) % rows > 0)
    _, axes = plt.subplots(rows, cols, figsize=(10, 10))

    img1 = cv2.cvtColor(cv2.imread(os.path.join(dest_folder, rand_img)), cv2.COLOR_BGR2RGB)
    axes[0, 0].imshow(img1)
    axes[0, 0].set_title(f"Source:\n{rand_img}")
    axes[0, 0].axis("off")
    for i, (img_name, sim) in enumerate(top_images):
        row = (i + 1) // cols
        col = (i + 1) % cols
        img_path = os.path.join(source_folder, similarities[i][0]['category'], img_name)
        img2 = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
        axes[row, col].imshow(img2, cmap='gray')
        axes[row, col].set_title(f"{similarities[i][0]['category']} - {img_name}\nSimilarity: {sim:.5f}")
        axes[row, col].axis("off")
    plt.tight_layout()
    plt.show()


def SimpleSearch(source_folder, dest_folder, query_desc, general_weights, weights, rand_img, n=15):
    if query_desc is None:
        print("Invalid query image.")
    else:
        collection = connect_to_db()
        db_desc = list(collection.find())
        distances = compute_distances(query_desc, db_desc)
        similarities = calculate_similarities(distances, general_weights=general_weights, weights=weights)
        top_images = get_top_images(similarities, n)
        
        plot_images(source_folder, dest_folder, rand_img, top_images, similarities, n)
        
        return top_images, distances