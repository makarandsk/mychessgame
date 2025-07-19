# In classify_squares.py
def classify_all_squares(squares_dir='extracted_squares', model_path='piece_style_classifier.h5', img_size=(96, 96)):
    import os
    import numpy as np
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.image import load_img, img_to_array
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    import csv

    model = load_model(model_path)
    results = []
    for fname in sorted(os.listdir(squares_dir)):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            continue
        img_path = os.path.join(squares_dir, fname)
        img = load_img(img_path, target_size=img_size)
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        pred = model.predict(x)[0][0]
        label = 'accepted' if pred < 0.5 else 'rejected'
        print(f'{fname}: {label}')
        results.append({'square': fname, 'label': label, 'score': float(pred)})

    # Save results to CSV
    csv_path = 'square_classification_results.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['square', 'label', 'score'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print('Results saved to square_classification_results.csv')
    return results