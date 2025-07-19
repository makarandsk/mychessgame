import os
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import load_model

# Settings
img_size = (64, 64)
batch_size = 32
val_dir = 'dataset/val'

# Load model
model = load_model('piece_style_classifier.h5')

# Data generator
val_datagen = ImageDataGenerator(rescale=1./255)
val_gen = val_datagen.flow_from_directory(
    val_dir,
    target_size=img_size,
    batch_size=batch_size,
    class_mode='binary',
    shuffle=False
)

# Evaluate
loss, acc = model.evaluate(val_gen, verbose=1)
print(f'Validation Accuracy: {acc:.4f}')

# Optional: Per-class accuracy
labels = val_gen.classes
preds = (model.predict(val_gen) > 0.5).astype(int).flatten()
accepted_idx = np.where(labels == 0)[0]
rejected_idx = np.where(labels == 1)[0]
if len(accepted_idx) > 0:
    acc_accepted = np.mean(preds[accepted_idx] == labels[accepted_idx])
    print(f'Accepted class accuracy: {acc_accepted:.4f}')
if len(rejected_idx) > 0:
    acc_rejected = np.mean(preds[rejected_idx] == labels[rejected_idx])
    print(f'Rejected class accuracy: {acc_rejected:.4f}') 