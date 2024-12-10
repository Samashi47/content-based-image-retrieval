from pymongo import MongoClient
from logic.descriptors import *
from PIL import Image
import os

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

def simple_similarity_calc(distances):
    general_weights = {
        'color': 1/3,
        'texture': 1/3,
        'shape': 1/3
    }
    weights = {
        'dominant_colors': 0.5,
        'color_histogram': 0.5,
        'fourier_descriptors': 0.5,
        'hu_moments': 0.5,
        'edge_histogram': 0.5,
        'gabor': 0.5
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

def process_query_image(image):
    image = Image.open(image)
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
        'dominant_colors': dominant_colors,
        'gabor': gabor,
        'color_histogram': color_hist,
        'hu_moments': hu_moments,
        'edge_histogram': edge_hist,
        'fourier_descriptors': fourier_desc
    }

def get_top_images(similarities, x=15):
    top = similarities[:x]
    return [ (os.path.join("apps\\api\\RSSCN7",doc['category'],doc['image_name']), sim) for doc, sim in top ]

def connect_to_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['RSSCN7']
    collection = db['descriptors']
    return collection

def SimpleSearch(query_desc, n=15):
    if query_desc is None:
        print("Invalid query image.")
    else:
        collection = connect_to_db()
        db_desc = list(collection.find())
        distances = compute_distances(query_desc, db_desc)
        similarities = simple_similarity_calc(distances)
        print(similarities[0])
        top_images = get_top_images(similarities, n)
        
        return top_images