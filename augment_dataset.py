import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img, array_to_img
import numpy as np

# Settings
folders = [('accepted', 'dataset/accepted'), ('rejected', 'dataset/rejected')]
size = (64, 64)
num_augmented = 5  # Number of augmented images per original

# Augmentation configuration
aug = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    brightness_range=[0.7, 1.3],
    fill_mode='nearest'
)

def augment_folder(folder):
    images = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for img_name in images:
        img_path = os.path.join(folder, img_name)
        img = load_img(img_path, target_size=size)
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)
        # Generate augmented images
        prefix = os.path.splitext(img_name)[0]
        i = 0
        for batch in aug.flow(x, batch_size=1):
            aug_img = array_to_img(batch[0], scale=True)
            aug_img.save(os.path.join(folder, f"{prefix}_aug{i+1}.png"))
            i += 1
            if i >= num_augmented:
                break

if __name__ == "__main__":
    for label, folder in folders:
        print(f"Augmenting images in {folder}...")
        augment_folder(folder)
    print("Data augmentation complete.")
