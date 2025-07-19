import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import numpy as np

# Settings
img_size = (96, 96)  # MobileNetV2 default is 96x96 or higher
batch_size = 32
epochs = 40
base_dir = 'dataset'
folders = ['accepted', 'rejected']

# Gather all image paths and labels
data = []
for label, folder in enumerate(folders):
    folder_path = os.path.join(base_dir, folder)
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"{folder}: {len(files)} images")
    print(f"Sample {folder} files: {files[:3]}")
    for fname in files:
        data.append({
            'filename': os.path.join(folder_path, fname),
            'class': folder
        })
df = pd.DataFrame(data)

# Encode labels for stratification
y = df['class'].map({'accepted': 0, 'rejected': 1}).values

# Stratified train/val split
train_df, val_df = train_test_split(df, test_size=0.2, stratify=y, random_state=42)

# Data augmentation
train_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,
    rotation_range=25,
    width_shift_range=0.15,
    height_shift_range=0.15,
    shear_range=0.15,
    zoom_range=0.15,
    horizontal_flip=True,
    brightness_range=[0.6, 1.4],
    fill_mode='nearest'
)
val_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

train_gen = train_datagen.flow_from_dataframe(
    train_df,
    x_col='filename',
    y_col='class',
    target_size=img_size,
    batch_size=batch_size,
    class_mode='binary',
    shuffle=True
)
val_gen = val_datagen.flow_from_dataframe(
    val_df,
    x_col='filename',
    y_col='class',
    target_size=img_size,
    batch_size=batch_size,
    class_mode='binary',
    shuffle=False
)

# Transfer learning model
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(img_size[0], img_size[1], 3))
base_model.trainable = False  # Freeze base model

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Callbacks
early_stop = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)
lr_reduce = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1)

# Train
history = model.fit(
    train_gen,
    epochs=epochs,
    validation_data=val_gen,
    callbacks=[early_stop, lr_reduce],
    verbose=2
)

# Save model
model.save('piece_style_classifier.h5')
print('Model saved as piece_style_classifier.h5')

# Print final accuracy
train_acc = history.history['accuracy'][-1]
val_acc = history.history['val_accuracy'][-1]
print(f'Final Training Accuracy: {train_acc:.4f}')
print(f'Final Validation Accuracy: {val_acc:.4f}')

# Confusion matrix on validation set
val_gen.reset()
y_true = val_df['class'].map({'accepted': 0, 'rejected': 1}).values
y_pred = model.predict(val_gen, verbose=0)
y_pred_bin = (y_pred > 0.5).astype(int).flatten()
print("\nValidation Confusion Matrix:")
print(confusion_matrix(y_true, y_pred_bin))
print("\nClassification Report:")
print(classification_report(y_true, y_pred_bin, target_names=folders)) 