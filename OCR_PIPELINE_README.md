# Chessify-like OCR Pipeline

A complete chessboard OCR (Optical Character Recognition) pipeline that detects chessboards, extracts squares, classifies pieces, and generates FEN strings - similar to Chessify.

## 🎯 Overview

This pipeline provides a robust solution for converting chessboard images into FEN (Forsyth-Edwards Notation) strings through the following steps:

1. **Board Detection & Extraction**: Detect and crop the chessboard from an image
2. **Square Extraction**: Split the board into 64 individual squares
3. **Piece Classification**: Classify each square using your trained model
4. **FEN Generation**: Convert the classified board state to FEN notation
5. **Manual Correction**: Optional UI for manual corrections
6. **Output**: Save FEN to file and copy to clipboard

## 📁 Project Structure

```
pychessgame/
├── src/
│   ├── vision/
│   │   └── ocr_pipeline.py          # Main OCR pipeline
│   ├── utils/
│   │   └── fen_utils.py             # FEN utilities and clipboard operations
│   └── ui/
│       └── manual_correction_ui.py  # Manual correction interface
├── test_ocr_pipeline.py             # Test script
├── OCR_PIPELINE_README.md           # This file
└── piece_style_classifier.h5        # Your trained model
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.7+
- Required packages: `opencv-python`, `tensorflow`, `numpy`, `pillow`, `pyperclip`
- Your trained model: `piece_style_classifier.h5`
- A chessboard image: `board.jpg`

### 2. Test the Pipeline

```bash
python test_ocr_pipeline.py
```

This will:
- Check for required files
- Test individual components
- Run the complete pipeline
- Display results and validation

### 3. Use the Pipeline Programmatically

```python
from src.vision.ocr_pipeline import run_ocr_pipeline

# Run the complete pipeline
fen = run_ocr_pipeline('board.jpg', 'piece_style_classifier.h5', (96, 96))
print(f"Generated FEN: {fen}")
```

## 🔧 Pipeline Components

### 1. ChessOCR Class (`src/vision/ocr_pipeline.py`)

The main OCR class that handles the complete pipeline:

```python
from src.vision.ocr_pipeline import ChessOCR

# Initialize with your model
ocr = ChessOCR('piece_style_classifier.h5', (96, 96))

# Run complete pipeline
fen = ocr.run_ocr_pipeline('board.jpg')
```

**Key Methods:**
- `detect_board_and_extract_squares()`: Board detection and square extraction
- `classify_all_squares()`: Classify squares using your model
- `generate_fen_string()`: Convert results to FEN
- `manual_correction_ui()`: Show correction interface

### 2. FEN Utilities (`src/utils/fen_utils.py`)

Helper functions for FEN handling:

```python
from src.utils.fen_utils import (
    copy_fen_to_clipboard,
    save_fen_to_file,
    validate_fen,
    board_state_to_fen
)

# Copy FEN to clipboard
copy_fen_to_clipboard(fen)

# Save FEN to file
save_fen_to_file(fen, 'my_position.txt')

# Validate FEN
if validate_fen(fen):
    print("Valid FEN!")
```

### 3. Manual Correction UI (`src/ui/manual_correction_ui.py`)

Interactive interface for correcting detected positions:

```python
from src.ui.manual_correction_ui import show_manual_correction_ui

# Show correction UI
corrected_fen = show_manual_correction_ui(
    'board.jpg', 
    classification_results, 
    initial_fen
)
```

## 🔗 Integration with Chess GUI

### Update `capture_image()` Function

Replace the existing `capture_image()` function in `src/ui/chess_gui.py` with the OCR-integrated version:

```python
# Add these imports at the top of chess_gui.py
from src.vision.ocr_pipeline import run_ocr_pipeline
from src.utils.fen_utils import copy_fen_to_clipboard, save_fen_to_file
from src.ui.chess_gui_ocr_integration import show_fen_result_dialog

def capture_image_updated(self):
    """Updated capture_image function with OCR pipeline integration."""
    # ... existing camera capture code ...
    
    # After image acceptance, replace the old processing with:
    def run_ocr_thread():
        try:
            self.status_message = "Running OCR pipeline..."
            
            # Process with OCR
            fen = run_ocr_pipeline('board.jpg', 'piece_style_classifier.h5', (96, 96))
            
            if not fen.startswith("Error:"):
                # Show result dialog
                show_fen_result_dialog(fen)
                self.status_message = f"OCR completed! FEN: {fen[:30]}..."
            else:
                self.status_message = fen
                
        except Exception as e:
            self.status_message = f"OCR error: {e}"
    
    # Run OCR in background thread
    threading.Thread(target=run_ocr_thread).start()
```

### Update Upload Image Processing

Similarly, update the upload image processing:

```python
def process_uploaded_image_updated(self, file_path):
    """Updated upload image processing with OCR pipeline integration."""
    shutil.copy(file_path, 'board.jpg')
    self.status_message = ""
    
    def run_ocr_thread():
        try:
            self.status_message = "Running OCR pipeline..."
            fen = run_ocr_pipeline('board.jpg', 'piece_style_classifier.h5', (96, 96))
            
            if not fen.startswith("Error:"):
                show_fen_result_dialog(fen)
                self.status_message = f"OCR completed! FEN: {fen[:30]}..."
            else:
                self.status_message = fen
                
        except Exception as e:
            self.status_message = f"OCR error: {e}"
    
    threading.Thread(target=run_ocr_thread).start()
```

## 📊 Output Files

The pipeline generates several output files:

- `extracted_squares/`: Directory containing extracted square images
- `extracted_squares/classification_results.json`: Classification results with confidence scores
- `extracted_squares/board_fen.txt`: Generated FEN string
- Debug images: `chessboard_corners.png`, `color_mask.png`, etc.

## 🎛️ Configuration

### Model Configuration

```python
# Initialize with different model and image size
ocr = ChessOCR(
    model_path='my_custom_model.h5',
    img_size=(128, 128)  # Different input size
)
```

### Board Detection Parameters

```python
# Customize board detection
board_img, squares = ocr.detect_board_and_extract_squares(
    'board.jpg',
    output_dir='my_squares',
    square_size=128,           # Output square size
    pattern_size=(7, 7),       # Chessboard pattern
    crop_percent=0.05          # Border crop percentage
)
```

## 🔍 Troubleshooting

### Common Issues

1. **"Model not loaded" error**
   - Ensure `piece_style_classifier.h5` exists in the project root
   - Check TensorFlow installation

2. **"Chessboard not found" error**
   - Try different lighting conditions
   - Ensure the board is clearly visible
   - Check debug images in the output directory

3. **Import errors**
   - Ensure all required packages are installed
   - Check Python path includes the `src` directory

### Debug Mode

Enable debug output by checking the generated files:
- `chessboard_corners.png`: Shows detected corners
- `color_mask.png`: Shows color-based detection
- `detected_board_contour.png`: Shows detected board outline
- `warped_board_cropped.png`: Shows the processed board

## 🚀 Advanced Usage

### Custom Piece Classification

To enhance piece type detection (beyond just piece/no-piece):

```python
# Modify the generate_fen_string method in ChessOCR
def generate_fen_string(self, classification_results):
    # Map your model outputs to piece types
    piece_mapping = {
        'white_pawn': 'P',
        'white_rook': 'R',
        'white_knight': 'N',
        # ... etc
    }
    
    # Use confidence scores to determine piece types
    for result in classification_results:
        if result['confidence'] > 0.8:
            # High confidence - use specific piece type
            piece_type = piece_mapping.get(result['predicted_class'], 'P')
        else:
            # Low confidence - use generic piece
            piece_type = 'P'
```

### Batch Processing

```python
import os
from src.vision.ocr_pipeline import ChessOCR

ocr = ChessOCR('piece_style_classifier.h5')

# Process multiple images
image_dir = 'chessboard_images/'
for filename in os.listdir(image_dir):
    if filename.endswith(('.jpg', '.png')):
        image_path = os.path.join(image_dir, filename)
        fen = ocr.run_ocr_pipeline(image_path)
        print(f"{filename}: {fen}")
```

## 📈 Performance Tips

1. **Image Quality**: Use high-resolution, well-lit images
2. **Board Detection**: Ensure the board has clear edges and good contrast
3. **Model Training**: Train your model on diverse chess piece styles
4. **Batch Processing**: Process multiple images in sequence for efficiency

## 🤝 Contributing

To enhance the pipeline:

1. **Improve Board Detection**: Add more robust detection algorithms
2. **Enhance Classification**: Support for specific piece types
3. **Add Validation**: Chess position legality checking
4. **UI Improvements**: Better manual correction interface

## 📝 License

This OCR pipeline is part of your chess game project. Feel free to modify and extend as needed.

---

**Happy Chess OCR! 🎯♟️** 