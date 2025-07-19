import os
from PIL import Image

# Directory containing images to resize
input_dir = os.path.join('dataset', 'New folder')
output_size = (64, 64)

# Supported image extensions
image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']

def resize_images_in_directory(directory, size):
    for filename in os.listdir(directory):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            img_path = os.path.join(directory, filename)
            try:
                with Image.open(img_path) as img:
                    img = img.convert('RGBA') if img.mode in ('RGBA', 'LA') else img.convert('RGB')
                    img_resized = img.resize(size, Image.Resampling.LANCZOS)
                    img_resized.save(img_path)
                    print(f"Resized: {filename}")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    print(f"Resizing images in {input_dir} to {output_size}...")
    resize_images_in_directory(input_dir, output_size)
    print("Done.") 