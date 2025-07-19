#!/usr/bin/env python3
"""
Chessify-like OCR Pipeline
Handles board detection, square extraction, piece classification, and FEN generation.
"""

import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import shutil
from typing import List, Tuple, Optional, Dict, Any
import json

class ChessOCR:
    """Main OCR class for chessboard detection and piece classification."""
    
    def __init__(self, model_path: str = 'piece_style_classifier.h5', img_size: Tuple[int, int] = (96, 96)):
        self.model_path = model_path
        self.img_size = img_size
        self.model = None
        self.last_classification_results = []
        self.load_model()
        
    def load_model(self):
        """Load the piece classification model."""
        try:
            self.model = load_model(self.model_path)
            print(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def detect_board_and_extract_squares(self, image_path: str, output_dir: str = 'extracted_squares', 
                                       square_size: int = 96, pattern_size: Tuple[int, int] = (7, 7), 
                                       crop_percent: float = 0.03) -> Tuple[Optional[np.ndarray], List[str]]:
        """
        Detect chessboard in image and extract individual squares.
        
        Returns:
            Tuple of (board_image, list_of_square_paths)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not read image: {image_path}")
            return None, []
        
        orig = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Try OpenCV chessboard corner detection first
        found, corners = cv2.findChessboardCorners(gray, pattern_size)
        debug_img = orig.copy()
        board_pts = None
        
        if found:
            print("Chessboard corners found using OpenCV method.")
            cv2.drawChessboardCorners(debug_img, pattern_size, corners, found)
            cv2.imwrite('chessboard_corners.png', debug_img)
            corners = corners.reshape(-1, 2)
            tl = corners[0]
            tr = corners[pattern_size[0]-1]
            br = corners[-1]
            bl = corners[-pattern_size[0]]
            board_pts = np.array([tl, tr, br, bl], dtype="float32")
        else:
            print("OpenCV corners not found, falling back to contour-based detection...")
            board_pts = self._detect_board_contour(image)
        
        if board_pts is None:
            print("Chessboard not found!")
            print("Trying manual board selection...")
            board_pts = self._manual_board_selection(image)
            
            if board_pts is None:
                print("Manual selection also failed. Please check your image.")
                return None, []
        
        # Perspective transform and processing
        warped = self._four_point_transform(orig, board_pts)
        board_size = min(warped.shape[:2])
        warped = cv2.resize(warped, (board_size, board_size))
        
        # Upscale for better quality
        target_board_size = 1024
        warped = cv2.resize(warped, (target_board_size, target_board_size), interpolation=cv2.INTER_LANCZOS4)
        
        # Enhance image
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        warped = cv2.filter2D(warped, -1, kernel)
        warped = self._crop_border(warped, percent=crop_percent)
        
        # Save debug images
        cv2.imwrite('warped_board_cropped.png', warped)
        
        # Extract squares
        square_paths = self._extract_squares(warped, output_dir, square_size)
        
        return warped, square_paths
    
    def _detect_board_contour(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect board using multiple detection methods."""
        h, w = image.shape[:2]
        min_area = (h * w) * 0.05  # Reduced minimum area requirement
        
        # Method 1: Try multiple color ranges for different board types
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Try different color ranges
        color_ranges = [
            # Brown wooden boards
            (np.array([10, 50, 50]), np.array([30, 255, 255])),
            # Dark brown boards
            (np.array([0, 50, 50]), np.array([20, 255, 255])),
            # Light brown boards
            (np.array([15, 30, 100]), np.array([35, 255, 255])),
            # Gray/black boards
            (np.array([0, 0, 50]), np.array([180, 255, 150])),
        ]
        
        for i, (lower, upper) in enumerate(color_ranges):
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
            
            cv2.imwrite(f'color_mask_{i}.png', mask)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            board_contour = self._find_best_contour(contours, image, min_area)
            if board_contour is not None:
                debug_board = image.copy()
                cv2.drawContours(debug_board, [board_contour], -1, (0,255,0), 3)
                cv2.imwrite(f'detected_board_contour_{i}.png', debug_board)
                return board_contour.reshape(4, 2)
        
        # Method 2: Try edge-based detection
        print("Color-based detection failed, trying edge-based detection...")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours in edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        board_contour = self._find_best_contour(contours, image, min_area)
        
        if board_contour is not None:
            debug_board = image.copy()
            cv2.drawContours(debug_board, [board_contour], -1, (0,255,0), 3)
            cv2.imwrite('detected_board_contour_edges.png', debug_board)
            return board_contour.reshape(4, 2)
        
        # Method 3: Try adaptive thresholding
        print("Edge-based detection failed, trying adaptive thresholding...")
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        board_contour = self._find_best_contour(contours, image, min_area)
        
        if board_contour is not None:
            debug_board = image.copy()
            cv2.drawContours(debug_board, [board_contour], -1, (0,255,0), 3)
            cv2.imwrite('detected_board_contour_adaptive.png', debug_board)
            return board_contour.reshape(4, 2)
        
        # Method 4: Fallback to largest rectangular contour
        print("All detection methods failed, using fallback...")
        all_contours = []
        for i, (lower, upper) in enumerate(color_ranges):
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            all_contours.extend(contours)
        
        if all_contours:
            # Find the largest contour that's roughly square
            largest_contour = max(all_contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area > min_area:
                # Approximate to get a rectangle
                peri = cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
                
                if len(approx) >= 4:
                    # Get the bounding rectangle
                    x, y, w, h = cv2.boundingRect(approx)
                    board_contour = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]], dtype=np.float32)
                    
                    debug_board = image.copy()
                    cv2.drawContours(debug_board, [board_contour.astype(np.int32)], -1, (0,255,0), 3)
                    cv2.imwrite('detected_board_contour_fallback.png', debug_board)
                    return board_contour
        
        return None
    
    def _find_best_contour(self, contours: list, image: np.ndarray, min_area: float) -> Optional[np.ndarray]:
        """Find the best rectangular contour that could be a chessboard."""
        h, w = image.shape[:2]
        best_contour = None
        best_score = 0
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            if len(approx) == 4:
                # Check if it's roughly square
                x, y, w_rect, h_rect = cv2.boundingRect(approx)
                aspect_ratio = float(w_rect) / h_rect
                
                # More lenient aspect ratio check
                if 0.7 < aspect_ratio < 1.3:
                    # Score based on area and squareness
                    squareness = 1.0 - abs(1.0 - aspect_ratio)
                    score = area * squareness
                    
                    if score > best_score:
                        best_score = score
                        best_contour = approx
        
        return best_contour
    
    def _manual_board_selection(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Manual board selection using mouse clicks."""
        try:
            points = []
            clicked = {'count': 0}
            
            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN and clicked['count'] < 4:
                    points.append([x, y])
                    clicked['count'] += 1
                    # Draw point
                    cv2.circle(display_img, (x, y), 5, (0, 255, 0), -1)
                    cv2.imshow('Manual Board Selection', display_img)
                    print(f"Point {clicked['count']}: ({x}, {y})")
            
            display_img = image.copy()
            cv2.namedWindow('Manual Board Selection', cv2.WINDOW_NORMAL)
            cv2.setMouseCallback('Manual Board Selection', mouse_callback)
            
            print("Click 4 corners of the chessboard (clockwise from top-left)")
            print("Press 'r' to reset, 'q' to quit")
            
            while clicked['count'] < 4:
                cv2.imshow('Manual Board Selection', display_img)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('r'):
                    points.clear()
                    clicked['count'] = 0
                    display_img = image.copy()
                elif key == ord('q'):
                    cv2.destroyAllWindows()
                    return None
            
            cv2.destroyAllWindows()
            
            if len(points) == 4:
                # Order points: top-left, top-right, bottom-right, bottom-left
                points = np.array(points, dtype=np.float32)
                return points
            
            return None
            
        except Exception as e:
            print(f"Manual selection error: {e}")
            return None
    
    def _four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Apply perspective transform to get a top-down view."""
        rect = pts.astype("float32")
        
        # Get the width and height of the new image
        (tl, tr, br, bl) = rect
        
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def _crop_border(self, image: np.ndarray, percent: float = 0.03) -> np.ndarray:
        """Crop border from the image."""
        h, w = image.shape[:2]
        crop_h = int(h * percent)
        crop_w = int(w * percent)
        return image[crop_h:h-crop_h, crop_w:w-crop_w]
    
    def _extract_squares(self, board_image: np.ndarray, output_dir: str, square_size: int) -> List[str]:
        """Extract 64 squares from the board image."""
        step = board_image.shape[0] // 8
        h, w = board_image.shape[:2]
        square_paths = []
        
        for row in range(8):
            for col in range(8):
                y1 = row * step
                y2 = (row + 1) * step if row < 7 else h
                x1 = col * step
                x2 = (col + 1) * step if col < 7 else w
                
                square = board_image[y1:y2, x1:x2]
                if square.size == 0:
                    print(f"Warning: Empty square at {row},{col}, skipping.")
                    continue
                
                square = cv2.resize(square, (square_size, square_size))
                fname = f"square_{row}_{col}.png"
                filepath = os.path.join(output_dir, fname)
                cv2.imwrite(filepath, square)
                square_paths.append(filepath)
        
        print(f"Extracted {len(square_paths)} squares to {output_dir}")
        return square_paths
    
    def classify_all_squares(self, squares_dir: str = 'extracted_squares') -> List[Dict[str, Any]]:
        """Classify all squares using the loaded model."""
        if self.model is None:
            print("Model not loaded, cannot classify squares")
            return []
        
        results = []
        square_files = sorted([f for f in os.listdir(squares_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))])
        
        for fname in square_files:
            img_path = os.path.join(squares_dir, fname)
            try:
                img = load_img(img_path, target_size=self.img_size)
                x = img_to_array(img)
                x = np.expand_dims(x, axis=0)
                x = preprocess_input(x)
                pred = self.model.predict(x, verbose=0)[0][0]
                label = 'accepted' if pred < 0.5 else 'rejected'
                confidence = float(pred)
                
                results.append({
                    'square': fname,
                    'label': label,
                    'confidence': confidence,
                    'path': img_path
                })
                print(f'{fname}: {label} (confidence: {confidence:.3f})')
                
            except Exception as e:
                print(f"Error classifying {fname}: {e}")
                results.append({
                    'square': fname,
                    'label': 'error',
                    'confidence': 0.0,
                    'path': img_path
                })
        
        return results
    
    def generate_fen_string(self, classification_results: List[Dict[str, Any]]) -> str:
        """Generate FEN string from classification results."""
        # Create 8x8 board state
        board_state = [['' for _ in range(8)] for _ in range(8)]
        
        for result in classification_results:
            # Parse filename to get row and col
            fname = result['square']
            if fname.startswith('square_') and '.png' in fname:
                parts = fname.replace('.png', '').split('_')
                if len(parts) == 3:
                    row = int(parts[1])
                    col = int(parts[2])
                    
                    if 0 <= row < 8 and 0 <= col < 8:
                        if result['label'] == 'accepted':
                            # For now, use 'P' for any piece (you can enhance this)
                            board_state[row][col] = 'P'
                        else:
                            board_state[row][col] = ''  # Empty square
        
        # Convert board state to FEN
        fen_parts = []
        board_str = ""
        
        for row in range(8):
            empty_count = 0
            for col in range(8):
                if board_state[row][col] == '':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        board_str += str(empty_count)
                        empty_count = 0
                    board_str += board_state[row][col]
            
            if empty_count > 0:
                board_str += str(empty_count)
            
            if row < 7:
                board_str += "/"
        
        fen_parts.append(board_str)
        
        # Add default FEN parts
        fen_parts.extend(['w', 'KQkq', '-', '0', '1'])
        
        return " ".join(fen_parts)
    
    def manual_correction_ui(self, board_img: np.ndarray, board_state: List[List[str]], 
                           fen: str) -> str:
        """Simple manual correction UI using tkinter."""
        try:
            from src.ui.manual_correction_ui import show_manual_correction_ui
            # Save board image temporarily for UI
            temp_img_path = 'temp_board_for_ui.png'
            cv2.imwrite(temp_img_path, board_img)
            
            # Show manual correction UI
            corrected_fen = show_manual_correction_ui(temp_img_path, self.last_classification_results, fen)
            
            # Clean up temp file
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
            return corrected_fen
        except Exception as e:
            print(f"Error in manual correction UI: {e}")
            return fen
    
    def run_ocr_pipeline(self, image_path: str, output_dir: str = 'extracted_squares') -> str:
        """
        Run the complete OCR pipeline.
        
        Returns:
            FEN string of the detected position
        """
        print("Starting OCR pipeline...")
        
        # Step 1: Detect and extract squares
        print("Step 1: Detecting board and extracting squares...")
        board_img, square_paths = self.detect_board_and_extract_squares(image_path, output_dir)
        
        if board_img is None:
            return "Error: Could not detect chessboard"
        
        # Step 2: Classify squares
        print("Step 2: Classifying squares...")
        classification_results = self.classify_all_squares(output_dir)
        self.last_classification_results = classification_results
        
        if not classification_results:
            return "Error: No squares could be classified"
        
        # Step 3: Generate FEN
        print("Step 3: Generating FEN...")
        fen = self.generate_fen_string(classification_results)
        
        # Step 4: Manual correction (placeholder)
        print("Step 4: Manual correction (placeholder)...")
        board_state = [['' for _ in range(8)] for _ in range(8)]  # Placeholder
        fen = self.manual_correction_ui(board_img, board_state, fen)
        
        # Step 5: Output results
        print(f"Final FEN: {fen}")
        
        # Save results
        self._save_results(classification_results, fen, output_dir)
        
        return fen
    
    def _save_results(self, classification_results: List[Dict[str, Any]], fen: str, output_dir: str):
        """Save classification results and FEN to files."""
        # Save classification results
        results_file = os.path.join(output_dir, 'classification_results.json')
        with open(results_file, 'w') as f:
            json.dump(classification_results, f, indent=2)
        
        # Save FEN
        fen_file = os.path.join(output_dir, 'board_fen.txt')
        with open(fen_file, 'w') as f:
            f.write(fen)
        
        print(f"Results saved to {results_file}")
        print(f"FEN saved to {fen_file}")


def run_ocr_pipeline(image_path: str, model_path: str = 'piece_style_classifier.h5', 
                    img_size: Tuple[int, int] = (96, 96)) -> str:
    """
    Convenience function to run the complete OCR pipeline.
    
    Args:
        image_path: Path to the input image
        model_path: Path to the classification model
        img_size: Input size for the model
    
    Returns:
        FEN string of the detected position
    """
    ocr = ChessOCR(model_path, img_size)
    return ocr.run_ocr_pipeline(image_path)


if __name__ == "__main__":
    # Test the pipeline
    fen = run_ocr_pipeline('board.jpg')
    print(f"Generated FEN: {fen}") 