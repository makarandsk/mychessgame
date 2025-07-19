import pygame

# --- Piece Drawing Functions ---
def draw_pawn(surface, x, y, color, outline, outline_width=2):
    # Head (perfect circle)
    pygame.draw.circle(surface, color, (x, y-18), 12)
    pygame.draw.circle(surface, outline, (x, y-18), 12, outline_width)
    # Body (ellipse)
    pygame.draw.ellipse(surface, color, (x-10, y-10, 20, 22))
    pygame.draw.ellipse(surface, outline, (x-10, y-10, 20, 22), outline_width)
    # Base (flared rectangle)
    pygame.draw.rect(surface, color, (x-14, y+10, 28, 8))
    pygame.draw.rect(surface, outline, (x-14, y+10, 28, 8), outline_width)
    # Flare lines
    pygame.draw.line(surface, outline, (x-10, y+10), (x-14, y+18), outline_width)
    pygame.draw.line(surface, outline, (x+10, y+10), (x+14, y+18), outline_width)

def draw_rook(surface, x, y, color, outline, outline_width=3, battlement_fill=None, flare_color=None):
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

def draw_knight(surface, x, y, color, outline, outline_width=3, eye_color=None):
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

def draw_bishop(surface, x, y, color, outline, outline_width=3, slit_color=None, dot_color=None):
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

def draw_queen(surface, x, y, color, outline, outline_width=3, tiara_color=None):
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

def draw_king(surface, x, y, color, outline, outline_width=3, cross_color=None):
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

# --- Main Demo ---
def main():
    pygame.init()
    num_pieces = 8
    spacing = 90
    margin = 40
    width = margin * 2 + spacing * (num_pieces - 1)
    height = 360
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Queen and King Style Demo")
    screen.fill((220, 220, 220))

    black = (0, 0, 0)
    white = (255, 255, 255)

    # Draw white queens (white fill, black outline, white tiara with black outline)
    for i in range(num_pieces):
        draw_queen(screen, margin + i*spacing, 80, white, black, outline_width=3, tiara_color=white)
    # Draw black queens (solid black, white outline, black tiara)
    for i in range(num_pieces):
        draw_queen(screen, margin + i*spacing, 170, black, white, outline_width=2, tiara_color=black)
    # Draw white kings (white fill, black outline, black cross)
    for i in range(num_pieces):
        draw_king(screen, margin + i*spacing, 260, white, black, outline_width=3, cross_color=black)
    # Draw black kings (solid black, white outline, black cross)
    for i in range(num_pieces):
        draw_king(screen, margin + i*spacing, 350, black, white, outline_width=2, cross_color=black)

    pygame.display.flip()
    print("Close the window to exit.")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    pygame.quit()

if __name__ == "__main__":
    main() 