# 🚀 Quick Start Guide - Enhanced CamScan

## What You Need

1. **30mm Calibration Square** - Print the `calibration_square_template.html` file
2. **Camera** - Webcam or phone camera
3. **Python 3.8+** - Pre-installed on most systems

## Step-by-Step Setup (3 minutes)

### 1️⃣ Print Your Calibration Square

```bash
# Open the template in your browser
open calibration_square_template.html
# Or on Linux: xdg-open calibration_square_template.html

# Click "Print" and follow the on-screen instructions
# IMPORTANT: Print at 100% scale, NO "fit to page"
```

**Verify**: Measure the printed square with a ruler - it should be exactly 30mm × 30mm

### 2️⃣ Start the Server

```bash
# Make the script executable (first time only)
chmod +x Start.sh

# Run the application
./Start.sh
```

The script will automatically:
- Create a virtual environment
- Install all dependencies
- Start the server on port 8091

### 3️⃣ Open in Browser

```
http://localhost:8091
```

Or from your phone on the same network:
```
http://YOUR_COMPUTER_IP:8091
```

To find your IP:
```bash
# Linux/Mac
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr IPv4
```

### 4️⃣ Calibrate and Measure!

1. **Show the calibration square** to your camera
2. **Click "Detect Calibration Square"** or wait for auto-detection
3. **Click on the video** to mark points and measure distances/areas

## 📱 Using Phone Camera

### Option A: Direct USB Connection
Many phones can be used as a webcam when connected via USB. Install:
- **Android**: DroidCam (free)
- **iOS**: EpocCam (free)

### Option B: IP Camera App
1. Install IP camera app on your phone
2. Note the stream URL (e.g., `http://192.168.1.100:8080/video`)
3. Edit `app.py` and change line ~217:
   ```python
   CAM_INDEX = "http://192.168.1.100:8080/video"  # Your phone's IP
   ```

## 🔧 Common Issues & Fixes

### "Camera not found"
```bash
# Try different camera indices
CAM_INDEX=0 ./Start.sh  # Default
CAM_INDEX=1 ./Start.sh  # External camera
CAM_INDEX=2 ./Start.sh  # Second external camera
```

### "Calibration square not detected"
- Ensure good lighting
- Square should be flat and clearly visible
- Fill 10-30% of the camera view
- Try a high-contrast printed square

### "Port 8091 already in use"
```bash
# Use a different port
PORT=8092 ./Start.sh
```

## 📏 Tips for Accurate Measurements

1. **Keep camera perpendicular** to the measurement surface
2. **Same plane**: Calibration square and measured object should be on the same flat surface
3. **Don't move camera** after calibration
4. **Good lighting** is essential
5. **Recalibrate** if you move the camera or zoom

## 🎯 What You Can Measure

- **Distances**: Click 2 points → Get distance in mm
- **Areas**: Click 3+ points → Get area in mm²
- **Multiple measurements**: Clear points and start over

## 🛠 Advanced Configuration

### Change Calibration Square Size
Edit `app.py`, line 15:
```python
CALIBRATION_SQUARE_MM = 30.0  # Change to your square size
```

### Adjust Detection Sensitivity
Edit `app.py`, lines 16-17:
```python
MIN_SQUARE_AREA = 500      # Minimum detection size
MAX_SQUARE_AREA = 100000   # Maximum detection size
```

### Change Server Settings
```bash
HOST=0.0.0.0 PORT=8080 CAM_INDEX=0 ./Start.sh
```

## 📚 Full Documentation

See `README.md` for complete documentation including:
- Detailed API documentation
- Customization options
- Troubleshooting guide
- Technical details

## 💡 Example Use Cases

- Measure small objects without a ruler
- Check dimensions of printed parts
- Verify PCB component spacing
- Measure fabric/paper for crafts
- Architecture model measurements
- Quick field measurements

## 🆘 Need Help?

1. Check `README.md` for detailed troubleshooting
2. Verify your calibration square is exactly 30mm
3. Ensure camera permissions are granted
4. Try different lighting conditions

## ⚡ Pro Tips

- **Multiple Squares**: Print several squares and keep them handy
- **Laminate**: Protect your calibration square by laminating it
- **Mount on Cardboard**: Attach to rigid backing for better flatness
- **Reference Objects**: Keep squares of different sizes for different zoom levels

---

**Ready to measure?** Run `./Start.sh` and open http://localhost:8091 🎉
