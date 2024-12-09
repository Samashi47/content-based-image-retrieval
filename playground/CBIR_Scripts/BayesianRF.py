from CBIR_Scripts.SimpleSearch import *
import pymc as pm

def calc_similarities(distances, weights=None):
    if weights is None:
        weights = {
            'dominant_colors': 0.5,
            'color_histogram': 0.5,
            'fourier_descriptors': 0.5,
            'hu_moments': 0.5,
            'edge_histogram': 0.5,
            'gabor': 0.5
        }
    
    total_weight = sum(weights.values())
    similarities = []
    individual_sims = []
    
    for doc, dist_metrics in distances:
        texture_similarity = (weights['gabor'] * (1 / (1 + dist_metrics['gabor'])) + 
                            weights['edge_histogram'] * (1 / (1 + dist_metrics['edge_histogram'])))
        
        color_similarity = (weights['dominant_colors'] * (1 / (1 + dist_metrics['dominant_colors'])) +
                          weights['color_histogram'] * (1 / (1 + dist_metrics['color_histogram'])))
        
        shape_similarity = (weights['hu_moments'] * (1 / (1 + dist_metrics['hu_moments'])) +
                          weights['fourier_descriptors'] * (1 / (1 + dist_metrics['fourier_descriptors'])))
        
        similarity = (color_similarity + texture_similarity + shape_similarity) / total_weight
        
        similarities.append((doc, similarity))
        individual_sims.append({
            'color_histogram': 1 / (1 + dist_metrics['color_histogram']),
            'dominant_colors': 1 / (1 + dist_metrics['dominant_colors']),
            'edge_histogram': 1 / (1 + dist_metrics['edge_histogram']),
            'gabor': 1 / (1 + dist_metrics['gabor']),
            'hu_moments': 1 / (1 + dist_metrics['hu_moments']),
            'fourier_descriptors': 1 / (1 + dist_metrics['fourier_descriptors'])
        })
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities, individual_sims

def normalize_weights(weights):
    total = sum(weights.values())
    return {k: v/total for k, v in weights.items()}

def constrain_weights(weights, min_val=0.0, max_val=1.0):
    return {k: max(min_val, min(v, max_val)) for k, v in weights.items()}

def update_weights_smoothly(old_weights, new_weights, learning_rate=0.1):
    return {k: old_weights[k] + learning_rate * (new_weights[k] - old_weights[k]) 
            for k in old_weights}
    
def update_weights(feedback_data, initial_weights):
    features = [list(feed['features'].values()) for feed in feedback_data]
    labels = [feed['label'] for feed in feedback_data]
    
    features = np.array(features)
    labels = np.array(labels)
    num_features = features.shape[1]
    
    with pm.Model() as model:
        weights = pm.Normal('weights', mu=initial_weights, sigma=1.0, shape=num_features)
        mu = pm.math.dot(features, weights)
        p = pm.invlogit(mu)
        likelihood = pm.Bernoulli('likelihood', p=p, observed=labels)
        
        trace = pm.sample(draws=2000, tune=1000, return_inferencedata=False)
    
    updated_weights = trace['weights'].mean(axis=0)
    return updated_weights

def collect_feedback(top_images, individual_sims):
    feedback_data = []
    for i, (img_name, _) in enumerate(top_images):
        response = input(f"Is the image {img_name} relevant? (y/n): ")
        if response.lower() == 'y':
            label = 1
        else:
            label = 0
        feedback_data.append({
            'features': individual_sims[i],
            'label': label
        })
    return feedback_data

def RFSearch(weights, source_folder, dest_folder, rand_img, n=15):
    query_desc = process_query_image(rand_img, dest_folder)
    if query_desc is None:
        print("Invalid query image.")
        return weight_history
    if weights is None:
        weights = {
            'dominant_colors': 0.5,
            'color_histogram': 0.5,
            'fourier_descriptors': 0.5,
            'hu_moments': 0.5,
            'edge_histogram': 0.5,
            'gabor': 0.5
        }
    weight_history = [weights.copy()]
    collection = connect_to_db()
    db_desc = list(collection.find())
    distances = compute_distances(query_desc, db_desc)
    similarities, individual_sims = calc_similarities(distances, weights)
    top_images = get_top_images(similarities, n)
    plot_images(source_folder, dest_folder, rand_img, top_images, similarities, n)
    
    plt.draw()
    plt.pause(0.001)
    while True:
        response = input("Do you want to provide feedback? (y/n): ")
        if response.lower() != 'y':
            break
        
        feedback_data = collect_feedback(top_images, individual_sims)
        
            # Update weights using Bayesian logistic regression
        initial_weights = np.array([weights[key] for key in ['color_histogram', 'dominant_colors', 'edge_histogram', 'gabor', 'hu_moments', 'fourier_descriptors']])
        updated_weights = update_weights(feedback_data, initial_weights)
        
        # Update weights dictionary
        weight_keys = ['color_histogram', 'dominant_colors', 'edge_histogram', 'gabor', 'hu_moments', 'fourier_descriptors']
        weights_dict = weights.copy()  # Create a copy of the original weights dictionary
        for key, value in zip(weight_keys, updated_weights):
            weights_dict[key] = value
            
        weights = update_weights_smoothly(weights, weights_dict, 0.5)
        weights = normalize_weights(weights)
        weights = constrain_weights(weights)
        weight_history.append(weights.copy())
        similarities, individual_sims = calc_similarities(distances, weights)
        top_images = get_top_images(similarities, n)
        plot_images(source_folder, dest_folder, rand_img, top_images, similarities, n)
        plt.draw()
        plt.pause(0.001)
        
    return weight_history