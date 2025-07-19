#!/usr/bin/env python3
"""
Test script for the complete Chessify-like OCR pipeline.
This demonstrates all the steps: board detection, square extraction, classification, and FEN generation.
"""

import os
import sys
import shutil

# Add src to path
sys.path.append('src')

def test_ocr_pipeline():
    """Test the complete OCR pipeline."""
    print("=" * 60)
    print("CHESSIFY-LIKE OCR PIPELINE TEST")
    print("=" * 60)
    
    # Check if required files exist
    required_files = [
        'piece_style_classifier.h5',
        'board.jpg'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please ensure you have:")
        print("- piece_style_classifier.h5 (your trained model)")
        print("- board.jpg (chessboard image to test)")
        return False
    
    print("✅ All required files found")
    
    try:
        # Import the OCR pipeline
        from vision.ocr_pipeline import run_ocr_pipeline
        from utils.fen_utils import validate_fen, print_board_state, fen_to_board_state
        
        print("\n🚀 Starting OCR Pipeline...")
        print("-" * 40)
        
        # Step 1: Run the complete pipeline
        print("Step 1: Running complete OCR pipeline...")
        fen = run_ocr_pipeline('board.jpg', 'piece_style_classifier.h5', (96, 96))
        
        if fen.startswith("Error:"):
            print(f"❌ Pipeline failed: {fen}")
            return False
        
        print(f"✅ FEN generated: {fen}")
        
        # Step 2: Validate FEN
        print("\nStep 2: Validating FEN...")
        if validate_fen(fen):
            print("✅ FEN is valid")
        else:
            print("⚠️  FEN validation failed")
        
        # Step 3: Display board state
        print("\nStep 3: Displaying board state...")
        board_state = fen_to_board_state(fen)
        if board_state:
            print_board_state(board_state)
        else:
            print("❌ Could not convert FEN to board state")
        
        # Step 4: Check output files
        print("\nStep 4: Checking output files...")
        output_files = [
            'extracted_squares/classification_results.json',
            'extracted_squares/board_fen.txt'
        ]
        
        for file in output_files:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"❌ {file} not found")
        
        # Step 5: Summary
        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"📋 Generated FEN: {fen}")
        print(f"📁 Output directory: extracted_squares/")
        print(f"📄 Results saved to: classification_results.json")
        print(f"📄 FEN saved to: board_fen.txt")
        
        # Check if we have the expected number of squares
        squares_dir = 'extracted_squares'
        if os.path.exists(squares_dir):
            square_files = [f for f in os.listdir(squares_dir) if f.startswith('square_') and f.endswith('.png')]
            print(f"🔲 Extracted squares: {len(square_files)}/64")
        
        print("\n🎉 Pipeline test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_individual_components():
    """Test individual components of the pipeline."""
    print("\n" + "=" * 60)
    print("INDIVIDUAL COMPONENT TESTS")
    print("=" * 60)
    
    all_components_ok = True
    
    try:
        # Test OCR class
        from vision.ocr_pipeline import ChessOCR
        print("✅ ChessOCR class imported successfully")
    except ImportError as e:
        print(f"❌ ChessOCR import error: {e}")
        all_components_ok = False
    
    try:
        # Test FEN utilities
        from utils.fen_utils import validate_fen, board_state_to_fen
        print("✅ FEN utilities imported successfully")
        
        # Test a simple FEN
        test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        if validate_fen(test_fen):
            print("✅ FEN validation works")
        else:
            print("❌ FEN validation failed")
    except ImportError as e:
        print(f"❌ FEN utilities import error: {e}")
        all_components_ok = False
    
    try:
        # Test manual correction UI
        from ui.manual_correction_ui import show_manual_correction_ui
        print("✅ Manual correction UI imported successfully")
    except ImportError as e:
        print(f"❌ Manual correction UI import error: {e}")
        all_components_ok = False
    
    if all_components_ok:
        print("✅ All components imported successfully")
    else:
        print("⚠️  Some components failed to import (see above)")
    
    return all_components_ok

def cleanup_test_files():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    files_to_remove = [
        'temp_board_for_ui.png',
        'chessboard_corners.png',
        'color_mask.png',
        'detected_board_contour.png',
        'warped_board_cropped.png',
        'warped_with_grid.png'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed {file}")
    
    # Clean up extracted_squares if it's empty
    if os.path.exists('extracted_squares'):
        try:
            if not os.listdir('extracted_squares'):
                os.rmdir('extracted_squares')
                print("🗑️  Removed empty extracted_squares directory")
        except:
            pass

def main():
    """Main test function."""
    print("Chessify-like OCR Pipeline Test")
    print("This will test the complete pipeline from image to FEN")
    print()
    
    # Test individual components first
    components_ok = test_individual_components()
    
    if not components_ok:
        print("\n⚠️  Some components failed to import.")
        print("The pipeline may still work with limited functionality.")
        print("Consider installing missing dependencies:")
        print("- pip install pyperclip (for clipboard support)")
        print("- pip install pillow (for image processing)")
        print()
    
    # Test the complete pipeline
    if test_ocr_pipeline():
        print("\n🎯 Pipeline test completed!")
        if components_ok:
            print("✅ All components working correctly.")
        else:
            print("⚠️  Pipeline works with limited functionality.")
    else:
        print("\n❌ Pipeline test failed. Please check the error messages above.")
    
    # Cleanup
    cleanup_test_files()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Integrate the pipeline with your chess GUI")
    print("2. Update the capture_image() function in chess_gui.py")
    print("3. Test with different chessboard images")
    print("4. Enhance piece type detection if needed")
    print("5. Install missing dependencies if needed")
    print("=" * 60)

if __name__ == "__main__":
    main() 