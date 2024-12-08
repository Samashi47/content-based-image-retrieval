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

def RFSearch(source_folder, dest_folder, rand_img, query_desc, general_weights, weights, distances, top_images, n=15):
    if query_desc is None:
        print("Invalid query image.")
        return weights, None
    
    # Display top images and collect feedback
    feedback_data = []
    # for i, (img_name, sim) in enumerate(top_images):
    #     print(f"{i}: {img_name} - Similarity: {sim:.5f}")
    relevant_indices = input("Enter indices of relevant images separated by spaces (e.g., '0 2 4'): ")
    relevant_indices = list(map(int, relevant_indices.strip().split()))
    
    similarities, individual_sims = calc_similarities(distances, weights)
    
    for i, (img_name, sim) in enumerate(top_images):
        if i in relevant_indices:
            label = 1
        else:
            label = 0
        feedback_data.append({
            'features': individual_sims[i],
            'label': label
        })
    
    # Update weights using Bayesian logistic regression
    initial_weights = np.array([weights[key] for key in ['color_histogram', 'dominant_colors', 'edge_histogram', 'gabor', 'hu_moments', 'fourier_descriptors']])
    updated_weights = update_weights(feedback_data, initial_weights)
    
    # Update weights dictionary
    weight_keys = ['color_histogram', 'dominant_colors', 'edge_histogram', 'gabor', 'hu_moments', 'fourier_descriptors']
    weights_dict = weights.copy()  # Create a copy of the original weights dictionary
    for key, value in zip(weight_keys, updated_weights):
        weights_dict[key] = value
    
    similarities, individual_sims = calc_similarities(distances, weights)
    top_images = get_top_images(similarities, n)
    plot_images(source_folder, dest_folder, rand_img, top_images, similarities, n)
    
    return weights_dict

def run_rf_loop(rand_img, weights, general_weights, source_folder, dest_folder):
    continue_feedback = True
    weight_history = []
    query_desc = process_query_image(rand_img, dest_folder)
    top_images, distances = SimpleSearch(source_folder, dest_folder, query_desc, general_weights, weights, rand_img, n=15)
    
    plt.draw()
    plt.pause(0.001)
    response = input("Do you want to provide feedback? (y/n): ")
    
    if response.lower() != 'y':
        continue_feedback = False
        
    while continue_feedback:
        weight_history.append(weights.copy())
        new_weights = RFSearch(source_folder, dest_folder, rand_img, query_desc, general_weights, weights, distances, top_images, n=15)
        weights = update_weights_smoothly(weights, new_weights, 0.1)
        
        # Normalize weights
        weights = normalize_weights(weights)
        
        # Constrain weights to valid range
        weights = constrain_weights(weights)
        response = input("Do you want to provide more feedback? (y/n): ")
        if response.lower() != 'y':
            continue_feedback = False
            
    return weight_history