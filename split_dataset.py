import os
import shutil
import random

# Settings
base_dir = 'dataset'
folders = ['accepted', 'rejected']
train_ratio = 0.9
val_ratio = 0.05  # 5% validation, 5% test

# Output directories
train_dir = os.path.join(base_dir, 'train')
val_dir = os.path.join(base_dir, 'val')
test_dir = os.path.join(base_dir, 'test')

for split_dir in [train_dir, val_dir, test_dir]:
    for folder in folders:
        os.makedirs(os.path.join(split_dir, folder), exist_ok=True)

for folder in folders:
    src_folder = os.path.join(base_dir, folder)
    images = [f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))]
    random.shuffle(images)
    n = len(images)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val
    train_imgs = images[:n_train]
    val_imgs = images[n_train:n_train+n_val]
    test_imgs = images[n_train+n_val:]
    # Move images
    for img in train_imgs:
        src = os.path.join(src_folder, img)
        dst = os.path.join(train_dir, folder, img)
        shutil.copy2(src, dst)
    for img in val_imgs:
        src = os.path.join(src_folder, img)
        dst = os.path.join(val_dir, folder, img)
        shutil.copy2(src, dst)
    for img in test_imgs:
        src = os.path.join(src_folder, img)
        dst = os.path.join(test_dir, folder, img)
        shutil.copy2(src, dst)

print("Dataset split into train/val/test sets.") 