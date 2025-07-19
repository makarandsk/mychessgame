#!/usr/bin/env python3
"""
Chess game logic module.
Handles move validation, piece movement rules, and game state management.
"""

from typing import List, Tuple, Optional, Dict
import copy
import random
import time
import os
try:
    from stockfish import Stockfish
    STOCKFISH_AVAILABLE = True
except ImportError:
    STOCKFISH_AVAILABLE = False

class Move:
    """Represents a chess move with all necessary information for undo/redo."""
    
    def __init__(self, from_row: int, from_col: int, to_row: int, to_col: int, 
                 piece: Dict, captured_piece: Optional[Dict] = None, 
                 promotion_piece: Optional[str] = None, is_castling: bool = False,
                 castling_rook_from: Optional[Tuple[int, int]] = None,
                 castling_rook_to: Optional[Tuple[int, int]] = None,
                 en_passant_captured: Optional[Tuple[int, int]] = None,
                 en_passant_target_before: Optional[Tuple[int, int]] = None,
                 castling_rights_before: Optional[Dict] = None):
        self.from_row = from_row
        self.from_col = from_col
        self.to_row = to_row
        self.to_col = to_col
        self.piece = piece.copy()  # Copy the piece data
        self.captured_piece = captured_piece.copy() if captured_piece else None
        self.promotion_piece = promotion_piece
        self.is_castling = is_castling
        self.castling_rook_from = castling_rook_from
        self.castling_rook_to = castling_rook_to
        self.en_passant_captured = en_passant_captured
        self.en_passant_target_before = en_passant_target_before
        self.castling_rights_before = castling_rights_before.copy() if castling_rights_before else None
    
    def __str__(self):
        piece_name = self.piece['type']
        if self.promotion_piece:
            piece_name = self.promotion_piece
        return f"{self.piece['color']} {piece_name} {chr(97+self.from_col)}{8-self.from_row} to {chr(97+self.to_col)}{8-self.to_row}"

class ChessLogic:
    """Handles chess game logic and move validation."""
    
    def __init__(self):
        """Initialize chess logic."""
        self.board: List[List[Optional[Dict[str, str | bool]]]] = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = 'white'  # 'white' or 'black'
        self.game_over = False
        self.check = False
        self.checkmate = False
        self.stalemate = False
        
        # En passant tracking
        self.en_passant_target = None  # (row, col) of the square that can be captured en passant
        
        # Castling tracking
        self.white_kingside_castle = True
        self.white_queenside_castle = True
        self.black_kingside_castle = True
        self.black_queenside_castle = True
        
        # Move history and undo/redo
        self.move_history = []  # List of move objects
        self.redo_stack = []    # Stack for redo operations
        
        # Simple AI (no external dependencies)
        self.piece_values = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
        
        # Piece-square tables for positional evaluation
        self.pawn_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ]
        
        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]
        
        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]
        
        self.rook_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ]
        
        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]
        
        self.king_middle_table = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
        
        self.king_end_table = [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]
        
        # Opening book moves (common strong openings)
        self.opening_moves = [
            "e2e4", "d2d4", "c2c4", "g1f3", "b1c3", "f2f4", "b2b3", "g2g3",
            "e7e5", "d7d5", "c7c5", "g8f6", "b8c6", "f7f5", "b7b6", "g7g6"
        ]
        
        # Move counter for opening book
        self.move_count = 0
    
    @property
    def in_check(self) -> bool:
        """Property to check if the current player is in check."""
        return self.check
    
    def initialize_board(self):
        """Initialize the board with starting piece positions."""
        # Clear the board
        self.board = [[None for _ in range(8)] for _ in range(8)]
        
        # Set up pawns
        for col in range(8):
            self.board[1][col] = {'type': 'pawn', 'color': 'black', 'has_moved': False}
            self.board[6][col] = {'type': 'pawn', 'color': 'white', 'has_moved': False}
        
        # Set up other pieces
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        
        for col, piece in enumerate(piece_order):
            # Black pieces (top row)
            self.board[0][col] = {'type': piece, 'color': 'black', 'has_moved': False}
            # White pieces (bottom row)
            self.board[7][col] = {'type': piece, 'color': 'white', 'has_moved': False}
    
    def get_piece(self, row: int, col: int) -> Optional[Dict[str, str | bool]]:
        """Get piece at given position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within board bounds."""
        return 0 <= row < 8 and 0 <= col < 8
    
    def is_same_color(self, row1: int, col1: int, row2: int, col: int) -> bool:
        """Check if two pieces are the same color."""
        piece1 = self.get_piece(row1, col1)
        piece2 = self.get_piece(row2, col)
        return bool(piece1 and piece2 and piece1['color'] == piece2['color'])
    
    def get_valid_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get all valid moves for a piece at given position."""
        piece = self.get_piece(row, col)
        if not piece or piece['color'] != self.current_player:
            return []
        
        moves = []
        piece_type = piece['type']
        
        if piece_type == 'pawn':
            moves = self.get_pawn_moves(row, col)
        elif piece_type == 'rook':
            moves = self.get_rook_moves(row, col)
        elif piece_type == 'knight':
            moves = self.get_knight_moves(row, col)
        elif piece_type == 'bishop':
            moves = self.get_bishop_moves(row, col)
        elif piece_type == 'queen':
            moves = self.get_queen_moves(row, col)
        elif piece_type == 'king':
            moves = self.get_king_moves(row, col)
        
        # Filter out moves that would put/leave king in check
        return [move for move in moves if not self.would_be_in_check(row, col, move[0], move[1])]
    
    def get_pawn_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid pawn moves."""
        moves = []
        piece = self.get_piece(row, col)
        if not piece:
            return moves
        direction = -1 if piece['color'] == 'white' else 1  # White moves up, black moves down
        
        # Forward move
        new_row = row + direction
        if self.is_valid_position(new_row, col) and not self.get_piece(new_row, col):
            moves.append((new_row, col))
            
            # Double move from starting position
            if not piece['has_moved']:
                double_row = row + 2 * direction
                if self.is_valid_position(double_row, col) and not self.get_piece(double_row, col):
                    moves.append((double_row, col))
        
        # Diagonal captures
        for dcol in [-1, 1]:
            new_row = row + direction
            new_col = col + dcol
            if self.is_valid_position(new_row, new_col):
                target_piece = self.get_piece(new_row, new_col)
                if target_piece and target_piece['color'] != piece['color']:
                    moves.append((new_row, new_col))
        
        # En passant capture
        if self.en_passant_target is not None:
            en_passant_row, en_passant_col = self.en_passant_target
            if (row + direction == en_passant_row and abs(col - en_passant_col) == 1):
                moves.append((en_passant_row, en_passant_col))
        
        return moves
    
    def get_rook_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid rook moves."""
        moves = []
        piece = self.get_piece(row, col)
        if not piece:
            return moves
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for drow, dcol in directions:
            for i in range(1, 8):
                new_row = row + i * drow
                new_col = col + i * dcol
                
                if not self.is_valid_position(new_row, new_col):
                    break
                
                target_piece = self.get_piece(new_row, new_col)
                if not target_piece:
                    moves.append((new_row, new_col))
                elif target_piece['color'] != piece['color']:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        
        return moves
    
    def get_knight_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid knight moves."""
        moves = []
        piece = self.get_piece(row, col)
        if not piece:
            return moves
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for drow, dcol in knight_moves:
            new_row = row + drow
            new_col = col + dcol
            
            if self.is_valid_position(new_row, new_col):
                target_piece = self.get_piece(new_row, new_col)
                if not target_piece or target_piece['color'] != piece['color']:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_bishop_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid bishop moves."""
        moves = []
        piece = self.get_piece(row, col)
        if not piece:
            return moves
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for drow, dcol in directions:
            for i in range(1, 8):
                new_row = row + i * drow
                new_col = col + i * dcol
                
                if not self.is_valid_position(new_row, new_col):
                    break
                
                target_piece = self.get_piece(new_row, new_col)
                if not target_piece:
                    moves.append((new_row, new_col))
                elif target_piece['color'] != piece['color']:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        
        return moves
    
    def get_queen_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid queen moves (combination of rook and bishop)."""
        piece = self.get_piece(row, col)
        if not piece:
            return []
        return self.get_rook_moves(row, col) + self.get_bishop_moves(row, col)
    
    def get_king_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid king moves."""
        moves = []
        piece = self.get_piece(row, col)
        if not piece:
            return moves
        
        # Regular king moves
        king_moves = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        
        for drow, dcol in king_moves:
            new_row = row + drow
            new_col = col + dcol
            
            if self.is_valid_position(new_row, new_col):
                target_piece = self.get_piece(new_row, new_col)
                if not target_piece or target_piece['color'] != piece['color']:
                    moves.append((new_row, new_col))
        
        # Castling moves
        if not piece['has_moved'] and not self.check:
            # Kingside castling
            if piece['color'] == 'white' and self.can_castle_kingside('white'):
                moves.append((7, 6))  # Kingside castle
            
            # Queenside castling
            if piece['color'] == 'white' and self.can_castle_queenside('white'):
                moves.append((7, 2))  # Queenside castle
            
            # Black kingside castling
            if piece['color'] == 'black' and self.can_castle_kingside('black'):
                moves.append((0, 6))  # Kingside castle
            
            # Black queenside castling
            if piece['color'] == 'black' and self.can_castle_queenside('black'):
                moves.append((0, 2))  # Queenside castle
        
        return moves
    
    def would_be_in_check(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if a move would put/leave the king in check."""
        # Make a temporary move
        temp_board = copy.deepcopy(self.board)
        temp_board[to_row][to_col] = temp_board[from_row][from_col]
        temp_board[from_row][from_col] = None
        
        # Find king position
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = temp_board[row][col]
                if piece and piece['type'] == 'king' and piece['color'] == self.current_player:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Check if any opponent piece can attack the king
        opponent_color = 'black' if self.current_player == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = temp_board[row][col]
                if piece and piece['color'] == opponent_color:
                    if self.can_piece_attack(temp_board, row, col, king_pos[0], king_pos[1]):
                        return True
        
        return False
    
    def can_piece_attack(self, board: List[List], from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if a piece can attack a specific position."""
        piece = board[from_row][from_col]
        if not piece:
            return False
        
        piece_type = piece['type']
        
        if piece_type == 'pawn':
            direction = -1 if piece['color'] == 'white' else 1
            return (from_row + direction == to_row and 
                   abs(from_col - to_col) == 1)
        elif piece_type == 'rook':
            return self.can_rook_attack(board, from_row, from_col, to_row, to_col)
        elif piece_type == 'knight':
            return self.can_knight_attack(from_row, from_col, to_row, to_col)
        elif piece_type == 'bishop':
            return self.can_bishop_attack(board, from_row, from_col, to_row, to_col)
        elif piece_type == 'queen':
            return (self.can_rook_attack(board, from_row, from_col, to_row, to_col) or
                   self.can_bishop_attack(board, from_row, from_col, to_row, to_col))
        elif piece_type == 'king':
            return abs(from_row - to_row) <= 1 and abs(from_col - to_col) <= 1
        
        return False
    
    def can_rook_attack(self, board: List[List], from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if rook can attack target position."""
        if from_row != to_row and from_col != to_col:
            return False
        
        drow = 0 if from_row == to_row else (1 if to_row > from_row else -1)
        dcol = 0 if from_col == to_col else (1 if to_col > from_col else -1)
        
        row, col = from_row + drow, from_col + dcol
        while row != to_row or col != to_col:
            if board[row][col]:
                return False
            row += drow
            col += dcol
        
        return True
    
    def can_knight_attack(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if knight can attack target position."""
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for drow, dcol in knight_moves:
            if from_row + drow == to_row and from_col + dcol == to_col:
                return True
        
        return False
    
    def can_bishop_attack(self, board: List[List], from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if bishop can attack target position."""
        if abs(from_row - to_row) != abs(from_col - to_col):
            return False
        
        drow = 1 if to_row > from_row else -1
        dcol = 1 if to_col > from_col else -1
        
        row, col = from_row + drow, from_col + dcol
        while row != to_row and col != to_col:
            if board[row][col]:
                return False
            row += drow
            col += dcol
        
        return True
    
    def is_square_under_attack(self, row: int, col: int, by_color: str) -> bool:
        """Check if a square is under attack by pieces of the specified color."""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece['color'] == by_color:
                    if self.can_piece_attack(self.board, r, c, row, col):
                        return True
        return False
    
    def can_castle_kingside(self, color: str) -> bool:
        """Check if kingside castling is possible for the given color."""
        if color == 'white':
            if not self.white_kingside_castle:
                return False
            king_row, king_col = 7, 4
            rook_row, rook_col = 7, 7
        else:
            if not self.black_kingside_castle:
                return False
            king_row, king_col = 0, 4
            rook_row, rook_col = 0, 7
        
        # Check if king and rook are in correct positions
        king = self.get_piece(king_row, king_col)
        rook = self.get_piece(rook_row, rook_col)
        
        if not king or king['type'] != 'king' or king['color'] != color or king['has_moved']:
            return False
        if not rook or rook['type'] != 'rook' or rook['color'] != color or rook['has_moved']:
            return False
        
        # Check if squares between king and rook are empty
        for col in range(king_col + 1, rook_col):
            if self.get_piece(king_row, col) is not None:
                return False
        
        # Check if king is not in check and squares are not under attack
        opponent_color = 'black' if color == 'white' else 'white'
        
        # First check if king is currently in check
        if self.is_square_under_attack(king_row, king_col, opponent_color):
            return False
            
        # Then check if the squares the king will move through are under attack
        if self.is_square_under_attack(king_row, king_col + 1, opponent_color):
            return False
        if self.is_square_under_attack(king_row, king_col + 2, opponent_color):
            return False
        
        return True
    
    def can_castle_queenside(self, color: str) -> bool:
        """Check if queenside castling is possible for the given color."""
        if color == 'white':
            if not self.white_queenside_castle:
                return False
            king_row, king_col = 7, 4
            rook_row, rook_col = 7, 0
        else:
            if not self.black_queenside_castle:
                return False
            king_row, king_col = 0, 4
            rook_row, rook_col = 0, 0
        
        # Check if king and rook are in correct positions
        king = self.get_piece(king_row, king_col)
        rook = self.get_piece(rook_row, rook_col)
        
        if not king or king['type'] != 'king' or king['color'] != color or king['has_moved']:
            return False
        if not rook or rook['type'] != 'rook' or rook['color'] != color or rook['has_moved']:
            return False
        
        # Check if squares between king and rook are empty
        for col in range(rook_col + 1, king_col):
            if self.get_piece(king_row, col) is not None:
                return False
        
        # Check if king is not in check and squares are not under attack
        opponent_color = 'black' if color == 'white' else 'white'
        
        # First check if king is currently in check
        if self.is_square_under_attack(king_row, king_col, opponent_color):
            return False
            
        # Then check if the squares the king will move through are under attack
        if self.is_square_under_attack(king_row, king_col - 1, opponent_color):
            return False
        if self.is_square_under_attack(king_row, king_col - 2, opponent_color):
            return False
        
        return True
    
    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, promotion_piece: Optional[str] = None) -> bool:
        """Make a move if it's valid. Optionally promote pawn to a specified piece. Robustly allow all valid pawn promotions, including Stockfish moves like g2h1q."""
        valid_moves = self.get_valid_moves(from_row, from_col)
        is_valid = (to_row, to_col) in valid_moves

        piece = self.board[from_row][from_col]
        if piece is None:
            return False

        # Robust promotion handling: allow any pawn move to last rank with a valid promotion piece
        if (
            not is_valid and
            piece['type'] == 'pawn' and
            promotion_piece in ['queen', 'rook', 'bishop', 'knight'] and
            ((piece['color'] == 'white' and to_row == 0) or (piece['color'] == 'black' and to_row == 7))
        ):
            direction = -1 if piece['color'] == 'white' else 1
            # Forward promotion
            if from_col == to_col and self.board[to_row][to_col] is None and from_row + direction == to_row:
                is_valid = True
            # Capturing promotion
            elif abs(from_col - to_col) == 1 and from_row + direction == to_row:
                target_piece = self.board[to_row][to_col]
                if target_piece and target_piece['color'] != piece['color']:
                    is_valid = True
                # En passant promotion is not possible in chess
        if not is_valid:
            return False

        # ... existing code ...

        # Store castling rights before the move
        castling_rights_before = {
            'white_kingside': self.white_kingside_castle,
            'white_queenside': self.white_queenside_castle,
            'black_kingside': self.black_kingside_castle,
            'black_queenside': self.black_queenside_castle
        }
        
        # Store en passant target before the move
        en_passant_target_before = self.en_passant_target
        
        # Get captured piece (if any)
        captured_piece = self.board[to_row][to_col]
        
        # Check if this is a castling move
        is_castling = piece['type'] == 'king' and abs(from_col - to_col) == 2
        castling_rook_from = None
        castling_rook_to = None
        
        # Handle castling
        if is_castling:
            if to_col > from_col:  # Kingside castling
                rook_col = 7
                rook_row = 7 if piece['color'] == 'white' else 0
                castling_rook_from = (rook_row, rook_col)
                castling_rook_to = (rook_row, 5)
                rook = self.board[rook_row][rook_col]
                self.board[rook_row][5] = rook  # Move rook to col 5
                self.board[rook_row][rook_col] = None
                if rook:
                    rook['has_moved'] = True
            else:  # Queenside castling
                rook_col = 0
                rook_row = 7 if piece['color'] == 'white' else 0
                castling_rook_from = (rook_row, rook_col)
                castling_rook_to = (rook_row, 3)
                rook = self.board[rook_row][rook_col]
                self.board[rook_row][3] = rook  # Move rook to col 3
                self.board[rook_row][rook_col] = None
                if rook:
                    rook['has_moved'] = True
        
        # Handle en passant capture
        en_passant_captured = None
        if piece['type'] == 'pawn' and self.en_passant_target and (to_row, to_col) == self.en_passant_target:
            # Remove the captured pawn
            captured_row = from_row  # The pawn that was captured is on the same row as the moving pawn
            captured_col = to_col
            en_passant_captured = (captured_row, captured_col)
            self.board[captured_row][captured_col] = None
        
        # Make the regular move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        
        # Mark piece as moved
        piece['has_moved'] = True
        
        # Update castling rights
        if piece['type'] == 'king':
            if piece['color'] == 'white':
                self.white_kingside_castle = False
                self.white_queenside_castle = False
            else:
                self.black_kingside_castle = False
                self.black_queenside_castle = False
        elif piece['type'] == 'rook':
            if piece['color'] == 'white':
                if from_col == 7:  # Kingside rook
                    self.white_kingside_castle = False
                elif from_col == 0:  # Queenside rook
                    self.white_queenside_castle = False
            else:
                if from_col == 7:  # Kingside rook
                    self.black_kingside_castle = False
                elif from_col == 0:  # Queenside rook
                    self.black_queenside_castle = False
        
        # Set en passant target for next move
        self.en_passant_target = None
        if piece['type'] == 'pawn' and abs(from_row - to_row) == 2:
            # Double pawn move - set en passant target
            en_passant_row = (from_row + to_row) // 2
            self.en_passant_target = (en_passant_row, to_col)
        
        # Pawn promotion (only if promotion_piece is specified)
        if piece['type'] == 'pawn' and promotion_piece:
            if (piece['color'] == 'white' and to_row == 0) or (piece['color'] == 'black' and to_row == 7):
                if promotion_piece in ['queen', 'rook', 'bishop', 'knight']:
                    piece['type'] = promotion_piece
        
        # Record the move in history
        move = Move(
            from_row=from_row,
            from_col=from_col,
            to_row=to_row,
            to_col=to_col,
            piece=piece,
            captured_piece=captured_piece,
            promotion_piece=promotion_piece,
            is_castling=is_castling,
            castling_rook_from=castling_rook_from,
            castling_rook_to=castling_rook_to,
            en_passant_captured=en_passant_captured,
            en_passant_target_before=en_passant_target_before,
            castling_rights_before=castling_rights_before
        )
        self.move_history.append(move)
        
        # Clear redo stack when a new move is made
        self.redo_stack.clear()
        
        # Switch players
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Check for check/checkmate
        self.update_game_state()
        
        # Increment move counter for opening book
        self.move_count += 1
        
        return True
    
    def update_game_state(self):
        """Update game state (check, checkmate, stalemate)."""
        # Find current player's king
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece['type'] == 'king' and piece['color'] == self.current_player:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return
        
        # Check if king is in check
        opponent_color = 'black' if self.current_player == 'white' else 'white'
        self.check = False
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece['color'] == opponent_color:
                    if self.can_piece_attack(self.board, row, col, king_pos[0], king_pos[1]):
                        self.check = True
                        break
            if self.check:
                break
        
        # Check for checkmate/stalemate
        has_legal_moves = False
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece['color'] == self.current_player:
                    if self.get_valid_moves(row, col):
                        has_legal_moves = True
                        break
            if has_legal_moves:
                break
        
        if not has_legal_moves:
            if self.check:
                self.checkmate = True
                self.game_over = True
            else:
                self.stalemate = True
                self.game_over = True
    
    def undo_move(self) -> bool:
        """Undo the last move. Returns True if successful, False if no moves to undo."""
        if not self.move_history:
            return False
        
        # Get the last move
        move = self.move_history.pop()
        
        # Store the move for potential redo
        self.redo_stack.append(move)
        
        # Restore the moved piece to its original position
        self.board[move.from_row][move.from_col] = move.piece
        self.board[move.to_row][move.to_col] = None
        # Restore pawn if this was a promotion
        if move.promotion_piece:
            self.board[move.from_row][move.from_col]['type'] = 'pawn'
        
        # Reset the has_moved flag for the moved piece
        move.piece['has_moved'] = False
        
        # Restore captured piece (if any)
        if move.captured_piece:
            self.board[move.to_row][move.to_col] = move.captured_piece
        
        # Handle castling undo
        if move.is_castling and move.castling_rook_from and move.castling_rook_to:
            # Move the rook back
            rook_row, rook_col = move.castling_rook_from
            to_row, to_col = move.castling_rook_to
            rook = self.board[to_row][to_col]
            self.board[rook_row][rook_col] = rook
            self.board[to_row][to_col] = None
            if rook:
                rook['has_moved'] = False
        
        # Handle en passant undo
        if move.en_passant_captured:
            captured_row, captured_col = move.en_passant_captured
            # Restore the captured pawn
            self.board[captured_row][captured_col] = move.captured_piece
        
        # Restore en passant target
        self.en_passant_target = move.en_passant_target_before
        
        # Restore castling rights
        if move.castling_rights_before:
            self.white_kingside_castle = move.castling_rights_before['white_kingside']
            self.white_queenside_castle = move.castling_rights_before['white_queenside']
            self.black_kingside_castle = move.castling_rights_before['black_kingside']
            self.black_queenside_castle = move.castling_rights_before['black_queenside']
        
        # Switch players back
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Reset game state
        self.game_over = False
        self.checkmate = False
        self.stalemate = False
        
        # Update game state
        self.update_game_state()
        
        return True
    
    def redo_move(self) -> bool:
        """Redo the last undone move. Returns True if successful, False if no moves to redo."""
        if not self.redo_stack:
            return False
        
        # Get the move to redo
        move = self.redo_stack.pop()
        
        # Add it back to move history
        self.move_history.append(move)
        
        # Reapply the move directly without calling make_move to avoid duplicates
        # Get the moving piece
        piece = self.board[move.from_row][move.from_col]
        if piece is None:
            return False
        
        # Handle castling redo
        if move.is_castling and move.castling_rook_from and move.castling_rook_to:
            if move.to_col > move.from_col:  # Kingside castling
                rook_col = 7
                rook_row = 7 if piece['color'] == 'white' else 0
                rook = self.board[rook_row][rook_col]
                self.board[rook_row][5] = rook  # Move rook to col 5
                self.board[rook_row][rook_col] = None
                if rook:
                    rook['has_moved'] = True
            else:  # Queenside castling
                rook_col = 0
                rook_row = 7 if piece['color'] == 'white' else 0
                rook = self.board[rook_row][rook_col]
                self.board[rook_row][3] = rook  # Move rook to col 3
                self.board[rook_row][rook_col] = None
                if rook:
                    rook['has_moved'] = True
        
        # Handle en passant capture redo
        if move.en_passant_captured:
            captured_row, captured_col = move.en_passant_captured
            self.board[captured_row][captured_col] = None
        
        # Make the regular move
        self.board[move.to_row][move.to_col] = piece
        self.board[move.from_row][move.from_col] = None
        
        # Mark piece as moved
        piece['has_moved'] = True
        
        # Update castling rights
        if piece['type'] == 'king':
            if piece['color'] == 'white':
                self.white_kingside_castle = False
                self.white_queenside_castle = False
            else:
                self.black_kingside_castle = False
                self.black_queenside_castle = False
        elif piece['type'] == 'rook':
            if piece['color'] == 'white':
                if move.from_col == 7:  # Kingside rook
                    self.white_kingside_castle = False
                elif move.from_col == 0:  # Queenside rook
                    self.white_queenside_castle = False
            else:
                if move.from_col == 7:  # Kingside rook
                    self.black_kingside_castle = False
                elif move.from_col == 0:  # Queenside rook
                    self.black_queenside_castle = False
        
        # Set en passant target for next move
        self.en_passant_target = None
        if piece['type'] == 'pawn' and abs(move.from_row - move.to_row) == 2:
            # Double pawn move - set en passant target
            en_passant_row = (move.from_row + move.to_row) // 2
            self.en_passant_target = (en_passant_row, move.to_col)
        
        # Pawn promotion
        if move.promotion_piece:
            if (piece['color'] == 'white' and move.to_row == 0) or (piece['color'] == 'black' and move.to_row == 7):
                if move.promotion_piece in ['queen', 'rook', 'bishop', 'knight']:
                    piece['type'] = move.promotion_piece
        
        # Switch players
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Check for check/checkmate
        self.update_game_state()
        
        return True
    
    def get_move_history(self) -> List[Move]:
        """Get the list of moves made so far."""
        return self.move_history.copy()
    
    def get_move_count(self) -> int:
        """Get the number of moves made so far."""
        return len(self.move_history)
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.move_history) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0
    
    def get_fen_position(self) -> str:
        """Generate FEN (Forsyth-Edwards Notation) for the current position."""
        fen_parts = []
        
        # Board position
        board_str = ""
        for row in range(8):
            empty_count = 0
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        board_str += str(empty_count)
                        empty_count = 0
                    
                    # Piece letter
                    piece_type = piece['type']
                    color = piece['color']
                    
                    if piece_type == 'pawn':
                        letter = 'P' if color == 'white' else 'p'
                    elif piece_type == 'rook':
                        letter = 'R' if color == 'white' else 'r'
                    elif piece_type == 'knight':
                        letter = 'N' if color == 'white' else 'n'
                    elif piece_type == 'bishop':
                        letter = 'B' if color == 'white' else 'b'
                    elif piece_type == 'queen':
                        letter = 'Q' if color == 'white' else 'q'
                    elif piece_type == 'king':
                        letter = 'K' if color == 'white' else 'k'
                    
                    board_str += letter
            
            if empty_count > 0:
                board_str += str(empty_count)
            
            if row < 7:
                board_str += "/"
        
        fen_parts.append(board_str)
        
        # Active color
        fen_parts.append('w' if self.current_player == 'white' else 'b')
        
        # Castling availability
        castling = ""
        # White kingside
        wk = self.get_piece(7, 4)
        wrk = self.get_piece(7, 7)
        if wk is not None and wk.get('type') == 'king' and wrk is not None and wrk.get('type') == 'rook' and self.white_kingside_castle:
            castling += "K"
        # White queenside
        wq = self.get_piece(7, 0)
        if wk is not None and wk.get('type') == 'king' and wq is not None and wq.get('type') == 'rook' and self.white_queenside_castle:
            castling += "Q"
        # Black kingside
        bk = self.get_piece(0, 4)
        brk = self.get_piece(0, 7)
        if bk is not None and bk.get('type') == 'king' and brk is not None and brk.get('type') == 'rook' and self.black_kingside_castle:
            castling += "k"
        # Black queenside
        bq = self.get_piece(0, 0)
        if bk is not None and bk.get('type') == 'king' and bq is not None and bq.get('type') == 'rook' and self.black_queenside_castle:
            castling += "q"
        if not castling:
            castling = "-"
        fen_parts.append(castling)
        
        # En passant target square
        if self.en_passant_target:
            row, col = self.en_passant_target
            en_passant_square = f"{chr(97 + col)}{8 - row}"
        else:
            en_passant_square = "-"
        fen_parts.append(en_passant_square)
        
        # Halfmove clock (we'll use 0 for simplicity)
        fen_parts.append("0")
        
        # Fullmove number (we'll use 1 for simplicity)
        fen_parts.append("1")
        
        return " ".join(fen_parts)
    
    def evaluate_position(self) -> float:
        """Evaluate the current position. Uses advanced evaluation for strong play."""
        return self.advanced_evaluate_position()
    
    def advanced_evaluate_position(self) -> float:
        """Advanced position evaluation with piece-square tables and tactical awareness."""
        try:
            score = 0.0
            
            # Count pieces and evaluate position
            for row in range(8):
                for col in range(8):
                    piece = self.get_piece(row, col)
                    if piece:
                        piece_type = piece['type']
                        color = piece['color']
                        multiplier = 1 if color == 'white' else -1
                        
                        # Material value
                        if piece_type in self.piece_values:
                            score += self.piece_values[piece_type] * multiplier
                        
                        # Positional value from piece-square tables
                        if piece_type == 'pawn':
                            table_value = self.pawn_table[row][col] if color == 'white' else self.pawn_table[7-row][col]
                            score += table_value * multiplier
                        elif piece_type == 'knight':
                            table_value = self.knight_table[row][col] if color == 'white' else self.knight_table[7-row][col]
                            score += table_value * multiplier
                        elif piece_type == 'bishop':
                            table_value = self.bishop_table[row][col] if color == 'white' else self.bishop_table[7-row][col]
                            score += table_value * multiplier
                        elif piece_type == 'rook':
                            table_value = self.rook_table[row][col] if color == 'white' else self.rook_table[7-row][col]
                            score += table_value * multiplier
                        elif piece_type == 'queen':
                            table_value = self.queen_table[row][col] if color == 'white' else self.queen_table[7-row][col]
                            score += table_value * multiplier
                        elif piece_type == 'king':
                            # Use different tables for middle game vs endgame
                            if self.is_endgame():
                                table_value = self.king_end_table[row][col] if color == 'white' else self.king_end_table[7-row][col]
                            else:
                                table_value = self.king_middle_table[row][col] if color == 'white' else self.king_middle_table[7-row][col]
                            score += table_value * multiplier
            
            # Bonus for center control
            center_bonus = self.evaluate_center_control()
            score += center_bonus
            
            # Bonus for development
            development_bonus = self.evaluate_development()
            score += development_bonus
            
            # Bonus for king safety
            king_safety_bonus = self.evaluate_king_safety()
            score += king_safety_bonus
            
            # Bonus for pawn structure
            pawn_structure_bonus = self.evaluate_pawn_structure()
            score += pawn_structure_bonus
            
            return score
            
        except Exception as e:
            print(f"Error in advanced evaluation: {e}")
            return self.simple_evaluate_position()
    
    def evaluate_center_control(self) -> float:
        """Evaluate control of center squares."""
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        score = 0.0
        
        for row, col in center_squares:
            # Check if square is attacked by white
            if self.is_square_under_attack(row, col, 'white'):
                score += 15
            # Check if square is attacked by black
            if self.is_square_under_attack(row, col, 'black'):
                score -= 15
        
        return score
    
    def evaluate_development(self) -> float:
        """Evaluate piece development."""
        score = 0.0
        
        # Bonus for developed knights and bishops
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece:
                    if piece['type'] in ['knight', 'bishop']:
                        if piece['color'] == 'white' and row < 6:  # Developed
                            score += 20
                        elif piece['color'] == 'black' and row > 1:  # Developed
                            score -= 20
        
        return score
    
    def evaluate_king_safety(self) -> float:
        """Evaluate king safety."""
        score = 0.0
        
        # Find kings
        white_king_pos = None
        black_king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece['type'] == 'king':
                    if piece['color'] == 'white':
                        white_king_pos = (row, col)
                    else:
                        black_king_pos = (row, col)
        
        # Evaluate white king safety
        if white_king_pos:
            row, col = white_king_pos
            if row == 7:  # King still on back rank
                score -= 40
            if abs(col - 3.5) > 2:  # King far from center
                score -= 25
        
        # Evaluate black king safety
        if black_king_pos:
            row, col = black_king_pos
            if row == 0:  # King still on back rank
                score += 40
            if abs(col - 3.5) > 2:  # King far from center
                score += 25
        
        return score
    
    def evaluate_pawn_structure(self) -> float:
        """Evaluate pawn structure."""
        score = 0.0
        
        # Bonus for connected pawns
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece['type'] == 'pawn':
                    # Check for connected pawns
                    for dcol in [-1, 1]:
                        if 0 <= col + dcol < 8:
                            neighbor = self.get_piece(row, col + dcol)
                            if neighbor and neighbor['type'] == 'pawn' and neighbor['color'] == piece['color']:
                                if piece['color'] == 'white':
                                    score += 10
                                else:
                                    score -= 10
        
        return score
    
    def is_endgame(self) -> bool:
        """Check if we're in an endgame (few pieces remaining)."""
        piece_count = 0
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece['type'] != 'king':
                    piece_count += 1
        return piece_count <= 12
    
    def simple_evaluate_position(self) -> float:
        """Simple position evaluation that won't crash."""
        try:
            score = 0.0
            
            # Count material
            for row in range(8):
                for col in range(8):
                    piece = self.get_piece(row, col)
                    if piece:
                        piece_type = piece['type']
                        color = piece['color']
                        multiplier = 1 if color == 'white' else -1
                        
                        # Material value
                        if piece_type in self.piece_values:
                            score += self.piece_values[piece_type] * multiplier
                        
                        # Simple positional bonus
                        if piece_type == 'pawn':
                            if color == 'white':
                                score += (7 - row) * 5  # Bonus for advancing pawns
                            else:
                                score -= row * 5
                        
                        # Center control bonus for knights and bishops
                        if piece_type in ['knight', 'bishop']:
                            center_distance = abs(3.5 - row) + abs(3.5 - col)
                            if color == 'white':
                                score += (7 - center_distance) * 2
                            else:
                                score -= (7 - center_distance) * 2
            
            return score
            
        except Exception as e:
            print(f"Error in simple evaluation: {e}")
            return 0.0
    
    def convert_uci_to_coordinates(self, uci_move: str) -> Optional[Tuple[int, int, int, int]]:
        """Convert UCI move format (e.g., 'e2e4') to board coordinates."""
        if len(uci_move) != 4:
            return None
        
        try:
            from_col = ord(uci_move[0]) - ord('a')
            from_row = 8 - int(uci_move[1])
            to_col = ord(uci_move[2]) - ord('a')
            to_row = 8 - int(uci_move[3])
            
            if (0 <= from_row < 8 and 0 <= from_col < 8 and 
                0 <= to_row < 8 and 0 <= to_col < 8):
                return (from_row, from_col, to_row, to_col)
            else:
                return None
        except (ValueError, IndexError):
            return None
    
    def get_ai_best_move(self, time_ms: int = 1000) -> Optional[str]:
        """Get the best move using optimized AI algorithms, symmetric for both sides."""
        try:
            print("AI starting move calculation...")
            original_player = self.current_player
            # Use opening book for first few moves
            if self.move_count < 8 and self.move_count < len(self.opening_moves):
                opening_move = self.opening_moves[self.move_count]
                coords = self.convert_uci_to_coordinates(opening_move)
                if coords:
                    from_row, from_col, to_row, to_col = coords
                    piece = self.get_piece(from_row, from_col)
                    if piece and piece['color'] == self.current_player:
                        valid_moves = self.get_valid_moves(from_row, from_col)
                        if (to_row, to_col) in valid_moves:
                            print(f"AI uses opening book: {opening_move}")
                            return opening_move
            # Fast AI: evaluate all moves and pick the best one
            valid_moves = self.get_all_valid_moves(self.current_player)
            if not valid_moves:
                print("No valid moves found for AI")
                return None
            # Sort moves by priority (captures first, then center moves, then others)
            valid_moves = self.sort_moves_by_priority(valid_moves)
            best_move = None
            best_score = float('-inf')
            print(f"AI evaluating {len(valid_moves)} moves...")
            # Use iterative deepening with time limit
            max_depth = 3  # Reduced from 5 to 3 for speed
            start_time = time.time()
            for depth in range(1, max_depth + 1):
                if time.time() - start_time > time_ms / 1000.0:
                    print(f"Time limit reached at depth {depth-1}")
                    break
                print(f"Searching to depth {depth}...")
                for from_row, from_col, to_row, to_col in valid_moves:
                    if time.time() - start_time > time_ms / 1000.0:
                        break
                    temp_board = copy.deepcopy(self.board)
                    original_piece = self.board[from_row][from_col]
                    captured_piece = self.board[to_row][to_col]
                    self.board[to_row][to_col] = original_piece
                    self.board[from_row][from_col] = None
                    # Switch player for minimax
                    self.current_player = 'black' if self.current_player == 'white' else 'white'
                    # Always maximize for the original player
                    maximizing = (original_player == 'white')
                    score = self.fast_minimax(depth - 1, float('-inf'), float('inf'), maximizing)
                    # Restore board
                    self.board = temp_board
                    self.current_player = original_player
                    uci_move = f"{chr(97 + from_col)}{8 - from_row}{chr(97 + to_col)}{8 - to_row}"
                    if score > best_score:
                        best_score = score
                        best_move = uci_move
            if best_move:
                print(f"AI suggests: {best_move} (score: {best_score:.1f})")
            return best_move
        except Exception as e:
            print(f"Error in AI best move calculation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_all_valid_moves(self, color: str) -> List[Tuple[int, int, int, int]]:
        """Get all valid moves for a given color."""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece['color'] == color:
                    valid_moves = self.get_valid_moves(row, col)
                    for to_row, to_col in valid_moves:
                        moves.append((row, col, to_row, to_col))
        return moves
    
    def sort_moves_by_priority(self, moves: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Sort moves by priority for better alpha-beta pruning."""
        move_scores = []
        
        for from_row, from_col, to_row, to_col in moves:
            score = 0
            
            # Captures get highest priority
            captured_piece = self.get_piece(to_row, to_col)
            if captured_piece and captured_piece['type'] in self.piece_values:
                score += 1000 + self.piece_values[captured_piece['type']]
            
            # Center moves get medium priority
            center_distance = abs(3.5 - to_row) + abs(3.5 - to_col)
            score += (7 - center_distance) * 10
            
            # Pawn advances get bonus
            piece = self.get_piece(from_row, from_col)
            if piece and piece['type'] == 'pawn':
                if piece['color'] == 'white':
                    score += (7 - to_row) * 5
                else:
                    score += to_row * 5
            
            move_scores.append((score, (from_row, from_col, to_row, to_col)))
        
        # Sort by score (highest first)
        move_scores.sort(reverse=True)
        return [move for score, move in move_scores]
    
    def fast_minimax(self, depth: int, alpha: float, beta: float, maximizing: bool, trans_table=None) -> float:
        """Fast minimax with quiescence, transposition table, and improved move ordering."""
        if trans_table is None:
            trans_table = {}
        board_hash = self.get_board_hash() + f"_{depth}_{maximizing}"
        if board_hash in trans_table:
            return trans_table[board_hash]
        if depth == 0:
            val = self.quiescence_search(alpha, beta, maximizing)
            trans_table[board_hash] = val
            return val
        if maximizing:
            max_eval = float('-inf')
            moves = self.get_all_valid_moves('white')
            moves = self.sort_moves_by_priority(moves)  # Improved move ordering
            for from_row, from_col, to_row, to_col in moves:
                temp_board = copy.deepcopy(self.board)
                original_piece = self.board[from_row][from_col]
                captured_piece = self.board[to_row][to_col]
                self.board[to_row][to_col] = original_piece
                self.board[from_row][from_col] = None
                self.current_player = 'black'
                eval_score = self.fast_minimax(depth - 1, alpha, beta, False, trans_table)
                self.board = temp_board
                self.current_player = 'white'
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            trans_table[board_hash] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            moves = self.get_all_valid_moves('black')
            moves = self.sort_moves_by_priority(moves)  # Improved move ordering
            for from_row, from_col, to_row, to_col in moves:
                temp_board = copy.deepcopy(self.board)
                original_piece = self.board[from_row][from_col]
                captured_piece = self.board[to_row][to_col]
                self.board[to_row][to_col] = original_piece
                self.board[from_row][from_col] = None
                self.current_player = 'white'
                eval_score = self.fast_minimax(depth - 1, alpha, beta, True, trans_table)
                self.board = temp_board
                self.current_player = 'black'
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            trans_table[board_hash] = min_eval
            return min_eval
    
    def quiescence_search(self, alpha: float, beta: float, maximizing: bool) -> float:
        """Quiescence search: extend search for captures to avoid horizon effect."""
        stand_pat = self.fast_evaluate_position()
        if maximizing:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
        # Generate all capture moves for the current player
        color = 'white' if maximizing else 'black'
        capture_moves = self.get_all_capture_moves(color)
        found_capture = False
        for from_row, from_col, to_row, to_col in capture_moves:
            found_capture = True
            temp_board = copy.deepcopy(self.board)
            captured_piece = self.board[to_row][to_col]
            piece = self.board[from_row][from_col]
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            self.current_player = 'black' if color == 'white' else 'white'
            score = self.quiescence_search(alpha, beta, not maximizing)
            self.board = temp_board
            self.current_player = color
            if maximizing:
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            else:
                if score < beta:
                    beta = score
                if beta <= alpha:
                    break
        if not found_capture:
            return stand_pat
        return alpha if maximizing else beta
    
    def get_all_capture_moves(self, color: str) -> list:
        """Return all capture moves for the given color."""
        moves = []
        for from_row in range(8):
            for from_col in range(8):
                piece = self.get_piece(from_row, from_col)
                if piece and piece['color'] == color:
                    valid_moves = self.get_valid_moves(from_row, from_col)
                    for to_row, to_col in valid_moves:
                        target = self.get_piece(to_row, to_col)
                        if target and target['color'] != color:
                            moves.append((from_row, from_col, to_row, to_col))
        return moves
    
    def reset_game(self):
        """Fully reset the game state, board, and all flags."""
        self.initialize_board()
        self.current_player = 'white'
        self.game_over = False
        self.check = False
        self.checkmate = False
        self.stalemate = False
        self.en_passant_target = None
        self.white_kingside_castle = True
        self.white_queenside_castle = True
        self.black_kingside_castle = True
        self.black_queenside_castle = True
        self.move_history.clear()
        self.redo_stack.clear()
        self.move_count = 0
        # Update game state to ensure everything is clean
        self.update_game_state()

    def fast_evaluate_position(self) -> float:
        """Advanced evaluation: material, king safety, pawn structure, activity, bishop pair, etc."""
        try:
            score = 0.0
            white_bishops = 0
            black_bishops = 0
            white_king_pos = None
            black_king_pos = None
            pawn_files = {'white': set(), 'black': set()}
            for row in range(8):
                for col in range(8):
                    piece = self.get_piece(row, col)
                    if piece:
                        piece_type = str(piece['type'])
                        color = str(piece['color'])
                        multiplier = 1 if color == 'white' else -1
                        # Material value
                        if piece_type in self.piece_values:
                            score += self.piece_values[piece_type] * multiplier
                        # Pawn structure
                        if piece_type == 'pawn':
                            pawn_files[color].add(col)
                            # Passed pawn bonus
                            if self.is_passed_pawn(row, col, color):
                                score += 40 * multiplier
                            # Doubled pawn penalty
                            if self.is_doubled_pawn(row, col, color):
                                score -= 20 * multiplier
                            # Isolated pawn penalty
                            if self.is_isolated_pawn(row, col, color):
                                score -= 15 * multiplier
                        # Piece activity
                        if piece_type in ['knight', 'bishop', 'rook', 'queen']:
                            # Center control
                            center_distance = abs(3.5 - row) + abs(3.5 - col)
                            score += (7 - center_distance) * 2 * multiplier
                        # Rook on 7th/2nd rank
                        if piece_type == 'rook':
                            if (color == 'white' and row == 1) or (color == 'black' and row == 6):
                                score += 30 * multiplier
                        # Bishop pair
                        if piece_type == 'bishop':
                            if color == 'white':
                                white_bishops += 1
                            else:
                                black_bishops += 1
                        # King position
                        if piece_type == 'king':
                            if color == 'white':
                                white_king_pos = (row, col)
                            else:
                                black_king_pos = (row, col)
            # Bishop pair bonus
            if white_bishops >= 2:
                score += 40
            if black_bishops >= 2:
                score -= 40
            # King safety
            score += self.king_safety_eval(white_king_pos, 'white')
            score -= self.king_safety_eval(black_king_pos, 'black')
            # Tactical awareness
            score += self.tactical_evaluation()
            return score
        except Exception as e:
            print(f"Error in advanced evaluation: {e}")
            return 0.0

    def is_passed_pawn(self, row, col, color):
        # No enemy pawns in front or on adjacent files
        direction = -1 if color == 'white' else 1
        for r in range(row + direction, 8 if color == 'black' else -1, direction):
            for dc in [-1, 0, 1]:
                c = col + dc
                if 0 <= c < 8:
                    piece = self.get_piece(r, c)
                    if piece and piece['type'] == 'pawn' and piece['color'] != color:
                        return False
        return True

    def is_doubled_pawn(self, row, col, color):
        # Another pawn of same color on same file
        for r in range(8):
            if r != row:
                piece = self.get_piece(r, col)
                if piece and piece['type'] == 'pawn' and piece['color'] == color:
                    return True
        return False

    def is_isolated_pawn(self, row, col, color):
        # No friendly pawns on adjacent files
        for dc in [-1, 1]:
            c = col + dc
            if 0 <= c < 8:
                for r in range(8):
                    piece = self.get_piece(r, c)
                    if piece and piece['type'] == 'pawn' and piece['color'] == color:
                        return False
        return True

    def king_safety_eval(self, king_pos, color):
        score = 0.0
        if not king_pos:
            score -= 200.0  # King missing (should not happen)
        else:
            row, col = king_pos
            # Bonus for castling (king not on original square)
            if (color == 'white' and row == 7 and col in [6, 2]) or (color == 'black' and row == 0 and col in [6, 2]):
                score += 30.0
            # Penalty for king in center in late game
            if (color == 'white' and row < 5) or (color == 'black' and row > 2):
                score -= 20.0
            # Penalty for open files near king
            for dc in [-1, 0, 1]:
                c = col + dc
                if 0 <= c < 8:
                    open_file = True
                    for r in range(8):
                        piece = self.get_piece(r, c)
                        if piece and piece['type'] == 'pawn' and piece['color'] == color:
                            open_file = False
                            break
                    if open_file:
                        score -= 10.0
        return score

    # --- Transposition Table ---
    def get_board_hash(self):
        # Use a simple FEN string as a hash key
        return self.get_fen_position()

    def tactical_evaluation(self) -> float:
        """Penalize hanging pieces and reward capturing hanging enemy pieces."""
        penalty = 0.0
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece:
                    color = str(piece['color'])
                    piece_type = str(piece['type'])
                    opponent = 'black' if color == 'white' else 'white'
                    # Is this piece attacked by opponent?
                    if self.is_square_under_attack(row, col, opponent):
                        # Is it defended?
                        defended = self.is_square_under_attack(row, col, color)
                        if not defended:
                            # Hanging piece! Penalize by its value
                            if piece_type in self.piece_values:
                                penalty += (-1 if color == 'white' else 1) * self.piece_values[piece_type] * 0.7
        return penalty

    def init_stockfish(self, path: str = "stockfish-windows-x86-64-avx2.exe"):
        """Initialize Stockfish engine if available."""
        if STOCKFISH_AVAILABLE and os.path.exists(path):
            try:
                self.stockfish = Stockfish(path=path, parameters={"Threads": 2, "Minimum Thinking Time": 30})
                self.stockfish.set_skill_level(20)
                print("Stockfish engine initialized!")
            except Exception as e:
                print(f"Error initializing Stockfish: {e}")
                self.stockfish = None
        else:
            self.stockfish = None
            print(f"Stockfish engine not available. Looking for: {path}")
            if not STOCKFISH_AVAILABLE:
                print("Stockfish Python package not installed.")
            if not os.path.exists(path):
                print(f"Stockfish executable not found at: {path}")

    def is_valid_for_stockfish(self) -> bool:
        """Check if the board is valid for Stockfish (both sides have one king, no more than 8 pawns per side, no pawns on first or last rank)."""
        white_kings = 0
        black_kings = 0
        white_pawns = 0
        black_pawns = 0
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece:
                    if piece['type'] == 'king':
                        if piece['color'] == 'white':
                            white_kings += 1
                        else:
                            black_kings += 1
                    if piece['type'] == 'pawn':
                        if piece['color'] == 'white':
                            white_pawns += 1
                        else:
                            black_pawns += 1
        # Check for pawns on first or last rank (illegal in FEN/Stockfish)
        for col in range(8):
            piece_first = self.board[0][col]
            piece_last = self.board[7][col]
            if piece_first is not None and piece_first.get('type') == 'pawn':
                print("Invalid position for Stockfish: pawn on first rank (row 0)")
                return False
            if piece_last is not None and piece_last.get('type') == 'pawn':
                print("Invalid position for Stockfish: pawn on last rank (row 7)")
                return False
        if white_kings != 1 or black_kings != 1:
            print(f"Invalid position for Stockfish: white_kings={white_kings}, black_kings={black_kings}")
            return False
        if white_pawns > 8 or black_pawns > 8:
            print(f"Invalid position for Stockfish: too many pawns (white={white_pawns}, black={black_pawns})")
            return False
        return True

    def get_stockfish_best_move(self, time_ms: int = 1000) -> Optional[str]:
        """Get the best move from Stockfish if available, else None."""
        if not self.is_valid_for_stockfish():
            print("Position is not valid for Stockfish. Please ensure both sides have one king, no more than 8 pawns each, and no pawns on the first or last rank.")
            return None
        if not hasattr(self, 'stockfish') or self.stockfish is None:
            self.init_stockfish()
        if self.stockfish:
            fen = self.get_fen_position()
            try:
                self.stockfish.set_fen_position(fen)
            except Exception as e:
                print(f"Stockfish FEN error: {e}\nFEN: {fen}")
                return None
            move = self.stockfish.get_best_move_time(time=time_ms)
            print(f"Stockfish suggests: {move}")
            return move
        else:
            print("Stockfish not available, using Python AI.")
            return self.get_ai_best_move(time_ms)

    def clear_board(self):
        """Clear the board for setup mode."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = 'white'
        self.game_over = False
        self.check = False
        self.checkmate = False
        self.stalemate = False
        self.en_passant_target = None
        self.white_kingside_castle = True
        self.white_queenside_castle = True
        self.black_kingside_castle = True
        self.black_queenside_castle = True
        self.move_history.clear()
        self.redo_stack.clear()
        self.move_count = 0
        print("Board cleared for setup mode")