from CBIR_Scripts.SimpleSearch import *
from PIL import Image

def RF(dest_folder, source_folder, weights, general_weights, top_images, distances, rand_img, n=15):
    feedback = {}
    print(f"Please provide feedback for the top {n} images.")
    for i, (img_name, sim) in enumerate(top_images):
        feedback_label = input(f"Is {img_name} relevant? (y/n): ")
        feedback[img_name] = feedback_label.lower() == 'y'

    alpha = 1.0
    num_descriptors = len(weights)
    prior_relevant = alpha / num_descriptors
    prior_irrelevant = alpha / num_descriptors

    relevant_counts = {desc: 0 for desc in weights}
    irrelevant_counts = {desc: 0 for desc in weights}

    collection = connect_to_db()
    
    for img_name, is_relevant in feedback.items():
        feedback_doc = collection.find_one({'image_name': img_name})
        if feedback_doc:
            for desc in weights:
                if desc in feedback_doc:
                    if is_relevant:
                        relevant_counts[desc] += 1
                    else:
                        irrelevant_counts[desc] += 1

    for desc in weights:
        prob_relevant = (relevant_counts[desc] + prior_relevant) / \
                        (relevant_counts[desc] + irrelevant_counts[desc] + prior_relevant + prior_irrelevant)
        weights[desc] = prob_relevant

    weight_sum = sum(weights.values())
    weights = {desc: w / weight_sum for desc, w in weights.items()}
    db_desc = list(collection.find())
    
    similarities = calculate_similarities(distances, general_weights=general_weights, weights=weights)
    
    top_images = get_top_images(similarities, n)
    rows = 4
    cols = (n + 1) // rows + ((n + 1) % rows > 0)
    _, axes = plt.subplots(rows, cols, figsize=(15, 15))

    img1 = Image.open(os.path.join(dest_folder, rand_img))
    axes[0, 0].imshow(img1)
    axes[0, 0].set_title(f"Source:\n{rand_img}")
    axes[0, 0].axis("off")
    
    for i, (img_name, sim) in enumerate(top_images):
        row = (i + 1) // cols
        col = (i + 1) % cols
        img_path = os.path.join(source_folder, similarities[i][0]['category'], img_name)
        img2 = Image.open(img_path)
        axes[row, col].imshow(img2, cmap='gray')
        axes[row, col].set_title(f"{similarities[i][0]['category']} - {img_name}\nSimilarity: {sim:.5f}")
        axes[row, col].axis("off")
    plt.tight_layout()
    plt.show()
    
    return weights, general_weights, top_images, similarities

