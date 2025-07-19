#!/usr/bin/env python3
"""
Integration module for OCR pipeline with chess GUI.
This shows how to update the capture_image function to use the new OCR pipeline.
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import messagebox

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.ocr_pipeline import run_ocr_pipeline
from utils.fen_utils import copy_fen_to_clipboard, save_fen_to_file

def process_image_with_ocr(image_path: str, status_callback=None) -> str:
    """
    Process an image with the OCR pipeline.
    
    Args:
        image_path: Path to the input image
        status_callback: Optional callback function to update status
    
    Returns:
        FEN string of the detected position
    """
    try:
        if status_callback:
            status_callback("Running OCR pipeline...")
        
        # Run the complete OCR pipeline
        fen = run_ocr_pipeline(image_path, 'piece_style_classifier.h5', (96, 96))
        
        if fen.startswith("Error:"):
            if status_callback:
                status_callback(f"OCR Error: {fen}")
            return fen
        
        # Save FEN to file
        save_fen_to_file(fen, 'board_fen.txt')
        
        # Copy to clipboard
        copy_fen_to_clipboard(fen)
        
        if status_callback:
            status_callback(f"FEN generated: {fen[:50]}...")
        
        return fen
        
    except Exception as e:
        error_msg = f"OCR processing error: {e}"
        if status_callback:
            status_callback(error_msg)
        return f"Error: {error_msg}"

def show_fen_result_dialog(fen: str):
    """Show a dialog with the generated FEN."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create a custom dialog
    dialog = tk.Toplevel(root)
    dialog.title("OCR Result - FEN Generated")
    dialog.geometry("600x400")
    dialog.resizable(True, True)
    
    # Center the dialog
    dialog.transient(root)
    dialog.grab_set()
    
    # Main frame
    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = tk.Label(main_frame, text="Chess Board OCR Result", 
                          font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # FEN display
    fen_label = tk.Label(main_frame, text="Generated FEN:", font=("Arial", 12, "bold"))
    fen_label.pack(anchor=tk.W, pady=(0, 5))
    
    fen_text = tk.Text(main_frame, height=3, width=70, wrap=tk.WORD, font=("Courier", 10))
    fen_text.pack(fill=tk.X, pady=(0, 20))
    fen_text.insert(tk.END, fen)
    fen_text.config(state=tk.DISABLED)
    
    # Info text
    info_text = tk.Text(main_frame, height=8, width=70, wrap=tk.WORD, font=("Arial", 10))
    info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    info_content = """The FEN string has been:
• Generated from the captured chessboard image
• Saved to 'board_fen.txt'
• Copied to your clipboard

You can now:
• Paste the FEN into chess analysis software
• Use it to set up a position in your chess GUI
• Share it with other chess players

The FEN format represents:
• Board position (piece placement)
• Active player (w/b)
• Castling rights (KQkq)
• En passant target (-)
• Halfmove clock (0)
• Fullmove number (1)"""
    
    info_text.insert(tk.END, info_content)
    info_text.config(state=tk.DISABLED)
    
    # Buttons
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(20, 0))
    
    def copy_again():
        copy_fen_to_clipboard(fen)
        messagebox.showinfo("Copied", "FEN copied to clipboard again!")
    
    def open_file():
        try:
            os.startfile('board_fen.txt')  # Windows
        except:
            try:
                os.system('open board_fen.txt')  # macOS
            except:
                os.system('xdg-open board_fen.txt')  # Linux
    
    tk.Button(button_frame, text="Copy FEN Again", command=copy_again).pack(side=tk.LEFT, padx=(0, 10))
    tk.Button(button_frame, text="Open FEN File", command=open_file).pack(side=tk.LEFT, padx=(0, 10))
    tk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
    
    # Center dialog on screen
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Wait for dialog to close
    dialog.wait_window()
    root.destroy()

def update_capture_image_function():
    """
    This function shows how to update the capture_image function in chess_gui.py.
    
    Replace the existing capture_image function with this updated version.
    """
    
    def capture_image_updated(self):
        """Updated capture_image function with OCR pipeline integration."""
        cap = cv2.VideoCapture(1)  # Try 1, 2, etc. until you get DroidCam
        if not cap.isOpened():
            print("Cannot open camera")
            return
        captured = False
        img_path = None

        btn_w, btn_h = 120, 40
        btn_gap = 20
        clicked = {'pos': None}

        def is_in_rect(mx, my, x, y, w, h):
            return x <= mx <= x + w and y <= my <= y + h

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                clicked['pos'] = (x, y)

        cv2.namedWindow('Capture Chessboard', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Capture Chessboard', mouse_callback)
        
        try:
            cv2.setWindowProperty('Capture Chessboard', cv2.WND_PROP_MOUSE_CURSOR, 0)
        except Exception:
            pass

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            display_frame = frame.copy()
            h, w = display_frame.shape[:2]
            btn_y = h - btn_h - 20
            click_btn_x = w // 2 - btn_w - btn_gap // 2
            retake_btn_x = w // 2 + btn_gap // 2
            cont_btn_x = w // 2 - btn_w // 2

            # Draw 'Click' button if not captured
            if not captured:
                cv2.rectangle(display_frame, (click_btn_x, btn_y), (click_btn_x + btn_w, btn_y + btn_h), (70, 130, 180), -1)
                cv2.putText(display_frame, 'Click', (click_btn_x + 25, btn_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Draw 'Retake' and 'Continue' buttons if captured
            if captured:
                cv2.rectangle(display_frame, (retake_btn_x, btn_y), (retake_btn_x + btn_w, btn_y + btn_h), (34, 139, 34), -1)
                cv2.putText(display_frame, 'Retake', (retake_btn_x + 10, btn_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.rectangle(display_frame, (cont_btn_x, btn_y - btn_h - btn_gap), (cont_btn_x + btn_w, btn_y - btn_gap), (255, 165, 0), -1)
                cv2.putText(display_frame, 'Continue', (cont_btn_x + 5, btn_y - btn_h - btn_gap + 28), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.imshow('Capture Chessboard', display_frame)
            key = cv2.waitKey(1)

            # Check if window was closed by user (X button)
            try:
                window_visible = cv2.getWindowProperty('Capture Chessboard', cv2.WND_PROP_VISIBLE)
                if window_visible < 1:
                    print("Camera window closed by user")
                    break
            except:
                break

            # Handle mouse clicks
            if clicked['pos']:
                mx, my = clicked['pos']
                if not captured and is_in_rect(mx, my, click_btn_x, btn_y, btn_w, btn_h):
                    img_path = 'captured_chessboard.png'
                    cv2.imwrite(img_path, frame)
                    print(f"Image captured: {img_path}")
                    captured = True
                elif captured and is_in_rect(mx, my, retake_btn_x, btn_y, btn_w, btn_h):
                    captured = False
                elif captured and is_in_rect(mx, my, cont_btn_x, btn_y - btn_h - btn_gap, btn_w, btn_h):
                    print(f"Image accepted: {img_path}")
                    # Rename the accepted image to 'board.jpg'
                    shutil.copy(img_path, 'board.jpg')
                    print("Saved accepted image as board.jpg")

                    # NEW: Run OCR pipeline
                    def run_ocr_thread():
                        try:
                            # Update status
                            self.status_message = "Running OCR pipeline..."
                            
                            # Process with OCR
                            fen = process_image_with_ocr('board.jpg', 
                                                       lambda msg: setattr(self, 'status_message', msg))
                            
                            if not fen.startswith("Error:"):
                                # Show result dialog
                                show_fen_result_dialog(fen)
                                self.status_message = f"OCR completed! FEN: {fen[:30]}..."
                            else:
                                self.status_message = fen
                                
                        except Exception as e:
                            self.status_message = f"OCR error: {e}"
                            print(f"OCR error: {e}")
                    
                    # Run OCR in background thread
                    threading.Thread(target=run_ocr_thread).start()
                    break
                clicked['pos'] = None

            if key == 27:  # ESC
                print("Camera capture cancelled by ESC key")
                break

        # Proper cleanup
        cap.release()
        cv2.destroyAllWindows()
        # Force destroy any remaining windows
        for i in range(10):
            cv2.waitKey(1)

    return capture_image_updated

def update_upload_image_function():
    """
    This function shows how to update the upload image processing in chess_gui.py.
    """
    
    def process_uploaded_image_updated(self, file_path):
        """Updated upload image processing with OCR pipeline integration."""
        shutil.copy(file_path, 'board.jpg')
        print("Saved uploaded image as board.jpg")
        self.status_message = ""
        
        def run_ocr_thread():
            try:
                # Update status
                self.status_message = "Running OCR pipeline..."
                
                # Process with OCR
                fen = process_image_with_ocr('board.jpg', 
                                           lambda msg: setattr(self, 'status_message', msg))
                
                if not fen.startswith("Error:"):
                    # Show result dialog
                    show_fen_result_dialog(fen)
                    self.status_message = f"OCR completed! FEN: {fen[:30]}..."
                else:
                    self.status_message = fen
                    
            except Exception as e:
                self.status_message = f"OCR error: {e}"
                print(f"OCR error: {e}")
        
        # Run OCR in background thread
        threading.Thread(target=run_ocr_thread).start()

    return process_uploaded_image_updated

# Example usage
if __name__ == "__main__":
    # Test the OCR pipeline
    print("Testing OCR pipeline...")
    fen = process_image_with_ocr('board.jpg')
    print(f"Generated FEN: {fen}")
    
    if not fen.startswith("Error:"):
        show_fen_result_dialog(fen) 