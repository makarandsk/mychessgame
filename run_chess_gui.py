#!/usr/bin/env python3
"""
Simple script to run the chess GUI.
"""

import sys
import os
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from extract_board_and_squares import detect_board_and_extract_squares
import tkinter as tk
from tkinter import filedialog
import pygame
import threading
from new_classify_squares import classify_all_squares

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the chess GUI
from ui.chess_gui import ChessGUI

if __name__ == "__main__":
    print("Starting Chess GUI...")
    print("Click on pieces to see their information.")
    print("Close the window to exit.")
    
    try:
        chess_gui = ChessGUI()
        chess_gui.run()
    except Exception as e:
        print(f"Error running chess GUI: {e}")
        print("Make sure you're running this with the Python 3.11 virtual environment:")
        print("  venv311\\Scripts\\python.exe run_chess_gui.py") 

def predict_piece(self, img_path):
    img = Image.open(img_path).resize((64, 64))
    img = np.array(img) / 255.0
    img = np.expand_dims(img, axis=0)
    pred = self.piece_model.predict(img)
    idx = np.argmax(pred)
    return self.piece_labels[idx], float(np.max(pred))

def update_board(self):
    board_state = []
    for row in range(8):
        row_state = []
        for col in range(8):
            square_path = f"extracted_squares/square_{row}_{col}.png"
            piece, confidence = self.predict_piece(square_path)
            row_state.append(piece)
        board_state.append(row_state)
    # Now update your ChessLogic or GUI with board_state 

def __init__(self):
    super().__init__()
    self.piece_model = load_model('piece_style_classifier.h5')
    self.piece_labels = [
        'empty', 'white_pawn', 'white_knight', 'white_bishop', 'white_rook', 'white_queen', 'white_king',
        'black_pawn', 'black_knight', 'black_bishop', 'black_rook', 'black_queen', 'black_king'
    ] 
    self._button_rects['capture_image'] = pygame.Rect(200, self.total_height - self.status_bar_height + 60, 160, 40)
    capture_rect = self._button_rects['capture_image']
    self._button_rects['upload_image'] = pygame.Rect(20, 20, 160, 40)

def get_file_path():
    # Hide the main Pygame window before opening the dialog
    pygame.display.iconify()  # Minimize the Pygame window
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Chessboard Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
    )
    root.destroy()
    pygame.display.set_mode((your_width, your_height))  # Restore the Pygame window
    return file_path

def upload_image_dialog(self):
    # Run the file dialog in the main thread
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Chessboard Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
    )
    root.destroy()
    if file_path:
        # Start a background thread for processing
        threading.Thread(target=self.process_uploaded_image, args=(file_path,)).start()

def process_uploaded_image(self, file_path):
    import shutil
    shutil.copy(file_path, 'board.jpg')
    print("Saved uploaded image as board.jpg")
    self.status_message = ""
    try:
        detect_board_and_extract_squares(
            'board.jpg',
            'extracted_squares',
            square_size=64,
            pattern_size=(7, 7),
            crop_percent=0.03
        )
    except Exception as e:
        self.status_message = "Chessboard not found in the image. Please try again."
        print(self.status_message)
        return
    board_state = []
    for row in range(8):
        row_state = []
        for col in range(8):
            square_path = f"extracted_squares/square_{row}_{col}.png"
            piece, confidence = self.predict_piece(square_path)
            row_state.append(piece)
            print(f"Square {row},{col}: {piece} (confidence: {confidence:.2f})")
        board_state.append(row_state)

    self.upload_image_dialog() 

    if 'upload_image' in self._button_rects:
        pygame.draw.rect(self.screen, (255, 0, 0), self._button_rects['upload_image'])  # Red rectangle
        text_surface = self.font.render('Upload Image', True, (255, 255, 255))
        self.screen.blit(text_surface, (self._button_rects['upload_image'].x + 10, self._button_rects['upload_image'].y + 5)) 

    # After extracting squares:
    results = classify_all_squares('extracted_squares', 'piece_style_classifier.h5', (96, 96))
    # You can now use 'results' to update your GUI or board state 