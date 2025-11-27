# Enhanced CamScan - Calibration-based Measurement System

An upgraded camera scanning application that uses a 30mm calibration square to make accurate real-world measurements from video feed.

## Features

- **Automatic Calibration Square Detection**: Detects your 30mm calibration square using computer vision
- **Real-time Measurements**: Measure distances and areas in millimeters
- **Live Video Feed**: Works with phone cameras or webcams
- **Interactive Measurement**: Click on the video to mark measurement points
- **Professional Interface**: Clean, modern UI with real-time status updates

## How It Works

1. **Calibration**: The system detects a 30mm square in the camera view
2. **Scale Calculation**: Calculates pixels-per-millimeter ratio
3. **Measurement**: All subsequent measurements are converted to real-world units

## Requirements

- Python 3.8+
- Webcam or phone camera (via IP camera app)
- 30mm calibration square (printed or physical)

## Installation

### Quick Start (Linux)

```bash
chmod +x Start.sh
./Start.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Start the server on port 8091

### Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Usage

### 1. Prepare Your Calibration Square

You need a square that is exactly **30mm × 30mm**. You can:
- Print a square using the provided template
- Use a physical object with known 30mm dimensions
- Create a square using tape/paper

**Important**: The square should be:
- High contrast (black on white or vice versa)
- Flat and not warped
- Clearly visible to the camera
- Well-lit

### 2. Start the Application

```bash
./Start.sh
```

Or with custom settings:
```bash
HOST=0.0.0.0 PORT=8091 CAM_INDEX=0 ./Start.sh
```

### 3. Access the Interface

Open your browser and navigate to:
```
http://localhost:8091
```

Or from another device on the same network:
```
http://YOUR_IP_ADDRESS:8091
```

### 4. Calibrate

1. Show your 30mm calibration square to the camera
2. Click "Detect Calibration Square" or wait for auto-detection
3. The system will highlight the detected square in green
4. Status will show "Calibrated" with pixels-per-mm ratio

### 5. Make Measurements

Once calibrated:

**Distance Measurement:**
- Click on the video at two points
- Distance in mm will be displayed

**Area Measurement:**
- Click on the video at 3 or more points to define a polygon
- Area in mm² will be displayed

**Clear and Restart:**
- Click "Clear Points" to remove measurement points
- Click "Reset Calibration" to recalibrate

## Configuration

### Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8091)
- `CAM_INDEX`: Camera index (default: 0)

### Calibration Square Size

To change the calibration square size, edit in `app.py`:

```python
CALIBRATION_SQUARE_MM = 30.0  # Change to your square size
```

### Detection Sensitivity

Adjust these parameters in `app.py`:

```python
MIN_SQUARE_AREA = 500  # Minimum pixel area for detection
MAX_SQUARE_AREA = 100000  # Maximum pixel area for detection
```

## Using with Phone Camera

To use your phone as a camera:

1. Install an IP camera app on your phone:
   - **Android**: IP Webcam, DroidCam
   - **iOS**: EpocCam, iVCam

2. Note the camera stream URL (usually like `http://192.168.1.x:8080/video`)

3. Modify camera initialization in `app.py`:

```python
# Replace CAM_INDEX with URL
camera = cv2.VideoCapture("http://192.168.1.100:8080/video")
```

Or use the IP camera as a network device:
```python
CAM_INDEX = "http://192.168.1.100:8080/video"
```

## Troubleshooting

### Calibration Not Detected

**Problem**: Square is not being detected

**Solutions**:
- Ensure square is high contrast (black on white)
- Improve lighting conditions
- Make sure square is flat and not warped
- Square should fill 10-30% of the frame
- Try adjusting `MIN_SQUARE_AREA` and `MAX_SQUARE_AREA`

### Measurements Are Inaccurate

**Problem**: Measurements don't match real-world dimensions

**Solutions**:
- Verify your calibration square is exactly 30mm
- Ensure the square and measured objects are on the same plane
- Recalibrate if camera moves or zoom changes
- Keep camera perpendicular to the measurement surface

### Video Feed Is Slow

**Problem**: Low frame rate or laggy video

**Solutions**:
- Reduce camera resolution in `app.py`:
  ```python
  camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
  camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
  ```
- Increase frame update interval in `templates/index.html`:
  ```javascript
  frameInterval = setInterval(updateFrame, 200); // 5 FPS
  ```

### Camera Not Found

**Problem**: "Failed to capture frame" error

**Solutions**:
- Check camera permissions
- Try different `CAM_INDEX` values (0, 1, 2, etc.)
- Verify camera is not in use by another application
- For external cameras, ensure they're properly connected

## Technical Details

### Detection Algorithm

1. **Preprocessing**: 
   - Convert to grayscale
   - Gaussian blur
   - Adaptive threshold + Canny edge detection

2. **Contour Detection**:
   - Find all contours in the image
   - Filter for quadrilaterals (4-sided shapes)

3. **Square Validation**:
   - Check area within reasonable range
   - Verify aspect ratio is close to 1:1 (square)
   - Select largest valid square

4. **Calibration**:
   - Calculate average side length in pixels
   - Compute pixels-per-millimeter ratio
   - Valid for 60 seconds (redetects if expired)

### Measurement Calculations

**Distance**: Euclidean distance between two points
```
distance_mm = sqrt((x2-x1)² + (y2-y1)²) / pixels_per_mm
```

**Area**: Polygon area using contour area
```
area_mm² = contour_area_pixels / (pixels_per_mm)²
```

## API Endpoints

The application provides REST API endpoints:

- `GET /api/frame` - Get current annotated frame
- `POST /api/calibrate` - Force calibration detection
- `POST /api/add_point` - Add measurement point (x, y)
- `POST /api/clear_points` - Clear all measurement points
- `GET /api/status` - Get calibration and measurement status

## Customization

### Changing Square Detection Color

In `app.py`, find the line:
```python
cv2.drawContours(frame, [square], -1, (0, 255, 0), 3)
```

Change `(0, 255, 0)` to your preferred BGR color.

### Adding New Measurement Types

Add new measurement methods to the `MeasurementTool` class:

```python
def calculate_perimeter(self) -> Optional[float]:
    """Calculate perimeter of polygon"""
    if len(self.measurement_points) < 3:
        return None
    
    perimeter_pixels = 0
    points = self.measurement_points
    
    for i in range(len(points)):
        p1 = np.array(points[i])
        p2 = np.array(points[(i + 1) % len(points)])
        perimeter_pixels += np.linalg.norm(p2 - p1)
    
    return self.detector.pixels_to_mm(perimeter_pixels)
```

## License

This is an educational project. Use freely for personal and commercial purposes.

## Tips for Best Results

1. **Lighting**: Ensure even, bright lighting without shadows
2. **Stability**: Keep camera steady during measurement
3. **Angle**: Camera should be perpendicular to measurement surface
4. **Distance**: Keep consistent distance from camera to objects
5. **Recalibrate**: Recalibrate if camera moves or zoom changes

## Credits

Built with:
- **OpenCV** - Computer vision
- **Flask** - Web framework
- **NumPy** - Numerical computing

---

**Need help?** Check the troubleshooting section or submit an issue.

**Want to contribute?** Feel free to submit pull requests with improvements!
