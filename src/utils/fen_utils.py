#!/usr/bin/env python3
"""
FEN utilities for chess position handling.
"""

from typing import List, Dict, Any, Optional
import json

# Try to import pyperclip, but make it optional
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("Warning: pyperclip not available. Clipboard functionality will be disabled.")
    print("Install with: pip install pyperclip")

def copy_fen_to_clipboard(fen: str) -> bool:
    """Copy FEN string to clipboard."""
    if not PYPERCLIP_AVAILABLE:
        print("Clipboard functionality not available. Install pyperclip: pip install pyperclip")
        print(f"FEN (not copied): {fen}")
        return False
    
    try:
        pyperclip.copy(fen)
        print(f"FEN copied to clipboard: {fen}")
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def save_fen_to_file(fen: str, filename: str = 'board_fen.txt') -> bool:
    """Save FEN string to a file."""
    try:
        with open(filename, 'w') as f:
            f.write(fen)
        print(f"FEN saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving FEN to file: {e}")
        return False

def load_fen_from_file(filename: str = 'board_fen.txt') -> Optional[str]:
    """Load FEN string from a file."""
    try:
        with open(filename, 'r') as f:
            fen = f.read().strip()
        return fen
    except Exception as e:
        print(f"Error loading FEN from file: {e}")
        return None

def validate_fen(fen: str) -> bool:
    """Basic FEN validation."""
    try:
        parts = fen.split()
        if len(parts) < 1:
            return False
        
        # Check board part
        board_part = parts[0]
        rows = board_part.split('/')
        if len(rows) != 8:
            return False
        
        for row in rows:
            square_count = 0
            for char in row:
                if char.isdigit():
                    square_count += int(char)
                elif char.lower() in 'pnbrqk':
                    square_count += 1
                else:
                    return False
            if square_count != 8:
                return False
        
        return True
    except Exception:
        return False

def classification_to_board_state(classification_results: List[Dict[str, Any]]) -> List[List[str]]:
    """Convert classification results to 8x8 board state."""
    board_state = [['' for _ in range(8)] for _ in range(8)]
    
    for result in classification_results:
        fname = result['square']
        if fname.startswith('square_') and '.png' in fname:
            parts = fname.replace('.png', '').split('_')
            if len(parts) == 3:
                row = int(parts[1])
                col = int(parts[2])
                
                if 0 <= row < 8 and 0 <= col < 8:
                    if result['label'] == 'accepted':
                        # For now, use 'P' for any piece
                        # You can enhance this to detect specific piece types
                        board_state[row][col] = 'P'
                    else:
                        board_state[row][col] = ''  # Empty square
    
    return board_state

def board_state_to_fen(board_state: List[List[str]], 
                      active_color: str = 'w',
                      castling: str = 'KQkq',
                      en_passant: str = '-',
                      halfmove_clock: str = '0',
                      fullmove_number: str = '1') -> str:
    """Convert board state to FEN string."""
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
    fen_parts.extend([active_color, castling, en_passant, halfmove_clock, fullmove_number])
    
    return " ".join(fen_parts)

def fen_to_board_state(fen: str) -> Optional[List[List[str]]]:
    """Convert FEN string to board state."""
    try:
        parts = fen.split()
        if len(parts) < 1:
            return None
        
        board_part = parts[0]
        rows = board_part.split('/')
        if len(rows) != 8:
            return None
        
        board_state = [['' for _ in range(8)] for _ in range(8)]
        
        for row_idx, row in enumerate(rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    # Empty squares
                    for _ in range(int(char)):
                        if col_idx < 8:
                            board_state[row_idx][col_idx] = ''
                            col_idx += 1
                else:
                    # Piece
                    if col_idx < 8:
                        board_state[row_idx][col_idx] = char
                        col_idx += 1
        
        return board_state
    except Exception:
        return None

def print_board_state(board_state: List[List[str]]):
    """Print board state in a readable format."""
    print("  a b c d e f g h")
    print("  ---------------")
    for row in range(8):
        print(f"{8-row} ", end="")
        for col in range(8):
            piece = board_state[row][col]
            if piece == '':
                print(". ", end="")
            else:
                print(f"{piece} ", end="")
        print(f" {8-row}")
    print("  ---------------")
    print("  a b c d e f g h")

def save_classification_results(results: List[Dict[str, Any]], filename: str = 'classification_results.json'):
    """Save classification results to JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Classification results saved to {filename}")
    except Exception as e:
        print(f"Error saving classification results: {e}")

def load_classification_results(filename: str = 'classification_results.json') -> Optional[List[Dict[str, Any]]]:
    """Load classification results from JSON file."""
    try:
        with open(filename, 'r') as f:
            results = json.load(f)
        return results
    except Exception as e:
        print(f"Error loading classification results: {e}")
        return None 