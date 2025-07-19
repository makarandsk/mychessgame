#!/usr/bin/env python3
"""
Manual correction UI for chess board state.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Callable
import cv2
from PIL import Image, ImageTk
import os

class ManualCorrectionUI:
    """Simple manual correction UI for chess board state."""
    
    def __init__(self, board_img_path: str, classification_results: List[Dict[str, Any]], 
                 initial_fen: str, on_save: Optional[Callable[[str], None]] = None):
        self.board_img_path = board_img_path
        self.classification_results = classification_results
        self.initial_fen = initial_fen
        self.on_save = on_save
        self.corrected_fen = initial_fen
        
        # Create board state from classification results
        self.board_state = self._create_board_state()
        
        # Create UI
        self.root = tk.Tk()
        self.root.title("Manual Correction - Chess Board State")
        self.root.geometry("800x600")
        
        self._create_widgets()
        self._load_board_image()
        
    def _create_board_state(self) -> List[List[str]]:
        """Create board state from classification results."""
        board_state = [['' for _ in range(8)] for _ in range(8)]
        
        for result in self.classification_results:
            fname = result['square']
            if fname.startswith('square_') and '.png' in fname:
                parts = fname.replace('.png', '').split('_')
                if len(parts) == 3:
                    row = int(parts[1])
                    col = int(parts[2])
                    
                    if 0 <= row < 8 and 0 <= col < 8:
                        if result['label'] == 'accepted':
                            board_state[row][col] = 'P'  # Placeholder for any piece
                        else:
                            board_state[row][col] = ''
        
        return board_state
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Manual Correction - Chess Board State", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Board image frame
        img_frame = ttk.LabelFrame(main_frame, text="Board Image", padding="5")
        img_frame.grid(row=1, column=0, rowspan=2, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.img_label = ttk.Label(img_frame, text="Loading image...")
        self.img_label.grid(row=0, column=0)
        
        # Board state frame
        board_frame = ttk.LabelFrame(main_frame, text="Board State", padding="5")
        board_frame.grid(row=1, column=1, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create 8x8 grid of buttons for board state
        self.board_buttons = []
        for row in range(8):
            button_row = []
            for col in range(8):
                btn = tk.Button(board_frame, text="", width=3, height=2,
                              command=lambda r=row, c=col: self._toggle_square(r, c))
                btn.grid(row=row, column=col, padx=1, pady=1)
                button_row.append(btn)
            self.board_buttons.append(button_row)
        
        # FEN display frame
        fen_frame = ttk.LabelFrame(main_frame, text="FEN String", padding="5")
        fen_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.fen_text = tk.Text(fen_frame, height=4, width=50, wrap=tk.WORD)
        self.fen_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        fen_scrollbar = ttk.Scrollbar(fen_frame, orient=tk.VERTICAL, command=self.fen_text.yview)
        fen_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.fen_text.configure(yscrollcommand=fen_scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=1, columnspan=2, pady=(10, 0))
        
        # Piece selection buttons
        piece_frame = ttk.LabelFrame(buttons_frame, text="Piece Selection", padding="5")
        piece_frame.grid(row=0, column=0, padx=(0, 10))
        
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k', '']
        piece_labels = ['♙', '♘', '♗', '♖', '♕', '♔', '♟', '♞', '♝', '♜', '♛', '♚', '·']
        
        self.selected_piece = tk.StringVar(value='P')
        
        for i, (piece, label) in enumerate(zip(pieces, piece_labels)):
            btn = ttk.Radiobutton(piece_frame, text=label, variable=self.selected_piece, 
                                value=piece, command=self._update_selection)
            btn.grid(row=i//6, column=i%6, padx=2, pady=1)
        
        # Action buttons
        action_frame = ttk.Frame(buttons_frame)
        action_frame.grid(row=0, column=1, padx=(10, 0))
        
        ttk.Button(action_frame, text="Update FEN", command=self._update_fen).grid(row=0, column=0, padx=2)
        ttk.Button(action_frame, text="Save", command=self._save).grid(row=0, column=1, padx=2)
        ttk.Button(action_frame, text="Cancel", command=self._cancel).grid(row=0, column=2, padx=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Initialize board display
        self._update_board_display()
        self._update_fen()
    
    def _load_board_image(self):
        """Load and display the board image."""
        try:
            if os.path.exists(self.board_img_path):
                # Load image with PIL
                img = Image.open(self.board_img_path)
                # Resize to reasonable size
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                self.img_label.configure(image=photo, text="")
                self.img_label.image = photo  # Keep a reference
            else:
                self.img_label.configure(text="Image not found")
        except Exception as e:
            self.img_label.configure(text=f"Error loading image: {e}")
    
    def _update_board_display(self):
        """Update the board display with current state."""
        for row in range(8):
            for col in range(8):
                piece = self.board_state[row][col]
                btn = self.board_buttons[row][col]
                
                if piece == '':
                    btn.configure(text="·", bg="white")
                elif piece == 'P':
                    btn.configure(text="♙", bg="lightblue")
                elif piece == 'N':
                    btn.configure(text="♘", bg="lightblue")
                elif piece == 'B':
                    btn.configure(text="♗", bg="lightblue")
                elif piece == 'R':
                    btn.configure(text="♖", bg="lightblue")
                elif piece == 'Q':
                    btn.configure(text="♕", bg="lightblue")
                elif piece == 'K':
                    btn.configure(text="♔", bg="lightblue")
                elif piece == 'p':
                    btn.configure(text="♟", bg="lightcoral")
                elif piece == 'n':
                    btn.configure(text="♞", bg="lightcoral")
                elif piece == 'b':
                    btn.configure(text="♝", bg="lightcoral")
                elif piece == 'r':
                    btn.configure(text="♜", bg="lightcoral")
                elif piece == 'q':
                    btn.configure(text="♛", bg="lightcoral")
                elif piece == 'k':
                    btn.configure(text="♚", bg="lightcoral")
    
    def _toggle_square(self, row: int, col: int):
        """Toggle a square with the selected piece."""
        selected = self.selected_piece.get()
        self.board_state[row][col] = selected
        self._update_board_display()
        self._update_fen()
    
    def _update_selection(self):
        """Update piece selection."""
        # This is handled by the radio buttons
        pass
    
    def _update_fen(self):
        """Update FEN string from current board state."""
        fen = self._board_state_to_fen()
        self.corrected_fen = fen
        
        # Update text widget
        self.fen_text.delete(1.0, tk.END)
        self.fen_text.insert(1.0, fen)
    
    def _board_state_to_fen(self) -> str:
        """Convert board state to FEN string."""
        fen_parts = []
        board_str = ""
        
        for row in range(8):
            empty_count = 0
            for col in range(8):
                if self.board_state[row][col] == '':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        board_str += str(empty_count)
                        empty_count = 0
                    board_str += self.board_state[row][col]
            
            if empty_count > 0:
                board_str += str(empty_count)
            
            if row < 7:
                board_str += "/"
        
        fen_parts.append(board_str)
        fen_parts.extend(['w', 'KQkq', '-', '0', '1'])
        
        return " ".join(fen_parts)
    
    def _save(self):
        """Save the corrected FEN."""
        if self.on_save:
            self.on_save(self.corrected_fen)
        
        messagebox.showinfo("Success", f"FEN saved:\n{self.corrected_fen}")
        self.root.destroy()
    
    def _cancel(self):
        """Cancel and close the window."""
        self.root.destroy()
    
    def run(self) -> str:
        """Run the UI and return the corrected FEN."""
        self.root.mainloop()
        return self.corrected_fen


def show_manual_correction_ui(board_img_path: str, classification_results: List[Dict[str, Any]], 
                            initial_fen: str) -> str:
    """
    Show manual correction UI and return corrected FEN.
    
    Args:
        board_img_path: Path to the board image
        classification_results: Results from square classification
        initial_fen: Initial FEN string
    
    Returns:
        Corrected FEN string
    """
    ui = ManualCorrectionUI(board_img_path, classification_results, initial_fen)
    return ui.run()


if __name__ == "__main__":
    # Test the UI
    test_results = [
        {'square': 'square_0_0.png', 'label': 'accepted', 'confidence': 0.8},
        {'square': 'square_0_1.png', 'label': 'rejected', 'confidence': 0.2},
        # ... more results
    ]
    
    fen = show_manual_correction_ui('board.jpg', test_results, 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    print(f"Corrected FEN: {fen}") 