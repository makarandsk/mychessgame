import cv2
import numpy as np
import os

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def draw_grid(image, color=(0,255,0), thickness=1):
    h, w = image.shape[:2]
    step = w // 8
    for i in range(1, 8):
        x = i * step
        cv2.line(image, (x, 0), (x, h), color, thickness)
        cv2.line(image, (0, x), (w, x), color, thickness)
    return image

def crop_border(image, percent=0.07):
    h, w = image.shape[:2]
    crop_h = int(h * percent)
    crop_w = int(w * percent)
    cropped = image[crop_h:h-crop_h, crop_w:w-crop_w]
    return cropped

def detect_board_and_extract_squares(image_path, output_dir, square_size=96, pattern_size=(7,7), crop_percent=0.03):
    os.makedirs(output_dir, exist_ok=True)
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image: {image_path}")
        return
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
        # Color-based mask for digital boards (tune for your board colors)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
        cv2.imwrite('color_mask.png', mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        board_contour = None
        max_area = 0
        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.8 < aspect_ratio < 1.2 and area > (image.shape[0] * image.shape[1]) * 0.1:
                    if area > max_area:
                        max_area = area
                        board_contour = approx
        if board_contour is None:
            print("Chessboard not found! Check color_mask.png for debugging.")
            return
        debug_board = orig.copy()
        cv2.drawContours(debug_board, [board_contour], -1, (0,255,0), 3)
        cv2.imwrite('detected_board_contour.png', debug_board)
        board_pts = board_contour.reshape(4, 2)
    # Perspective transform and upscaling
    warped = four_point_transform(orig, board_pts)
    board_size = min(warped.shape[:2])
    warped = cv2.resize(warped, (board_size, board_size))
    target_board_size = 1024
    warped = cv2.resize(warped, (target_board_size, target_board_size), interpolation=cv2.INTER_LANCZOS4)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    warped = cv2.filter2D(warped, -1, kernel)
    warped = crop_border(warped, percent=crop_percent)
    cv2.imwrite('warped_board_cropped.png', warped)
    warped_with_grid = warped.copy()
    warped_with_grid = draw_grid(warped_with_grid)
    cv2.imwrite('warped_with_grid.png', warped_with_grid)
    # Extract squares
    step = warped.shape[0] // 8
    h, w = warped.shape[:2]
    for row in range(8):
        for col in range(8):
            y1 = row * step
            y2 = (row + 1) * step if row < 7 else h
            x1 = col * step
            x2 = (col + 1) * step if col < 7 else w
            square = warped[y1:y2, x1:x2]
            if square.size == 0:
                print(f"Warning: Empty square at {row},{col}, skipping.")
                continue
            square = cv2.resize(square, (square_size, square_size))
            fname = f"square_{row}_{col}.png"
            cv2.imwrite(os.path.join(output_dir, fname), square)
    print(f"Extracted 64 squares to {output_dir}")
    print("Debug images saved: chessboard_corners.png, color_mask.png, detected_board_contour.png, warped_board_cropped.png, warped_with_grid.png")

if __name__ == "__main__":
    detect_board_and_extract_squares('board.jpg', 'extracted_squares', square_size=96, pattern_size=(7,7), crop_percent=0.03)