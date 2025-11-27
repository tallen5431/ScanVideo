#!/usr/bin/env python3
"""
Enhanced CamScan - System Verification Script
Run this to verify your installation is working correctly
"""

import sys
import os

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8 or higher is required")
        return False
    else:
        print("✅ Python version is compatible")
        return True

def check_dependencies():
    """Check if required packages can be imported"""
    print_header("Checking Dependencies")
    
    packages = {
        'flask': 'Flask',
        'cv2': 'OpenCV (opencv-python)',
        'numpy': 'NumPy',
        'waitress': 'Waitress'
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✅ {name} is installed")
        except ImportError:
            print(f"❌ {name} is NOT installed")
            all_ok = False
    
    return all_ok

def check_camera():
    """Check if camera can be accessed"""
    print_header("Checking Camera Access")
    
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        
        if not cam.isOpened():
            print("❌ Cannot open camera (index 0)")
            print("   Try: CAM_INDEX=1 ./Start.sh")
            cam.release()
            return False
        
        ret, frame = cam.read()
        cam.release()
        
        if not ret:
            print("❌ Cannot read from camera")
            return False
        
        print(f"✅ Camera is accessible")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def check_files():
    """Check if all required files exist"""
    print_header("Checking Project Files")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'Start.sh',
        'templates/index.html'
    ]
    
    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} is missing")
            all_ok = False
    
    return all_ok

def check_permissions():
    """Check if Start.sh is executable"""
    print_header("Checking Permissions")
    
    if not os.path.exists('Start.sh'):
        print("⚠️  Start.sh not found")
        return False
    
    if os.access('Start.sh', os.X_OK):
        print("✅ Start.sh is executable")
        return True
    else:
        print("⚠️  Start.sh is not executable")
        print("   Run: chmod +x Start.sh")
        return False

def test_square_detection():
    """Test if square detection code works"""
    print_header("Testing Square Detection")
    
    try:
        import cv2
        import numpy as np
        
        # Create a test image with a square
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.rectangle(img, (100, 100), (200, 200), (0, 0, 0), -1)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        found_square = False
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            if len(approx) == 4:
                found_square = True
                break
        
        if found_square:
            print("✅ Square detection algorithm works")
            return True
        else:
            print("❌ Square detection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Square detection test error: {e}")
        return False

def print_recommendations():
    """Print recommendations based on checks"""
    print_header("Recommendations")
    
    print("""
Next Steps:
1. If all checks passed: Run ./Start.sh to start the server
2. Open http://localhost:8091 in your browser
3. Print the calibration square using calibration_square_template.html
4. Show the square to your camera and click "Detect Calibration Square"

Troubleshooting:
- If camera fails: Try different CAM_INDEX values (0, 1, 2...)
- If dependencies fail: Run pip install -r requirements.txt
- If Start.sh not executable: Run chmod +x Start.sh

Documentation:
- Quick start: Read QUICKSTART.md
- Full guide: Read README.md
- Problems: Check README.md troubleshooting section
    """)

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         Enhanced CamScan - System Verification          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    checks = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Camera': check_camera(),
        'Files': check_files(),
        'Permissions': check_permissions(),
        'Detection': test_square_detection()
    }
    
    print_header("Summary")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    print("\nDetailed Results:")
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {check}")
    
    if passed == total:
        print("\n" + "="*60)
        print("  🎉 All checks passed! You're ready to go!")
        print("="*60)
        print("\nRun: ./Start.sh")
        print("Then open: http://localhost:8091")
    else:
        print("\n" + "="*60)
        print("  ⚠️  Some checks failed. See recommendations below.")
        print("="*60)
    
    print_recommendations()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Verification error: {e}")
        sys.exit(1)
