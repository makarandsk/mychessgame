#!/usr/bin/env python3
"""
Debug script for board detection issues.
This will help you understand why the board detection is failing and provide manual selection.
"""

import cv2
import numpy as np
import os
import sys

def debug_board_detection(image_path: str):
    """Debug board detection with multiple methods."""
    print("=" * 60)
    print("BOARD DETECTION DEBUG")
    print("=" * 60)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not read image: {image_path}")
        return
    
    print(f"✅ Image loaded: {image.shape}")
    
    # Method 1: OpenCV chessboard corners
    print("\n1. Testing OpenCV chessboard corner detection...")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(gray, (7, 7))
    
    if found:
        print("✅ OpenCV corners found!")
        cv2.drawChessboardCorners(image, (7, 7), corners, found)
        cv2.imwrite('debug_opencv_corners.png', image)
        return True
    else:
        print("❌ OpenCV corners not found")
    
    # Method 2: Color-based detection
    print("\n2. Testing color-based detection...")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Try different color ranges
    color_ranges = [
        ("Brown", np.array([10, 50, 50]), np.array([30, 255, 255])),
        ("Dark Brown", np.array([0, 50, 50]), np.array([20, 255, 255])),
        ("Light Brown", np.array([15, 30, 100]), np.array([35, 255, 255])),
        ("Gray/Black", np.array([0, 0, 50]), np.array([180, 255, 150])),
    ]
    
    for name, lower, upper in color_ranges:
        print(f"   Testing {name}...")
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find largest contour
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            min_area = (image.shape[0] * image.shape[1]) * 0.05
            
            if area > min_area:
                print(f"   ✅ {name} - Found contour with area: {area:.0f}")
                cv2.imwrite(f'debug_mask_{name.lower().replace(" ", "_")}.png', mask)
                
                # Draw contour
                debug_img = image.copy()
                cv2.drawContours(debug_img, [largest], -1, (0, 255, 0), 3)
                cv2.imwrite(f'debug_contour_{name.lower().replace(" ", "_")}.png', debug_img)
            else:
                print(f"   ❌ {name} - Contour too small: {area:.0f}")
        else:
            print(f"   ❌ {name} - No contours found")
    
    # Method 3: Edge detection
    print("\n3. Testing edge detection...")
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    cv2.imwrite('debug_edges.png', edges)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        min_area = (image.shape[0] * image.shape[1]) * 0.05
        
        if area > min_area:
            print(f"✅ Edge detection - Found contour with area: {area:.0f}")
            debug_img = image.copy()
            cv2.drawContours(debug_img, [largest], -1, (0, 255, 0), 3)
            cv2.imwrite('debug_contour_edges.png', debug_img)
        else:
            print(f"❌ Edge detection - Contour too small: {area:.0f}")
    else:
        print("❌ Edge detection - No contours found")
    
    # Method 4: Manual selection
    print("\n4. Manual board selection...")
    print("If automatic detection fails, you can manually select the board corners.")
    print("This will open a window where you can click the 4 corners of the chessboard.")
    
    response = input("Would you like to try manual selection? (y/n): ")
    if response.lower() in ['y', 'yes']:
        return manual_board_selection(image)
    
    return False

def manual_board_selection(image):
    """Manual board selection using mouse clicks."""
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
            return False
    
    cv2.destroyAllWindows()
    
    if len(points) == 4:
        print("✅ Manual selection completed!")
        print(f"Selected points: {points}")
        
        # Save the selected points
        points_array = np.array(points, dtype=np.float32)
        np.save('manual_board_points.npy', points_array)
        
        # Draw the selected board
        debug_img = image.copy()
        for i, point in enumerate(points):
            cv2.circle(debug_img, tuple(point), 10, (0, 255, 0), -1)
            cv2.putText(debug_img, str(i+1), (point[0]+15, point[1]+15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw lines connecting the points
        for i in range(4):
            pt1 = tuple(points[i])
            pt2 = tuple(points[(i+1) % 4])
            cv2.line(debug_img, pt1, pt2, (255, 0, 0), 2)
        
        cv2.imwrite('debug_manual_selection.png', debug_img)
        return True
    
    return False

def main():
    """Main debug function."""
    image_path = 'board.jpg'
    
    if not os.path.exists(image_path):
        print(f"❌ {image_path} not found!")
        print("Please ensure you have a chessboard image named 'board.jpg'")
        return
    
    print("Starting board detection debug...")
    success = debug_board_detection(image_path)
    
    if success:
        print("\n🎉 Board detection successful!")
        print("Check the generated debug images to see what was detected.")
    else:
        print("\n❌ Board detection failed.")
        print("Try:")
        print("1. Better lighting conditions")
        print("2. Clearer board edges")
        print("3. Manual selection")
        print("4. Different chessboard image")

if __name__ == "__main__":
    main() 