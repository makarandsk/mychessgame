#!/usr/bin/env python3
"""
Simple verification script for all installed libraries.
"""

print("=== Chess Application Library Verification ===")

# Test each library individually
libraries = [
    ("numpy", "np"),
    ("cv2", "cv2"),
    ("PIL", "PIL"),
    ("matplotlib", "matplotlib"),
    ("chess", "chess"),
    ("pygame", "pygame"),
    ("stockfish", "stockfish"),
    ("tensorflow", "tf"),
    ("keras", "keras"),
    ("sklearn", "sklearn")
]

for lib_name, import_name in libraries:
    try:
        if lib_name == "numpy":
            import numpy as np
            print(f"✅ {lib_name}: {np.__version__}")
        elif lib_name == "cv2":
            import cv2
            print(f"✅ {lib_name}: {cv2.__version__}")
        elif lib_name == "PIL":
            import PIL
            print(f"✅ {lib_name}: {PIL.__version__}")
        elif lib_name == "matplotlib":
            import matplotlib
            print(f"✅ {lib_name}: {matplotlib.__version__}")
        elif lib_name == "chess":
            import chess
            print(f"✅ {lib_name}: {chess.__version__}")
        elif lib_name == "pygame":
            import pygame
            print(f"✅ {lib_name}: {pygame.version.ver}")
        elif lib_name == "stockfish":
            import stockfish
            print(f"✅ {lib_name}: Installed")
        elif lib_name == "tensorflow":
            import tensorflow as tf
            print(f"✅ {lib_name}: {tf.__version__}")
        elif lib_name == "keras":
            import keras
            print(f"✅ {lib_name}: {keras.__version__}")
        elif lib_name == "sklearn":
            import sklearn
            print(f"✅ {lib_name}: {sklearn.__version__}")
    except ImportError as e:
        print(f"❌ {lib_name}: {e}")

print("\n=== Verification Complete ===") 