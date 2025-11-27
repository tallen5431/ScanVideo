#!/usr/bin/env python3
"""
Enhanced CamScan with Calibration Square Detection
Detects a 30mm calibration square and enables real-world measurements
"""

import os
import io
import base64
import json
import time
from typing import Optional, Tuple, List, Dict, Any

import cv2
import numpy as np
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

# Configuration
CALIBRATION_SQUARE_MM = 30.0  # Known size of calibration square in millimeters
MIN_SQUARE_AREA = 200  # Minimum area in pixels to consider as a square (lowered for better detection)
MAX_SQUARE_AREA = 200000  # Maximum area in pixels (increased for close-up squares)


class CalibrationDetector:
    """Detects and tracks calibration square for measurements"""
    
    def __init__(self, real_size_mm: float = 30.0):
        self.real_size_mm = real_size_mm
        self.pixels_per_mm: Optional[float] = None
        self.calibration_square: Optional[np.ndarray] = None
        self.last_detection_time = 0
        
    def detect_squares(self, frame: np.ndarray) -> List[np.ndarray]:
        """Detect all square-like contours in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        squares = []

        # Try multiple threshold methods for robustness
        threshold_methods = []

        # Method 1: Adaptive threshold (inverted for black squares)
        thresh_inv = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        threshold_methods.append(thresh_inv)

        # Method 2: Adaptive threshold (normal for white squares)
        thresh_normal = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        threshold_methods.append(thresh_normal)

        # Method 3: Simple binary threshold for black squares
        _, thresh_binary_inv = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
        threshold_methods.append(thresh_binary_inv)

        # Method 4: Otsu's threshold (inverted)
        _, thresh_otsu_inv = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        threshold_methods.append(thresh_otsu_inv)

        # Method 5: Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        threshold_methods.append(edges)

        # Try to find squares in each thresholded image
        seen_squares = set()

        for thresh in threshold_methods:
            # Find contours
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                # Approximate the contour
                peri = cv2.arcLength(contour, True)
                if peri < 20:  # Skip very small contours (lowered threshold)
                    continue

                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

                # Check if it's a quadrilateral
                if len(approx) == 4:
                    area = cv2.contourArea(approx)

                    # Filter by area
                    if MIN_SQUARE_AREA < area < MAX_SQUARE_AREA:
                        # Check if it's roughly square-shaped
                        x, y, w, h = cv2.boundingRect(approx)
                        aspect_ratio = float(w) / h if h > 0 else 0

                        # Accept if aspect ratio is close to 1:1 (square) - relaxed tolerance
                        if 0.6 < aspect_ratio < 1.7:
                            # Create a unique signature for this square to avoid duplicates
                            signature = (int(x/10)*10, int(y/10)*10, int(w/10)*10, int(h/10)*10)
                            if signature not in seen_squares:
                                seen_squares.add(signature)
                                squares.append(approx)

        return squares
    
    def detect_cube_pattern(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[List[np.ndarray]]]:
        """Detect calibration cube pattern: 30mm black square with 4x 5mm white corner squares.
        
        Returns:
            (found, outer_square, inner_squares)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect dark regions (the black 30mm square)
        _, thresh_dark = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Detect bright regions (the white 5mm squares)
        _, thresh_bright = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours in dark regions
        contours_dark, _ = cv2.findContours(
            thresh_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Find potential outer squares (black 30mm square)
        outer_candidates = []
        for contour in contours_dark:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                if MIN_SQUARE_AREA < area < MAX_SQUARE_AREA:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    if 0.6 < aspect_ratio < 1.7:
                        outer_candidates.append((approx, area, (x, y, w, h)))
        
        if not outer_candidates:
            return False, None, None
        
        # Sort by area and try each candidate
        outer_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for outer_square, outer_area, (ox, oy, ow, oh) in outer_candidates:
            # Look for 4 small white squares inside this outer square
            # Extract ROI
            margin = 5  # Small margin
            x1 = max(0, ox - margin)
            y1 = max(0, oy - margin)
            x2 = min(frame.shape[1], ox + ow + margin)
            y2 = min(frame.shape[0], oy + oh + margin)
            
            roi = thresh_bright[y1:y2, x1:x2]
            
            # Find contours in the ROI
            contours_bright, _ = cv2.findContours(
                roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Look for small square contours
            inner_squares = []
            for contour in contours_bright:
                peri = cv2.arcLength(contour, True)
                if peri < 10:  # Too small
                    continue
                    
                approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
                
                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Small squares should be roughly 1/36 of outer square (5mm vs 30mm)
                    expected_area = outer_area / 36.0
                    
                    # Accept squares that are roughly the right size
                    if 0.1 * expected_area < area < 3.0 * expected_area:
                        x, y, w, h = cv2.boundingRect(approx)
                        aspect_ratio = float(w) / h if h > 0 else 0
                        
                        if 0.6 < aspect_ratio < 1.4:
                            # Adjust contour coordinates back to frame coordinates
                            adjusted = approx.copy()
                            adjusted[:, 0, 0] += x1
                            adjusted[:, 0, 1] += y1
                            inner_squares.append(adjusted)
            
            # Check if we found 3-4 inner squares (allowing some detection failures)
            if len(inner_squares) >= 3:
                return True, outer_square, inner_squares
        
        return False, None, None

    def find_calibration_square(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """Find the best candidate for calibration square.
        
        First tries to detect the cube pattern (30mm square with 4x 5mm inner squares).
        Falls back to simple square detection if cube pattern not found.
        """
        # Try cube pattern detection first
        found_cube, outer_square, inner_squares = self.detect_cube_pattern(frame)
        
        if found_cube and outer_square is not None:
            # Calculate pixels per mm using the outer square
            side_length = self.calculate_square_side_length(outer_square)
            self.pixels_per_mm = side_length / self.real_size_mm
            self.calibration_square = outer_square
            self.last_detection_time = time.time()
            print(f"✓ Detected cube pattern! Calibration: {self.pixels_per_mm:.2f} px/mm")
            return True, outer_square
        
        # Fallback to simple square detection
        squares = self.detect_squares(frame)

        if not squares:
            print(f"⊗ No squares detected in frame")
            return False, None

        print(f"⊙ Found {len(squares)} potential square(s)")
        
        # Sort by area (assuming calibration square is prominent)
        squares.sort(key=lambda s: cv2.contourArea(s), reverse=True)
        
        # Use the largest square that meets criteria
        best_square = squares[0]
        
        # Calculate pixels per mm
        side_length = self.calculate_square_side_length(best_square)
        self.pixels_per_mm = side_length / self.real_size_mm
        self.calibration_square = best_square
        self.last_detection_time = time.time()
        print(f"○ Detected simple square. Calibration: {self.pixels_per_mm:.2f} px/mm")
        
        return True, best_square
    
    def calculate_square_side_length(self, square: np.ndarray) -> float:
        """Calculate the average side length of a square contour in pixels"""
        points = square.reshape(-1, 2)
        sides = []
        
        for i in range(4):
            p1 = points[i]
            p2 = points[(i + 1) % 4]
            distance = np.linalg.norm(p2 - p1)
            sides.append(distance)
        
        return np.mean(sides)
    
    def is_calibrated(self) -> bool:
        """Check if calibration is valid"""
        return (self.pixels_per_mm is not None and 
                time.time() - self.last_detection_time < 60)  # Valid for 60 seconds
    
    def pixels_to_mm(self, pixels: float) -> float:
        """Convert pixels to millimeters"""
        if not self.is_calibrated():
            return 0.0
        return pixels / self.pixels_per_mm
    
    def mm_to_pixels(self, mm: float) -> float:
        """Convert millimeters to pixels"""
        if not self.is_calibrated():
            return 0.0
        return mm * self.pixels_per_mm


class MeasurementTool:
    """Handles measurement operations"""
    
    def __init__(self, detector: CalibrationDetector):
        self.detector = detector
        self.measurement_points: List[Tuple[int, int]] = []
        
    def add_point(self, x: int, y: int):
        """Add a measurement point"""
        self.measurement_points.append((x, y))
        
    def clear_points(self):
        """Clear all measurement points"""
        self.measurement_points = []
        
    def calculate_distance(self) -> Optional[float]:
        """Calculate distance between two points in mm"""
        if len(self.measurement_points) < 2:
            return None
        
        p1 = np.array(self.measurement_points[0])
        p2 = np.array(self.measurement_points[1])
        
        pixel_distance = np.linalg.norm(p2 - p1)
        return self.detector.pixels_to_mm(pixel_distance)
    
    def calculate_area(self) -> Optional[float]:
        """Calculate area of polygon defined by points in mmÂ²"""
        if len(self.measurement_points) < 3:
            return None
        
        points = np.array(self.measurement_points, dtype=np.int32)
        pixel_area = cv2.contourArea(points)
        
        # Convert pixelÂ² to mmÂ²
        if self.detector.is_calibrated():
            mm_per_pixel = 1.0 / self.detector.pixels_per_mm
            return pixel_area * (mm_per_pixel ** 2)
        
        return None


# Global instances
detector = CalibrationDetector(CALIBRATION_SQUARE_MM)
measurement_tool = MeasurementTool(detector)

# Camera capture
camera = None

def get_cam_index():
    """Safely get camera index from environment"""
    cam_index_str = os.getenv("CAM_INDEX", "0")
    try:
        # Try to parse as integer
        return int(cam_index_str)
    except ValueError:
        # If it's a URL string, return as-is
        return cam_index_str
        
CAM_INDEX = get_cam_index()


def get_camera():
    """Get or initialize camera"""
    global camera
    if camera is None or not camera.isOpened():
        try:
            camera = cv2.VideoCapture(CAM_INDEX)
            if camera.isOpened():
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            else:
                print(f"Warning: Could not open camera {CAM_INDEX}")
                return None
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return None
    return camera


def release_camera():
    """Release camera resources"""
    global camera
    if camera is not None:
        camera.release()
        camera = None


@app.route("/")
def index():
    """Serve the main HTML interface"""
    return render_template("index.html")


@app.route("/api/frame")
def api_get_frame():
    """Get current camera frame with annotations"""
    cam = get_camera()
    
    if cam is None:
        return jsonify({"error": "Camera not initialized. Check camera connection."}), 500
    
    ret, frame = cam.read()
    
    if not ret:
        return jsonify({"error": "Failed to capture frame. Camera may be in use."}), 500
    
    # Try to detect calibration square if not calibrated
    if not detector.is_calibrated():
        found, square = detector.find_calibration_square(frame)
        if found and square is not None:
            # Draw the calibration square
            cv2.drawContours(frame, [square], -1, (0, 255, 0), 3)
            cv2.putText(
                frame, "Calibration Square Detected!", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )
        else:
            # Show all detected squares for debugging
            all_squares = detector.detect_squares(frame)
            if all_squares:
                # Draw all detected squares in yellow for debugging
                for sq in all_squares:
                    cv2.drawContours(frame, [sq], -1, (0, 255, 255), 2)
                cv2.putText(
                    frame, f"Found {len(all_squares)} square(s) - need better match", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
                )
    
    # Draw calibration status
    if detector.is_calibrated():
        status_text = f"Calibrated: {detector.pixels_per_mm:.2f} px/mm"
        cv2.putText(
            frame, status_text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
    else:
        cv2.putText(
            frame, "Show calibration square", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
    
    # Draw measurement points
    for i, point in enumerate(measurement_tool.measurement_points):
        cv2.circle(frame, point, 5, (255, 0, 0), -1)
        cv2.putText(
            frame, str(i + 1), (point[0] + 10, point[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2
        )
    
    # Draw lines between measurement points
    if len(measurement_tool.measurement_points) >= 2:
        for i in range(len(measurement_tool.measurement_points) - 1):
            cv2.line(
                frame, 
                measurement_tool.measurement_points[i],
                measurement_tool.measurement_points[i + 1],
                (255, 0, 0), 2
            )
    
    # Calculate and display measurements
    if len(measurement_tool.measurement_points) == 2:
        distance = measurement_tool.calculate_distance()
        if distance is not None:
            mid_point = (
                (measurement_tool.measurement_points[0][0] + measurement_tool.measurement_points[1][0]) // 2,
                (measurement_tool.measurement_points[0][1] + measurement_tool.measurement_points[1][1]) // 2
            )
            cv2.putText(
                frame, f"{distance:.1f} mm", mid_point,
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2
            )
    
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        "image": frame_base64,
        "calibrated": detector.is_calibrated(),
        "pixels_per_mm": detector.pixels_per_mm,
        "measurement_points": len(measurement_tool.measurement_points)
    })


@app.route("/api/calibrate", methods=["POST"])
def api_calibrate():
    """Force calibration detection"""
    cam = get_camera()
    
    if cam is None:
        return jsonify({"error": "Camera not initialized"}), 500
    
    ret, frame = cam.read()
    
    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500
    
    found, square = detector.find_calibration_square(frame)
    
    if found:
        return jsonify({
            "success": True,
            "pixels_per_mm": detector.pixels_per_mm,
            "message": "Calibration successful!"
        })
    else:
        return jsonify({
            "success": False,
            "message": "No calibration square found. Make sure it's visible and well-lit."
        })


@app.route("/api/add_point", methods=["POST"])
def api_add_point():
    """Add a measurement point"""
    data = request.json
    x = data.get("x")
    y = data.get("y")
    
    if x is None or y is None:
        return jsonify({"error": "Missing x or y coordinate"}), 400
    
    if not detector.is_calibrated():
        return jsonify({"error": "Not calibrated. Show calibration square first."}), 400
    
    measurement_tool.add_point(int(x), int(y))
    
    # Calculate results if we have enough points
    result = {
        "points": len(measurement_tool.measurement_points)
    }
    
    if len(measurement_tool.measurement_points) == 2:
        distance = measurement_tool.calculate_distance()
        result["distance_mm"] = round(distance, 2) if distance else None
    
    if len(measurement_tool.measurement_points) >= 3:
        area = measurement_tool.calculate_area()
        result["area_mm2"] = round(area, 2) if area else None
    
    return jsonify(result)


@app.route("/api/clear_points", methods=["POST"])
def api_clear_points():
    """Clear all measurement points"""
    measurement_tool.clear_points()
    return jsonify({"success": True})


@app.route("/api/calibrate_frame", methods=["POST", "OPTIONS"])
def api_calibrate_frame():
    """Calibrate using a frame sent from browser camera"""
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    print(f"[DEBUG] Received calibrate_frame request")
    print(f"[DEBUG] Content-Type: {request.content_type}")
    print(f"[DEBUG] Request method: {request.method}")

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON data"}), 400

    if not data:
        print(f"[ERROR] No JSON data in request")
        return jsonify({"error": "No JSON data provided"}), 400

    frame_base64 = data.get("frame")
    auto_mode = data.get("auto", False)
    
    if not frame_base64:
        return jsonify({"error": "No frame data provided"}), 400
    
    try:
        # Decode base64 image - handle data URL format
        if ',' in frame_base64:
            frame_base64 = frame_base64.split(',')[1]
            
        frame_bytes = base64.b64decode(frame_base64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"error": "Failed to decode frame"}), 400
        
        # Try to find calibration square
        found, square = detector.find_calibration_square(frame)
        
        # Draw the detected square on the frame for visual feedback
        annotated_frame = frame.copy()
        if found and square is not None:
            # Draw green rectangle around detected square
            cv2.drawContours(annotated_frame, [square], -1, (0, 255, 0), 3)

            # Add "CALIBRATED" text
            cv2.putText(
                annotated_frame, "CALIBRATED!", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3
            )

            # Show calibration info
            cal_text = f"Scale: {detector.pixels_per_mm:.2f} px/mm"
            cv2.putText(
                annotated_frame, cal_text, (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
        else:
            # Show all detected squares for debugging
            all_squares = detector.detect_squares(frame)
            if all_squares:
                # Draw all detected squares in yellow for debugging
                for sq in all_squares:
                    cv2.drawContours(annotated_frame, [sq], -1, (0, 255, 255), 2)
                cv2.putText(
                    annotated_frame, f"Found {len(all_squares)} square(s) - need better match", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2
                )
            else:
                # Draw "SEARCHING..." text
                cv2.putText(
                    annotated_frame, "SEARCHING FOR SQUARE...", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2
                )
        
        # Encode annotated frame back to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        if found:
            return jsonify({
                "success": True,
                "calibrated": True,
                "pixels_per_mm": detector.pixels_per_mm,
                "message": "Calibration successful!",
                "annotated_frame": annotated_base64
            })
        else:
            return jsonify({
                "success": False,
                "calibrated": False,
                "message": "Searching for calibration square..." if auto_mode else "No calibration square found. Make sure it's visible and well-lit.",
                "annotated_frame": annotated_base64
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Calibration error: {str(e)}"}), 500


@app.route("/api/status")
def api_status():
    """Get current status"""
    return jsonify({
        "calibrated": detector.is_calibrated(),
        "pixels_per_mm": detector.pixels_per_mm,
        "measurement_points": len(measurement_tool.measurement_points),
        "calibration_square_mm": CALIBRATION_SQUARE_MM
    })


@app.route("/api/test")
def api_test():
    """Test endpoint to verify API is working"""
    return jsonify({
        "status": "ok",
        "message": "API is working",
        "endpoints": [
            "/api/frame",
            "/api/calibrate",
            "/api/calibrate_frame",
            "/api/add_point",
            "/api/clear_points",
            "/api/status",
            "/api/test"
        ]
    })


if __name__ == "__main__":
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8091"))
    
    print(f"Starting Enhanced CamScan on {HOST}:{PORT}")
    print(f"Calibration square size: {CALIBRATION_SQUARE_MM}mm")
    
    try:
        from waitress import serve
        # Increase max request body size to 10MB for base64 image uploads
        serve(app, host=HOST, port=PORT, max_request_body_size=10485760)
    except ImportError:
        print("Waitress not installed, using Flask development server")
        app.run(host=HOST, port=PORT, debug=False)
    finally:
        release_camera()