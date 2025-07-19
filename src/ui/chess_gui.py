#!/usr/bin/env python3
"""
Chess GUI using Pygame.
Handles board rendering, piece display, and basic game interface.
"""

import pygame
import os
import sys
from typing import Optional, List, Tuple, Union, Dict
import time
import tkinter as tk
from tkinter import filedialog
import threading
import cv2
import numpy as np
import shutil

# Add the src directory to the path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.chess_logic import ChessLogic
from extract_board_and_squares import detect_board_and_extract_squares

class ChessPiece:
    """Represents a chess piece with its type, color, and position."""
    
    def __init__(self, piece_type: str, color: str, position: Tuple[int, int]):
        self.piece_type = piece_type  # 'pawn', 'rook', 'knight', 'bishop', 'queen', 'king'
        self.color = color  # 'white' or 'black'
        self.position = position  # (row, col)
        self.has_moved = False
    
    def __str__(self):
        return f"{self.color} {self.piece_type} at {self.position}"

class ChessGUI:
    """Main chess GUI class using Pygame."""
    
    def __init__(self, window_size: int = 640):
        """Initialize the chess GUI."""
        pygame.init()
        
        self.square_size = window_size // 8
        self.status_bar_height = 110
        self.palette_width = self.square_size
        self.notation_space = self.square_size // 3  # Space for notations inside squares

        self.board_pixel_size = self.square_size * 8
        self.total_width = self.board_pixel_size + 2 * self.palette_width + 2 * self.notation_space
        self.total_height = self.board_pixel_size + self.status_bar_height + self.notation_space
        
        # Colors
        self.light_square = (240, 217, 181)  # Light brown
        self.dark_square = (181, 136, 99)    # Dark brown
        self.highlight_color = (255, 255, 0, 128)  # Yellow highlight
        self.valid_move_color = (0, 255, 0, 128)   # Green for valid moves
        self.setup_highlight_color = (255, 0, 0, 128)  # Red for setup mode
        
        # Initialize display with increased width for palettes and notations
        self.screen = pygame.display.set_mode((self.total_width, self.total_height))
        pygame.display.set_caption("Chess Game")
        
        # Debug: Print window dimensions
        print(f"Chess GUI initialized:")
        print(f"  Window size: {window_size}")
        print(f"  Status bar height: {self.status_bar_height}")
        print(f"  Total height: {self.total_height}")
        print(f"  Screen size: {self.screen.get_size()}")
        
        # Initialize chess logic
        self.chess_logic = ChessLogic()
        self.chess_logic.initialize_board()
        
        # Game state
        self.selected_piece: Optional[Tuple[int, int]] = None
        self.valid_moves: List[Tuple[int, int]] = []
        self.promotion_pending = None  # (from_row, from_col, to_row, to_col)
        self.promotion_color = None
        self.promotion_square = None
        self.promotion_choices = ['queen', 'rook', 'bishop', 'knight']
        self.promotion_rects = []
        self.ai_thinking = False  # Track if AI is currently thinking
        
        # Setup mode state
        self.setup_mode = False
        self.selected_setup_piece = None  # (piece_type, color) or None
        self.piece_palette_rects = {}  # Store piece palette rectangles
        
        # Font for text display
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self._button_rects = {}
        self.last_ai_move = None  # Store last Stockfish/AI move for display
        self.status_message = ""
        
        # Add upload image button
        # self._button_rects['capture_image'] = pygame.Rect(200, self.total_height - self.status_bar_height + 60, 160, 40)
        # capture_rect = self._button_rects['capture_image']
        # self._button_rects['upload_image'] = pygame.Rect(
        #     capture_rect.right + 20,  # 20 pixels to the right of capture
        #     capture_rect.y,
        #     160,
        #     40
        # )
    
    def get_piece_at(self, row: int, col: int) -> Optional[Dict]:
        """Get piece data at given position."""
        return self.chess_logic.get_piece(row, col)
    
    def draw_pawn(self, surface, x, y, color, outline, outline_width=2):
        s = self.square_size
        # Head (circle)
        head_radius = s // 6
        pygame.draw.circle(surface, color, (x, y - s // 6), head_radius)
        pygame.draw.circle(surface, outline, (x, y - s // 6), head_radius, outline_width)
        # Body (rectangle)
        body_width = s // 3
        body_height = s // 3
        pygame.draw.rect(surface, color, (x - body_width // 2, y - body_height // 2, body_width, body_height))
        pygame.draw.rect(surface, outline, (x - body_width // 2, y - body_height // 2, body_width, body_height), outline_width)
        # Base (rectangle)
        base_width = s // 2
        base_height = s // 8
        pygame.draw.rect(surface, color, (x - base_width // 2, y + s // 6, base_width, base_height))
        pygame.draw.rect(surface, outline, (x - base_width // 2, y + s // 6, base_width, base_height), outline_width)

    def draw_rook(self, surface, x, y, color, outline, outline_width=3, battlement_fill=None, flare_color=None):
        """Draw a rook piece."""
        # Body
        body_rect = pygame.Rect(x-16, y-24, 32, 38)
        pygame.draw.rect(surface, color, body_rect)
        pygame.draw.rect(surface, outline, body_rect, outline_width)
        # Top (battlements)
        for dx in [-10, 0, 10]:
            battlement = pygame.Rect(x+dx-5, y-32, 10, 10)
            fill = battlement_fill if battlement_fill is not None else color
            pygame.draw.rect(surface, fill, battlement)
            pygame.draw.rect(surface, outline, battlement, outline_width)
        # Base
        base_rect = pygame.Rect(x-14, y+14, 28, 8)
        pygame.draw.rect(surface, color, base_rect)
        pygame.draw.rect(surface, outline, base_rect, outline_width)
        # Flare lines
        flare = flare_color if flare_color is not None else outline
        pygame.draw.line(surface, flare, (x-12, y+14), (x-16, y+22), outline_width)
        pygame.draw.line(surface, flare, (x+12, y+14), (x+16, y+22), outline_width)

    def draw_knight(self, surface, x, y, color, outline, outline_width=3, eye_color=None):
        """Draw a knight piece."""
        # Knight shape based on reference image (scaled and centered)
        points = [
            (x-18, y+24), (x-12, y-8), (x-8, y-28), (x+2, y-38), (x+16, y-32), (x+20, y-20),
            (x+18, y-10), (x+10, y-2), (x+18, y+10), (x+8, y+18), (x+10, y+24), (x, y+28)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, outline, points, outline_width)
        # Eye
        eye = eye_color if eye_color is not None else outline
        pygame.draw.circle(surface, eye, (x+6, y-18), 3)
        # Base
        pygame.draw.rect(surface, color, (x-12, y+28, 24, 10))
        pygame.draw.rect(surface, outline, (x-12, y+28, 24, 10), outline_width)
        # Flare lines
        pygame.draw.line(surface, outline, (x-8, y+28), (x-14, y+38), outline_width)
        pygame.draw.line(surface, outline, (x+8, y+28), (x+14, y+38), outline_width)

    def draw_bishop(self, surface, x, y, color, outline, outline_width=3, slit_color=None, dot_color=None):
        """Draw a bishop piece."""
        # Body (ellipse)
        pygame.draw.ellipse(surface, color, (x-12, y-24, 24, 36))
        pygame.draw.ellipse(surface, outline, (x-12, y-24, 24, 36), outline_width)
        # Mitre (pointed hat)
        pygame.draw.polygon(surface, color, [(x-10, y-8), (x, y-28), (x+10, y-8)])
        pygame.draw.polygon(surface, outline, [(x-10, y-8), (x, y-28), (x+10, y-8)], outline_width)
        # Dot above mitre
        dot = dot_color if dot_color is not None else outline
        pygame.draw.circle(surface, dot, (x, y-32), 4)
        # Slit (diagonal)
        slit = slit_color if slit_color is not None else outline
        pygame.draw.line(surface, slit, (x-4, y-12), (x+4, y+8), outline_width)
        # Base
        pygame.draw.rect(surface, color, (x-10, y+12, 20, 8))
        pygame.draw.rect(surface, outline, (x-10, y+12, 20, 8), outline_width)
        # Flare lines
        pygame.draw.line(surface, outline, (x-8, y+12), (x-12, y+20), outline_width)
        pygame.draw.line(surface, outline, (x+8, y+12), (x+12, y+20), outline_width)

    def draw_queen(self, surface, x, y, color, outline, outline_width=3, tiara_color=None):
        """Draw a queen piece."""
        # Body (tall oval)
        pygame.draw.ellipse(surface, color, (x-14, y-28, 28, 44))
        pygame.draw.ellipse(surface, outline, (x-14, y-28, 28, 44), outline_width)
        # Tiara (oval with arrow)
        tiara = tiara_color if tiara_color is not None else outline
        # Oval base of tiara
        pygame.draw.ellipse(surface, tiara, (x-8, y-36, 16, 8))
        pygame.draw.ellipse(surface, outline, (x-8, y-36, 16, 8), 1)  # Black outline
        # Arrow pointing upward from oval
        arrow_tip = (x, y-44)
        arrow_base_left = (x-4, y-36)
        arrow_base_right = (x+4, y-36)
        pygame.draw.polygon(surface, tiara, [arrow_tip, arrow_base_left, arrow_base_right])
        # Arrow outline
        pygame.draw.polygon(surface, outline, [arrow_tip, arrow_base_left, arrow_base_right], 1)
        # Base
        pygame.draw.rect(surface, color, (x-12, y+18, 24, 8))
        pygame.draw.rect(surface, outline, (x-12, y+18, 24, 8), outline_width)
        # Flare lines
        pygame.draw.line(surface, outline, (x-10, y+18), (x-14, y+26), outline_width)
        pygame.draw.line(surface, outline, (x+10, y+18), (x+14, y+26), outline_width)

    def draw_king(self, surface, x, y, color, outline, outline_width=3, cross_color=None):
        """Draw a king piece."""
        # Body (tall oval, slightly wider than queen)
        pygame.draw.ellipse(surface, color, (x-16, y-30, 32, 48))
        pygame.draw.ellipse(surface, outline, (x-16, y-30, 32, 48), outline_width)
        # Crown (cross)
        cross = cross_color if cross_color is not None else outline
        # Vertical line of cross
        pygame.draw.line(surface, cross, (x, y-42), (x, y-30), outline_width)
        # Horizontal line of cross
        pygame.draw.line(surface, cross, (x-6, y-36), (x+6, y-36), outline_width)
        # Base
        pygame.draw.rect(surface, color, (x-14, y+20, 28, 8))
        pygame.draw.rect(surface, outline, (x-14, y+20, 28, 8), outline_width)
        # Flare lines
        pygame.draw.line(surface, outline, (x-12, y+20), (x-16, y+28), outline_width)
        pygame.draw.line(surface, outline, (x+12, y+20), (x+16, y+28), outline_width)
        
    def find_king(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.chess_logic.get_piece(row, col)
                if piece and piece['type'] == 'king' and piece['color'] == color:
                    return (row, col)
        return None

    def draw_board(self):
        """Draw the chess board grid and notations inside squares."""
        for row in range(8):
            for col in range(8):
                # Determine square color
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                # Offset for palettes and notations
                x = col * self.square_size + self.palette_width + self.notation_space
                y = row * self.square_size + self.status_bar_height
                pygame.draw.rect(self.screen, color, (x, y, self.square_size, self.square_size))
                # Draw highlights
                if self.selected_piece and (row, col) == self.selected_piece:
                    highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    pygame.draw.rect(highlight_surface, self.highlight_color, (0, 0, self.square_size, self.square_size))
                    self.screen.blit(highlight_surface, (x, y))
                elif (row, col) in self.valid_moves:
                    highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    pygame.draw.rect(highlight_surface, self.valid_move_color, (0, 0, self.square_size, self.square_size))
                    self.screen.blit(highlight_surface, (x, y))
                # Draw rank notation (left side, inside square)
                if col == 0:
                    rank_char = str(8 - row)
                    label = self.small_font.render(rank_char, True, (80, 80, 80))
                    self.screen.blit(label, (x + 2, y + 2))
                # Draw file notation (bottom, inside square)
                if row == 7:
                    file_char = chr(ord('a') + col)
                    label = self.small_font.render(file_char, True, (80, 80, 80))
                    self.screen.blit(label, (x + self.square_size - label.get_width() - 2, y + self.square_size - label.get_height() - 2))
                # Optionally: right and top notations for symmetry
                if col == 7:
                    rank_char = str(8 - row)
                    label = self.small_font.render(rank_char, True, (80, 80, 80))
                    self.screen.blit(label, (x + self.square_size - label.get_width() - 2, y + 2))
                if row == 0:
                    file_char = chr(ord('a') + col)
                    label = self.small_font.render(file_char, True, (80, 80, 80))
                    self.screen.blit(label, (x + 2, y + 2))

    def draw_status_bar(self):
        """Draw the status bar with game information and controls."""
        self._button_rects = {}
        
        # Status bar background (now at the top)
        status_rect = pygame.Rect(0, 0, self.total_width, self.status_bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), status_rect)
        
        # Game status text
        status_text = ""
        status_color = (255, 255, 255)
        
        if self.chess_logic.checkmate:
            winner = "Black" if self.chess_logic.current_player == "white" else "White"
            status_text = f"Checkmate! {winner} wins!"
            status_color = (255, 0, 0)
        elif self.chess_logic.stalemate:
            status_text = "Stalemate! It's a draw!"
            status_color = (255, 165, 0)
        elif self.chess_logic.in_check:
            status_text = f"{self.chess_logic.current_player.capitalize()} is in check!"
            status_color = (255, 255, 0)
        else:
            status_text = f"{self.chess_logic.current_player.capitalize()}'s turn"
            if self.ai_thinking:
                status_text = "AI is thinking..."
                status_color = (0, 255, 255)
        
        # Render status text (at y=8)
        status_surface = self.font.render(status_text, True, status_color)
        self.screen.blit(status_surface, (10, 8))
        
        # Move count (at y=36)
        move_text = f"Move: {self.chess_logic.move_count}"
        move_surface = self.small_font.render(move_text, True, (200, 200, 200))
        self.screen.blit(move_surface, (10, 36))

        # Draw buttons in a row at the bottom of the status bar
        button_y = 52
        button_w = 90
        button_h = 24
        button_gap = 10
        
        # Reset button
        reset_button_rect = pygame.Rect(10, button_y, button_w, button_h)
        pygame.draw.rect(self.screen, (100, 100, 100), reset_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), reset_button_rect, 2)
        reset_text = self.small_font.render("Reset", True, (255, 255, 255))
        self.screen.blit(reset_text, (reset_button_rect.x + 15, reset_button_rect.y + 4))
        self._button_rects['reset'] = reset_button_rect
        # AI Move button
        ai_button_rect = pygame.Rect(10 + button_w + button_gap, button_y, button_w, button_h)
        ai_button_color = (100, 100, 100) if self.ai_thinking or self.setup_mode else (0, 150, 0)
        pygame.draw.rect(self.screen, ai_button_color, ai_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), ai_button_rect, 2)
        ai_text = self.small_font.render("AI Move", True, (255, 255, 255))
        self.screen.blit(ai_text, (ai_button_rect.x + 10, ai_button_rect.y + 4))
        self._button_rects['ai'] = ai_button_rect
        # Undo button
        undo_button_rect = pygame.Rect(10 + 2 * (button_w + button_gap), button_y, button_w, button_h)
        pygame.draw.rect(self.screen, (100, 100, 100), undo_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), undo_button_rect, 2)
        undo_surface = self.small_font.render("Undo", True, (255, 255, 255))
        self.screen.blit(undo_surface, (undo_button_rect.x + 10, undo_button_rect.y + 4))
        self._button_rects['undo'] = undo_button_rect
        # Redo button
        redo_button_rect = pygame.Rect(10 + 3 * (button_w + button_gap), button_y, button_w, button_h)
        pygame.draw.rect(self.screen, (100, 100, 100), redo_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), redo_button_rect, 2)
        redo_surface = self.small_font.render("Redo", True, (255, 255, 255))
        self.screen.blit(redo_surface, (redo_button_rect.x + 10, redo_button_rect.y + 4))
        self._button_rects['redo'] = redo_button_rect
        # Setup button
        setup_button_rect = pygame.Rect(10 + 4 * (button_w + button_gap), button_y, button_w, button_h)
        setup_button_color = (255, 165, 0) if self.setup_mode else (100, 100, 100)
        pygame.draw.rect(self.screen, setup_button_color, setup_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), setup_button_rect, 2)
        setup_text = self.small_font.render("Setup", True, (255, 255, 255))
        self.screen.blit(setup_text, (setup_button_rect.x + 10, setup_button_rect.y + 4))
        self._button_rects['setup'] = setup_button_rect
        # Add OCR icon buttons above Setup and Redo buttons, side by side
        ocr_button_w = 36
        ocr_button_h = 36
        ocr_button_gap = 10
        # Place above Setup and Redo buttons
        setup_x = 10 + 4 * (button_w + button_gap)
        redo_x = 10 + 3 * (button_w + button_gap)
        ocr_y = button_y - ocr_button_h - ocr_button_gap
        # Upload icon button (above Setup)
        '''if setup_button_rect:
            upload_button_rect = pygame.Rect(
                setup_button_rect.x,
                setup_button_rect.y - setup_button_rect.height - 10,  # 10 pixels above setup
                setup_button_rect.width,
                setup_button_rect.height
            )
            self._button_rects['upload_image'] = upload_button_rect
            pygame.draw.rect(self.screen, (70, 130, 180), upload_button_rect, border_radius=8)  # Blue
            pygame.draw.rect(self.screen, (200, 200, 200), upload_button_rect, 2, border_radius=8)  # White border
            # Draw upload icon (arrow up into tray)
            center_x = upload_button_rect.x + upload_button_rect.width // 2
            center_y = upload_button_rect.y + upload_button_rect.height // 2
            # Tray
            pygame.draw.rect(self.screen, (255,255,255), (center_x-10, center_y+6, 20, 6), border_radius=3)
            # Arrow
            pygame.draw.polygon(self.screen, (255,255,255), [
                (center_x, center_y-10), (center_x-8, center_y), (center_x-4, center_y), (center_x-4, center_y+4),
                (center_x+4, center_y+4), (center_x+4, center_y), (center_x+8, center_y)
            ])'''
        # Setup mode: radio buttons for player selection and Play button
        if self.setup_mode:
            clear_button_rect = pygame.Rect(10 + 5 * (button_w + button_gap), button_y, button_w, button_h)
            pygame.draw.rect(self.screen, (200, 50, 50), clear_button_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), clear_button_rect, 2)
            clear_text = self.small_font.render("Clear", True, (255, 255, 255))
            self.screen.blit(clear_text, (clear_button_rect.x + 10, clear_button_rect.y + 4))
            self._button_rects['clear'] = clear_button_rect
            # --- Radio buttons and Play button layout ---
            play_button_w = 60  # Reduced width
            play_button_x = self.total_width - play_button_w - 20
            button_h = 24
            button_y = 52
            radio_gap = 40  # Closer together
            radio_radius = 12
            # Black radio to the left of Play, White to the left of Black
            black_radio_center = (play_button_x - 2*radio_gap, button_y + button_h // 2)
            white_radio_center = (play_button_x - 3*radio_gap, button_y + button_h // 2)
            # White radio
            pygame.draw.circle(self.screen, (255,255,255), white_radio_center, radio_radius, 2)
            if getattr(self, 'setup_selected_player', 'white') == 'white':
                pygame.draw.circle(self.screen, (255,255,255), white_radio_center, radio_radius-4)
            self._button_rects['radio_white'] = pygame.Rect(
                white_radio_center[0] - radio_radius, button_y, 2*radio_radius, button_h
            )
            # Black radio
            pygame.draw.circle(self.screen, (0,0,0), black_radio_center, radio_radius, 2)
            if getattr(self, 'setup_selected_player', 'white') == 'black':
                pygame.draw.circle(self.screen, (0,0,0), black_radio_center, radio_radius-4)
            self._button_rects['radio_black'] = pygame.Rect(
                black_radio_center[0] - radio_radius, button_y, 2*radio_radius, button_h
            )
            # Play button
            play_button_rect = pygame.Rect(play_button_x, button_y, play_button_w, button_h)
            pygame.draw.rect(self.screen, (0, 150, 0), play_button_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), play_button_rect, 2)
            play_text = self.small_font.render("Play", True, (255, 255, 255))
            self.screen.blit(play_text, (play_button_rect.x + 8, play_button_rect.y + 4))
            self._button_rects['play'] = play_button_rect
        else:
            # Remove from button rects if not in setup mode
            if 'toggle_player' in self._button_rects:
                del self._button_rects['toggle_player']

        # After drawing all buttons, display the last Stockfish/AI move below the buttons
        if getattr(self, 'last_ai_move', None):
            ai_text = f"Last AI move: {self.last_ai_move}"
            ai_surface = self.small_font.render(ai_text, True, (0, 255, 255))  # Bright cyan
            self.screen.blit(ai_surface, (10, button_y + button_h + 8))

        # Add status message if it exists
        if hasattr(self, 'status_message') and self.status_message:
            status_text = self.status_message
            status_surface = self.font.render(status_text, True, (255, 0, 0))
            self.screen.blit(status_surface, (20, self.total_height - self.status_bar_height + 10))

        # Place above Setup and Redo buttons
        if setup_button_rect:
            upload_button_rect = pygame.Rect(
                setup_button_rect.x,
                setup_button_rect.y - ocr_button_h - ocr_button_gap,  # above setup
                ocr_button_w,
                ocr_button_h
            )
            self._button_rects['upload_image'] = upload_button_rect
            pygame.draw.rect(self.screen, (70, 130, 180), upload_button_rect, border_radius=8)  # Blue
            pygame.draw.rect(self.screen, (200, 200, 200), upload_button_rect, 2, border_radius=8)  # White border
            # Draw upload icon (arrow up into tray)
            center_x = upload_button_rect.x + ocr_button_w // 2
            center_y = upload_button_rect.y + ocr_button_h // 2
            # Tray
            pygame.draw.rect(self.screen, (255,255,255), (center_x-10, center_y+6, 20, 6), border_radius=3)
            # Arrow
            pygame.draw.polygon(self.screen, (255,255,255), [
                (center_x, center_y-10), (center_x-8, center_y), (center_x-4, center_y), (center_x-4, center_y+4),
                (center_x+4, center_y+4), (center_x+4, center_y), (center_x+8, center_y)
            ])
        if redo_button_rect:
            capture_button_rect = pygame.Rect(
                redo_button_rect.x,
                redo_button_rect.y - ocr_button_h - ocr_button_gap,  # above redo
                ocr_button_w,
                ocr_button_h
            )
            self._button_rects['capture_image'] = capture_button_rect
            pygame.draw.rect(self.screen, (34, 139, 34), capture_button_rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 200, 200), capture_button_rect, 2, border_radius=8)
            # Draw camera icon
            cam_cx = capture_button_rect.x + ocr_button_w // 2
            cam_cy = capture_button_rect.y + ocr_button_h // 2
            # Camera body
            pygame.draw.rect(self.screen, (255,255,255), (cam_cx-10, cam_cy-6, 20, 12), border_radius=4)
            # Lens
            pygame.draw.circle(self.screen, (70,130,180), (cam_cx, cam_cy), 5)
            pygame.draw.circle(self.screen, (255,255,255), (cam_cx, cam_cy), 3)
            # Top bar
            pygame.draw.rect(self.screen, (255,255,255), (cam_cx-6, cam_cy-10, 12, 4), border_radius=2)

    def draw_piece(self, piece_data: Dict, row: int, col: int):
        """Draw a chess piece using custom vector graphics."""
        # Add palette and notation offsets to x
        x = col * self.square_size + self.palette_width + self.notation_space + self.square_size // 2
        y = row * self.square_size + self.status_bar_height + self.square_size // 2
        
        # Set colors based on piece color
        if piece_data['color'] == 'white':
            color = (255, 255, 255)
            outline = (0, 0, 0)
            outline_width = 3
        else:  # black
            color = (0, 0, 0)
            outline = (255, 255, 255)
            outline_width = 2
        
        # Draw the appropriate piece
        if piece_data['type'] == 'pawn':
            self.draw_pawn(self.screen, x, y, color, outline, outline_width)
        elif piece_data['type'] == 'rook':
            self.draw_rook(self.screen, x, y, color, outline, outline_width)
        elif piece_data['type'] == 'knight':
            self.draw_knight(self.screen, x, y, color, outline, outline_width)
        elif piece_data['type'] == 'bishop':
            self.draw_bishop(self.screen, x, y, color, outline, outline_width)
        elif piece_data['type'] == 'queen':
            tiara_color = (255, 255, 255) if piece_data['color'] == 'white' else (0, 0, 0)
            self.draw_queen(self.screen, x, y, color, outline, outline_width, tiara_color)
        elif piece_data['type'] == 'king':
            cross_color = (0, 0, 0)  # Black cross for both colors
            self.draw_king(self.screen, x, y, color, outline, outline_width, cross_color)
    
    def draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(8):
            for col in range(8):
                piece_data = self.chess_logic.get_piece(row, col)
                if piece_data is not None:
                    self.draw_piece(piece_data, row, col)
    
    def get_square_from_pos(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        x, y = pos
        board_left = self.palette_width + self.notation_space
        board_top = self.status_bar_height
        board_right = board_left + self.square_size * 8
        board_bottom = board_top + self.square_size * 8

        if not (board_left <= x < board_right and board_top <= y < board_bottom):
            return -1, -1  # Not on the board

        col = (x - board_left) // self.square_size
        row = (y - board_top) // self.square_size

        # Final check: must be in 0..7
        if not (0 <= row < 8 and 0 <= col < 8):
            return -1, -1

        return int(row), int(col)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if board position is valid."""
        return 0 <= row < 8 and 0 <= col < 8
    
    def show_promotion_menu(self, color, square):
        """Show the promotion menu overlay at the given square."""
        print(f"Showing promotion menu for {color} pieces at square {square}")
        self.promotion_rects = []
        menu_width = self.square_size * 4
        menu_height = self.square_size
        
        # Position menu in the center of the screen
        x = (self.total_width - menu_width) // 2
        y = (self.total_height - menu_height) // 2
        
        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.total_width, self.total_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Dark overlay
        self.screen.blit(overlay, (0, 0))
        
        # Create menu surface
        menu_surface = pygame.Surface((menu_width, menu_height))
        menu_surface.fill((220, 220, 220))
        pygame.draw.rect(menu_surface, (100, 100, 100), (0, 0, menu_width, menu_height), 3)
        
        for i, piece_type in enumerate(self.promotion_choices):
            px = i * self.square_size
            rect = pygame.Rect(px, 0, self.square_size, self.square_size)
            self.promotion_rects.append(rect.move(x, y))
            
            # Draw piece
            cx = px + self.square_size // 2
            cy = menu_height // 2
            
            if piece_type == 'queen':
                tiara_color = (255, 255, 255) if color == 'white' else (0, 0, 0)
                self.draw_queen(menu_surface, cx, cy, (255,255,255) if color=='white' else (0,0,0), (0,0,0) if color=='white' else (255,255,255), 3 if color=='white' else 2, tiara_color)
            elif piece_type == 'rook':
                self.draw_rook(menu_surface, cx, cy, (255,255,255) if color=='white' else (0,0,0), (0,0,0) if color=='white' else (255,255,255), 3 if color=='white' else 2)
            elif piece_type == 'bishop':
                self.draw_bishop(menu_surface, cx, cy, (255,255,255) if color=='white' else (0,0,0), (0,0,0) if color=='white' else (255,255,255), 3 if color=='white' else 2)
            elif piece_type == 'knight':
                self.draw_knight(menu_surface, cx, cy, (255,255,255) if color=='white' else (0,0,0), (0,0,0) if color=='white' else (255,255,255), 3 if color=='white' else 2)
        
        self.screen.blit(menu_surface, (x, y))
        print(f"Promotion menu drawn at ({x}, {y}) with {len(self.promotion_rects)} options")

    def handle_click(self, pos: Tuple[int, int], button: int = 1):
        # Handle right-click in setup mode
        if button == 3 and self.setup_mode:
            if self.selected_setup_piece:
                self.selected_setup_piece = None
                print("Deselected setup piece")
            return
        # Use the new button rects for click detection
        button_rects = getattr(self, '_button_rects', None)
        if button_rects is None:
            # Fallback: draw_status_bar hasn't been called yet, so use old logic
            button_y = 52
            button_w = 90
            button_h = 24
            button_gap = 10
            button_rects = {
                'reset': pygame.Rect(10, button_y, button_w, button_h),
                'ai': pygame.Rect(10 + button_w + button_gap, button_y, button_w, button_h),
                'undo': pygame.Rect(10 + 2 * (button_w + button_gap), button_y, button_w, button_h),
                'redo': pygame.Rect(10 + 3 * (button_w + button_gap), button_y, button_w, button_h),
            }
        # Use .get() for all button checks
        if button_rects.get('reset') and button_rects['reset'].collidepoint(pos):
            self.chess_logic.reset_game()
            self.selected_piece = None
            self.valid_moves = []
            self.promotion_pending = None
            self.promotion_color = None
            self.promotion_square = None
            self.promotion_rects = []
            self.ai_thinking = False
            self.chess_logic.init_stockfish()
            return
        if button_rects.get('ai') and button_rects['ai'].collidepoint(pos):
            if not self.ai_thinking:
                self.ai_thinking = True
                def ai_move_thread():
                    try:
                        ai_move = self.chess_logic.get_stockfish_best_move(time_ms=2000)
                        if ai_move:
                            self.last_ai_move = ai_move  # Store for display
                            coords = self.chess_logic.convert_uci_to_coordinates(ai_move)
                            promotion_piece = None
                            if len(ai_move) == 5:
                                promo_letter = ai_move[4].lower()
                                promo_map = {'q': 'queen', 'r': 'rook', 'b': 'bishop', 'n': 'knight'}
                                promotion_piece = promo_map.get(promo_letter)
                                print(f"Stockfish suggests promotion to {promotion_piece} for move {ai_move}")
                            if coords:
                                from_row, from_col, to_row, to_col = coords
                                print(f"AI move: {ai_move}, from {from_row},{from_col} to {to_row},{to_col}, promotion: {promotion_piece}")
                                # If this is a promotion move, show the promotion menu and auto-select the piece
                                if promotion_piece and self.chess_logic.get_piece(from_row, from_col)['type'] == 'pawn' and (
                                    (self.chess_logic.get_piece(from_row, from_col)['color'] == 'white' and to_row == 0) or
                                    (self.chess_logic.get_piece(from_row, from_col)['color'] == 'black' and to_row == 7)
                                ):
                                    # Set up promotion menu state
                                    self.promotion_pending = (from_row, from_col, to_row, to_col)
                                    self.promotion_color = self.chess_logic.get_piece(from_row, from_col)['color']
                                    self.promotion_square = (to_row, to_col)
                                    # Show the promotion menu visually
                                    self.show_promotion_menu(self.promotion_color, self.promotion_square)
                                    pygame.display.flip()
                                    # Process events and wait for 0.5 seconds, so the menu is visible
                                    import time
                                    start = time.time()
                                    while time.time() - start < 0.5:
                                        for event in pygame.event.get():
                                            if event.type == pygame.QUIT:
                                                pygame.quit()
                                                return
                                        pygame.display.flip()
                                        time.sleep(0.01)
                                    # Auto-select the correct promotion piece
                                    try:
                                        i = self.promotion_choices.index(promotion_piece)
                                        self.chess_logic.make_move(from_row, from_col, to_row, to_col, promotion_piece)
                                        self.promotion_pending = None
                                        self.promotion_color = None
                                        self.promotion_square = None
                                        self.promotion_rects = []
                                    except Exception as e:
                                        print(f"Auto-promotion error: {e}")
                                else:
                                    self.chess_logic.make_move(from_row, from_col, to_row, to_col, promotion_piece)
                    except Exception as e:
                        print(f"AI move error: {e}")
                    finally:
                        self.ai_thinking = False
                ai_thread = threading.Thread(target=ai_move_thread)
                ai_thread.daemon = True
                ai_thread.start()
            return
        if button_rects.get('undo') and button_rects['undo'].collidepoint(pos):
            if self.chess_logic.can_undo():
                self.chess_logic.undo_move()
                self.selected_piece = None
                self.valid_moves = []
                self.promotion_pending = None
            return
        if button_rects.get('redo') and button_rects['redo'].collidepoint(pos):
            if self.chess_logic.can_redo():
                self.chess_logic.redo_move()
                self.selected_piece = None
                self.valid_moves = []
                self.promotion_pending = None
            return
        if button_rects.get('setup') and button_rects['setup'].collidepoint(pos):
            # Toggle setup mode
            self.setup_mode = not self.setup_mode
            if self.setup_mode:
                print("Setup mode enabled")
                # Clear game state when entering setup mode
                self.selected_piece = None
                self.valid_moves = []
                self.promotion_pending = None
                self.promotion_color = None
                self.promotion_square = None
                self.promotion_rects = []
                self.selected_setup_piece = None
                self.chess_logic.clear_board()
            else:
                print("Setup mode disabled")
                # Clear setup state when exiting setup mode
                self.selected_setup_piece = None
                self.piece_palette_rects = {}
            self.chess_logic.init_stockfish()
            return
        if button_rects.get('clear') and button_rects['clear'].collidepoint(pos):
            self.chess_logic.clear_board()
            self.selected_piece = None
            self.valid_moves = []
            self.promotion_pending = None
            self.promotion_color = None
            self.promotion_square = None
            self.promotion_rects = []
            self.selected_setup_piece = None
            return
        if button_rects.get('toggle_player') and button_rects['toggle_player'].collidepoint(pos):
            # Toggle the player to move
            if self.chess_logic.current_player == "white":
                self.chess_logic.current_player = "black"
            else:
                self.chess_logic.current_player = "white"
            return
        if button_rects.get('capture_image') and button_rects['capture_image'].collidepoint(pos):
            # Capture image from camera with click, retake, and continue buttons
            

            def capture_image():
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
                # Try to set the mouse pointer to arrow (default)
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
                        # Window might have been destroyed
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

                            # Before calling detect_board_and_extract_squares, set a default status message
                            self.status_message = ""
                            try:
                                detect_board_and_extract_squares(
                                    'board.jpg',
                                    'extracted_squares',
                                    square_size=64,  # Match your model's input size
                                    pattern_size=(7, 7),
                                    crop_percent=0.03
                                )
                            except Exception as e:
                                self.status_message = "Chessboard not found in the image. Please try again."
                                print(self.status_message)
                                return

                            # Extract squares from the accepted board image
                            board_state = []
                            for row in range(8):
                                row_state = []
                                for col in range(8):
                                    square_path = f"extracted_squares/square_{row}_{col}.png"
                                    piece, confidence = self.predict_piece(square_path)
                                    row_state.append(piece)
                                    print(f"Square {row},{col}: {piece} (confidence: {confidence:.2f})")
                                board_state.append(row_state)
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

            threading.Thread(target=capture_image).start()
            return
        if button_rects.get('upload_image') and button_rects['upload_image'].collidepoint(pos):
            pygame.display.iconify()
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select Chessboard Image",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
            )
            root.destroy()
            pygame.display.set_mode((self.total_width, self.total_height))
            if file_path:
                shutil.copy(file_path, 'board.jpg')
                print("Saved uploaded image as board.jpg")
                self.status_message = ""
                def process_uploaded_image():
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
                threading.Thread(target=process_uploaded_image).start()
            return
        # Don't handle board clicks if AI is thinking
        if self.ai_thinking:
            return
        
        # Handle piece palette clicks in setup mode
        if self.setup_mode:
            # Prevent Stockfish/AI Move in setup mode
            if self._button_rects.get('ai') and self._button_rects['ai'].collidepoint(pos):
                print("AI Move is disabled in setup mode.")
                return
            # Radio button selection
            if self._button_rects.get('radio_white') and self._button_rects['radio_white'].collidepoint(pos):
                if getattr(self, 'setup_selected_player', 'white') == 'white':
                    self.setup_selected_player = None  # Deselect if already selected
                else:
                    self.setup_selected_player = 'white'
                return
            if self._button_rects.get('radio_black') and self._button_rects['radio_black'].collidepoint(pos):
                if getattr(self, 'setup_selected_player', 'white') == 'black':
                    self.setup_selected_player = None
                else:
                    self.setup_selected_player = 'black'
                return
            # Play button
            if self._button_rects.get('play') and self._button_rects['play'].collidepoint(pos):
                if getattr(self, 'setup_selected_player', None) in ('white', 'black'):
                    self.chess_logic.current_player = self.setup_selected_player
                    self.setup_mode = False
                    self.selected_setup_piece = None
                    self.piece_palette_rects = {}
                    self.chess_logic.init_stockfish()
                return
            # Palette piece selection (toggle)
            for (piece_type, color), rect in self.piece_palette_rects.items():
                if rect.collidepoint(pos):
                    if self.selected_setup_piece == (piece_type, color):
                        self.selected_setup_piece = None  # Deselect if already selected
                    else:
                        self.selected_setup_piece = (piece_type, color)
                    print(f"Selected {self.selected_setup_piece} for placement")
                    return
            # Board clicks for placing/removing pieces
            row, col = self.get_square_from_pos(pos)
            if row == -1 or col == -1 or not self.is_valid_position(row, col):
                return
            if self.selected_setup_piece:
                piece_type, color = self.selected_setup_piece
                self.chess_logic.board[row][col] = {
                    'type': piece_type,
                    'color': color,
                    'has_moved': False
                }
                print(f"Placed {color} {piece_type} at ({row}, {col})")
            else:
                if self.chess_logic.get_piece(row, col):
                    self.chess_logic.board[row][col] = None
                    print(f"Removed piece at ({row}, {col})")
            return
        
        # Handle promotion menu clicks
        if self.promotion_pending:
            for i, rect in enumerate(self.promotion_rects):
                if rect.collidepoint(pos):
                    piece_type = self.promotion_choices[i]
                    from_row, from_col, to_row, to_col = self.promotion_pending
                    
                    # Make the promotion move
                    self.chess_logic.make_move(from_row, from_col, to_row, to_col, piece_type)
                    
                    # Clear promotion state
                    self.promotion_pending = None
                    self.promotion_color = None
                    self.promotion_square = None
                    self.promotion_rects = []
                    return
        
        # Handle board clicks
        row, col = self.get_square_from_pos(pos)
        if row == -1 or col == -1 or not self.is_valid_position(row, col):
            return
        # Prevent board moves after checkmate
        if self.chess_logic.checkmate:
            return
        
        # Now it's safe to use row and col!
        # Handle setup mode board clicks
        if self.setup_mode:
            # Radio button selection
            if self._button_rects.get('radio_white') and self._button_rects['radio_white'].collidepoint(pos):
                self.setup_selected_player = 'white'
                return
            if self._button_rects.get('radio_black') and self._button_rects['radio_black'].collidepoint(pos):
                self.setup_selected_player = 'black'
                return
            # Play button
            if self._button_rects.get('play') and self._button_rects['play'].collidepoint(pos):
                self.chess_logic.current_player = getattr(self, 'setup_selected_player', 'white')
                self.setup_mode = False
                self.selected_setup_piece = None
                self.piece_palette_rects = {}
                self.chess_logic.init_stockfish()
                return
            if self.selected_setup_piece:
                piece_type, color = self.selected_setup_piece
                # Place the selected piece on the board
                self.chess_logic.board[row][col] = {
                    'type': piece_type,
                    'color': color,
                    'has_moved': False
                }
                print(f"Placed {color} {piece_type} at ({row}, {col})")
                # Keep the piece selected for multiple placements
            else:
                # Remove piece if clicking on an occupied square without a selected piece
                if self.chess_logic.get_piece(row, col):
                    self.chess_logic.board[row][col] = None
                    print(f"Removed piece at ({row}, {col})")
            return
        
        # Handle normal game mode board clicks
        # If a piece is already selected, try to move it
        if self.selected_piece:
            from_row, from_col = self.selected_piece
            if (row, col) in self.valid_moves:
                # Check for auto-promotion from Stockfish move
                piece = self.chess_logic.get_piece(from_row, from_col)
                if piece and piece['type'] == 'pawn':
                    if (piece['color'] == 'white' and row == 0) or (piece['color'] == 'black' and row == 7):
                        # Check for auto-promotion from Stockfish move
                        if self.last_ai_move:
                            coords = self.chess_logic.convert_uci_to_coordinates(self.last_ai_move)
                            if coords == (from_row, from_col, row, col) and len(self.last_ai_move) == 5:
                                promo_letter = self.last_ai_move[4]
                                promo_map = {
                                    'q': 'queen', 'r': 'rook', 'b': 'bishop', 'n': 'knight',
                                    'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'
                                }
                                promotion_piece = promo_map.get(promo_letter)
                                if promotion_piece:
                                    self.chess_logic.make_move(from_row, from_col, row, col, promotion_piece)
                                    # Clear selection
                                    self.selected_piece = None
                                    self.valid_moves = []
                                    return
                        # Otherwise, show the promotion menu as usual
                        self.promotion_pending = (from_row, from_col, row, col)
                        self.promotion_color = piece['color']
                        self.promotion_square = (row, col)
                        self.show_promotion_menu(piece['color'], (row, col))
                        return
                
                # Make the move
                self.chess_logic.make_move(from_row, from_col, row, col)
                
                # Clear selection
                self.selected_piece = None
                self.valid_moves = []
            else:
                # Select a different piece
                piece = self.chess_logic.get_piece(row, col)
                if piece and piece['color'] == self.chess_logic.current_player:
                    self.selected_piece = (row, col)
                    self.valid_moves = self.chess_logic.get_valid_moves(row, col)
                else:
                    self.selected_piece = None
                    self.valid_moves = []
        else:
            # Select a piece
            piece = self.chess_logic.get_piece(row, col)
            if piece and piece['color'] == self.chess_logic.current_player:
                self.selected_piece = (row, col)
                self.valid_moves = self.chess_logic.get_valid_moves(row, col)
    
    def draw_piece_palette(self):
        """Draw the piece palette for setup mode on the sides of the board, centered in their squares."""
        if not self.setup_mode:
            return
        piece_types = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
        piece_size = self.square_size
        board_top = self.status_bar_height

        # Black pieces on the left
        for i, piece_type in enumerate(piece_types):
            x = 0
            y = board_top + i * piece_size
            piece_rect = pygame.Rect(x, y, piece_size, piece_size)
            # Center the piece in the palette square
            center_x = x + piece_size // 2
            center_y = y + piece_size // 2
            if self.selected_setup_piece == (piece_type, 'black'):
                pygame.draw.rect(self.screen, (255, 255, 0), piece_rect)
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), piece_rect)
            pygame.draw.rect(self.screen, (50, 50, 50), piece_rect, 2)
            self.draw_piece_in_palette(piece_type, 'black', center_x, center_y)
            self.piece_palette_rects[(piece_type, 'black')] = piece_rect

        # White pieces on the right
        right_x = self.palette_width + self.board_pixel_size + self.notation_space
        for i, piece_type in enumerate(piece_types):
            x = right_x
            y = board_top + i * piece_size
            piece_rect = pygame.Rect(x, y, piece_size, piece_size)
            center_x = x + piece_size // 2
            center_y = y + piece_size // 2
            if self.selected_setup_piece == (piece_type, 'white'):
                pygame.draw.rect(self.screen, (255, 255, 0), piece_rect)
            else:
                pygame.draw.rect(self.screen, (200, 200, 200), piece_rect)
            pygame.draw.rect(self.screen, (50, 50, 50), piece_rect, 2)
            self.draw_piece_in_palette(piece_type, 'white', center_x, center_y)
            self.piece_palette_rects[(piece_type, 'white')] = piece_rect
    
    def draw_piece_in_palette(self, piece_type: str, color: str, x: int, y: int):
        """Draw a piece in the palette at the specified position."""
        piece_color = (255, 255, 255) if color == 'white' else (0, 0, 0)
        outline_color = (0, 0, 0) if color == 'white' else (255, 255, 255)
        
        if piece_type == 'pawn':
            self.draw_pawn(self.screen, x, y, piece_color, outline_color, 2)
        elif piece_type == 'rook':
            self.draw_rook(self.screen, x, y, piece_color, outline_color, 2)
        elif piece_type == 'knight':
            self.draw_knight(self.screen, x, y, piece_color, outline_color, 2)
        elif piece_type == 'bishop':
            self.draw_bishop(self.screen, x, y, piece_color, outline_color, 2)
        elif piece_type == 'queen':
            self.draw_queen(self.screen, x, y, piece_color, outline_color, 2)
        elif piece_type == 'king':
            self.draw_king(self.screen, x, y, piece_color, outline_color, 2)

    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()
        
        print("Starting chess GUI...")
        print(f"Window dimensions: {self.total_width}x{self.total_height}")
        
        self.screen.fill((0, 0, 0))
        self.draw_status_bar()
        self.draw_board()
        self.draw_pieces()
        pygame.display.flip()
        
        print("Initial drawing complete - you should see:")
        print(f"  - Chess board in top {self.board_pixel_size}x{self.board_pixel_size} area")
        print(f"  - Status bar in bottom {self.total_width}x{self.status_bar_height} area")
        print("  - Buttons: Reset, AI Move, Undo, Redo")

        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_click(event.pos)
                    elif event.type == pygame.KEYDOWN:
                        # Handle keyboard shortcuts
                        if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.chess_logic.can_undo():
                                self.chess_logic.undo_move()
                                self.selected_piece = None
                                self.valid_moves = []
                        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.chess_logic.can_redo():
                                self.chess_logic.redo_move()
                                self.selected_piece = None
                                self.valid_moves = []

                self.screen.fill((0, 0, 0))
                self.draw_status_bar()
                self.draw_board()
                self.draw_pieces()
                self.draw_piece_palette()
                if self.promotion_pending:
                    self.show_promotion_menu(self.promotion_color, self.promotion_square)
                pygame.display.flip()
                clock.tick(60)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\n[ERROR] Exception occurred: {e}")
            input("\nPress Enter to exit...")
        pygame.quit()

if __name__ == "__main__":
    # Create and run the chess GUI
    chess_gui = ChessGUI()
    chess_gui.run() 