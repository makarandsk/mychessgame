#!/usr/bin/env python3
"""
Installation script for OCR pipeline dependencies.
"""

import subprocess
import sys
import importlib

def check_package(package_name):
    """Check if a package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Check and install required dependencies."""
    print("OCR Pipeline Dependency Checker")
    print("=" * 40)
    
    # Required packages
    required_packages = [
        ("opencv-python", "cv2"),
        ("tensorflow", "tensorflow"),
        ("numpy", "numpy"),
        ("pillow", "PIL"),
        ("pyperclip", "pyperclip")
    ]
    
    missing_packages = []
    
    print("Checking required packages...")
    for package_name, import_name in required_packages:
        if check_package(import_name):
            print(f"✅ {package_name} - Installed")
        else:
            print(f"❌ {package_name} - Missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        response = input("Would you like to install missing packages? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            print("\nInstalling missing packages...")
            for package in missing_packages:
                print(f"Installing {package}...")
                if install_package(package):
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}")
        else:
            print("Skipping package installation.")
    else:
        print("\n🎉 All required packages are installed!")
    
    print("\n" + "=" * 40)
    print("Next steps:")
    print("1. Run: python test_ocr_pipeline.py")
    print("2. Ensure you have piece_style_classifier.h5 and board.jpg")
    print("3. Test the pipeline with your chessboard images")

if __name__ == "__main__":
    main() 