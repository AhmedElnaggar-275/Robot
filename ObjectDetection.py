#!/usr/bin/env python3  # Allow running this file directly on Linux/macOS (Windows ignores this line)
"""  # Module docstring: explains what this script does.
Face Tracking Robot Controller - FIXED VERSION  # High-level description.
Stops when no face detected  # Behavior note: sends STOP when face not detected.

NOTE ABOUT THIS REPO:  # Important project-specific note.
- The Arduino sketch in this repository (Robot.ino / robot.cpp) does not currently parse these serial commands.  # So PC->Arduino commands may do nothing.
- This Python script is still useful for testing the face detection and command decision logic on the PC.  # You can later update Arduino to read serial.
"""  # End of module docstring.

import cv2  # type: ignore  # OpenCV: camera capture, drawing, and face detection (Pylance stubs may be incomplete).
import serial  # PySerial: used to talk to Arduino over USB serial.
import time  # Used for delays and timeouts.
import numpy as np  # NumPy: used to create images (manual control UI).
from collections import deque  # Deque: fixed-length queue for smoothing face positions.
import threading  # Unused right now; kept because it existed in original code.
import sys  # Used for sys.exit when a fatal error occurs.
import os  # Unused right now; kept because it existed in original code.


class FaceTrackingRobot:  # Main class that owns camera, detector, and Arduino link.
    def __init__(self, arduino_port=None, camera_id=0):  # Constructor parameters: serial port and camera index.
        """  # Docstring for __init__.
        Initialize face tracking robot  # Create camera + optionally connect to Arduino.
        If arduino_port is None, runs in simulation mode  # Simulation prints commands instead of sending serial.
        """  # End docstring.
        # Arduino connection  # Section header.
        self.arduino = None  # Will hold serial.Serial object when connected.
        self.simulation_mode = False  # Becomes True if no port or connect fails.

        if arduino_port:  # If user provided a port string like "COM3".
            try:  # Try to open the serial connection.
                self.arduino = serial.Serial(arduino_port, 115200, timeout=1)  # Open serial at 115200 baud.
                time.sleep(2)  # Give Arduino time to reset after opening serial.
                print(f"✓ Connected to Arduino on {arduino_port}")  # User feedback.
            except Exception as e:  # noqa: BLE001  # If opening serial fails (broad except to keep UX simple).
                print(f"✗ Could not connect to Arduino: {e}")  # Show error.
                print("Running in SIMULATION MODE (no robot movement)")  # Fall back to simulation.
                self.simulation_mode = True  # Mark simulation mode.
        else:  # No port provided.
            print("Running in SIMULATION MODE (no robot movement)")  # Inform the user.
            self.simulation_mode = True  # Mark simulation mode.

        # Initialize camera  # Section header.
        self.cap = cv2.VideoCapture(camera_id)  # Open camera device by index (0 is default webcam).
        if not self.cap.isOpened():  # If OpenCV failed to open the camera.
            print("✗ Error: Could not open camera!")  # Print a clear error.
            sys.exit(1)  # Exit program with non-zero code.

        # Set camera resolution  # Attempt to request resolution.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Ask for width = 640 pixels.
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Ask for height = 480 pixels.

        # Load face detection model (Haar Cascade - built into OpenCV)  # Use classic Haar cascade.
        self.face_cascade = cv2.CascadeClassifier(  # Create the classifier object.
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'  # Path to pre-trained face cascade.
        )  # End CascadeClassifier creation.

        if self.face_cascade.empty():  # If the classifier failed to load.
            print("✗ Error: Could not load face detection model!")  # Print error.
            sys.exit(1)  # Exit because face detection can't run.

        print("✓ Face detection model loaded")  # Inform the user it's ready.

        # Tracking parameters  # Precomputed dimensions and centers.
        self.frame_width = 640  # Expected frame width (matches requested capture size).
        self.frame_height = 480  # Expected frame height (matches requested capture size).
        self.center_x = self.frame_width // 2  # X coordinate of frame center.
        self.center_y = self.frame_height // 2  # Y coordinate of frame center.

        # Control parameters - ADJUST THESE FOR YOUR ROBOT  # Tuning knobs.
        self.dead_zone = 80  # Pixels near center where we don't turn.
        self.min_face_size = 15000  # Face area threshold: smaller means far away.
        self.max_face_size = 60000  # Face area threshold: larger means too close.

        # Search parameters  # Used if you implement search when no face.
        self.no_face_counter = 0  # Counts consecutive frames with no detected face.
        self.search_direction = 'L'  # Default search direction if search is enabled.
        self.last_face_time = time.time()  # Timestamp of last detection.
        self.search_timeout = 2.0  # Seconds without a face before searching.

        # Face position history for smoothing  # Reduces jitter.
        self.face_positions = deque(maxlen=5)  # Keep last 5 face measurements.

        # Movement control  # State variables.
        self.movement_enabled = True  # Can be toggled with 's'.
        self.last_command = None  # Last command sent, used to reduce spam.
        self.command_count = 0  # Counter used to periodically resend command.

        print("\n" + "="*50)  # Print a divider line.
        print("FACE TRACKING ROBOT CONTROLS - FIXED")  # Title.
        print("="*50)  # Another divider.
        print("When NO FACE detected: Robot STOPS")  # Behavior summary.
        print("Press 'q' to quit")  # Key hint.
        print("Press 's' to toggle movement on/off")  # Key hint.
        print("Press 'm' for manual control mode")  # Key hint.
        print("="*50 + "\n")  # Divider and spacing.

    def detect_face(self, frame):  # Given a frame, try to find a face.
        """Detect faces in frame using Haar Cascade"""  # Method docstring.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert BGR image to grayscale.

        # Enhance contrast for better detection  # Helps Haar cascade on low-contrast images.
        gray = cv2.equalizeHist(gray)  # Histogram equalization.

        # Detect faces  # Return list of rectangles.
        faces = self.face_cascade.detectMultiScale(  # Run multi-scale detection.
            gray,  # Input image (grayscale).
            scaleFactor=1.1,  # Step between scales; smaller = slower but more accurate.
            minNeighbors=6,  # Higher = fewer false positives.
            minSize=(80, 80),  # Ignore tiny detections.
            maxSize=(400, 400),  # Ignore huge detections.
            flags=cv2.CASCADE_SCALE_IMAGE  # Compatibility flag.
        )  # End detectMultiScale.

        if len(faces) == 0:  # If no faces detected.
            return None  # Signal to caller that no face exists.

        # Get the largest face  # Prefer the closest/most prominent face.
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])  # Choose by area w*h.
        x, y, w, h = largest_face  # Unpack rectangle.

        return (x, y, w, h)  # Return bounding box.

    def calculate_movement_command(self, face_rect):  # Decide what command to send.
        """Calculate movement command based on face position"""  # Docstring.
        if face_rect is None:  # If we did not detect a face.
            # No face detected — per request, continuously rotate RIGHT to search.
            # This keeps the robot scanning until a face appears.
            self.no_face_counter += 1  # Increment missing-face frame count.
            return 'R'  # Search by rotating right when no face is found.

        # Reset counters when face is detected  # Face found again.
        self.no_face_counter = 0  # Clear counter.
        self.last_face_time = time.time()  # Update last-seen timestamp.

        x, y, w, h = face_rect  # Unpack bounding box.
        face_center_x = x + w // 2  # Compute face center x.
        face_center_y = y + h // 2  # Compute face center y (currently not used in command).
        face_area = w * h  # Compute face area (proxy for distance).

        # Add to history for smoothing  # Keep last few measurements.
        self.face_positions.append((face_center_x, face_center_y, face_area))  # Push tuple.

        # Calculate average from history  # Smooth by simple mean.
        if len(self.face_positions) > 0:  # If there is history (always true after append).
            avg_x = int(sum(pos[0] for pos in self.face_positions) / len(self.face_positions))  # Mean x.
            _avg_y = int(sum(pos[1] for pos in self.face_positions) / len(self.face_positions))  # Mean y (kept for completeness).
            avg_area = int(sum(pos[2] for pos in self.face_positions) / len(self.face_positions))  # Mean area.
        else:  # Defensive fallback.
            avg_x, _avg_y, avg_area = face_center_x, face_center_y, face_area  # Use current values.

        # Calculate horizontal offset from center  # Left/right error for turning.
        offset_x = avg_x - self.center_x  # Positive means face is to the right.

        # Decision logic (commands restricted to F/L/R/S):
        # - If face is "too close" (area above max threshold) => Stop 'S'.
        # - Else, if face is left/right beyond dead-zone => Turn 'L' or 'R'.
        # - Else (face detected and roughly centered) => Move forward 'F'.
        if avg_area > self.max_face_size:  # Face too close → stop.
            return 'S'
        if abs(offset_x) >= self.dead_zone:  # Face not centered → turn toward it.
            return 'L' if offset_x < 0 else 'R'
        return 'F'  # Face detected and centered enough → advance.

    def send_to_arduino(self, command):  # Send command over serial or simulate.
        """Send command to Arduino"""  # Docstring.
        allowed = {'F', 'L', 'R', 'S'}  # Only these commands are permitted to be sent.
        if command not in allowed:  # If command is outside allowed set, do nothing.
            return False  # Silently ignore disallowed commands.
        if not self.simulation_mode and self.arduino and self.movement_enabled:  # Only send if real mode.
            try:  # Serial write might fail.
                self.arduino.write(command.encode())  # Convert string to bytes and send.
                return True  # Report success.
            except Exception as e:  # Handle serial errors.
                print(f"✗ Error sending to Arduino: {e}")  # Print why it failed.
                return False  # Report failure.
        elif self.simulation_mode:  # In simulation we don't send serial.
            cmd_names = {'F': 'FORWARD', 'L': 'LEFT', 'R': 'RIGHT', 'S': 'STOP'}  # Human names (filtered to allowed).
            print(f"[SIM] Command: {cmd_names.get(command, command)}")  # Print simulated movement.
            return True  # Simulation always "succeeds".
        return False  # Movement disabled or missing serial connection.

    def draw_interface(self, frame, face_rect, command):  # Overlay UI on frame.
        """Draw tracking interface on frame"""  # Docstring.
        cv2.line(frame, (self.center_x, 0), (self.center_x, self.frame_height), (0, 255, 0), 1)  # Draw vertical center.
        cv2.line(frame, (0, self.center_y), (self.frame_width, self.center_y), (0, 255, 0), 1)  # Draw horizontal center.

        cv2.rectangle(frame, (self.center_x - self.dead_zone, 0), (self.center_x + self.dead_zone, self.frame_height), (0, 100, 0), 1)  # Dead-zone box.

        if face_rect:  # If we have a detected face.
            x, y, w, h = face_rect  # Unpack face rectangle.
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw face bounding box.

            face_center_x = x + w // 2  # Face center x.
            face_center_y = y + h // 2  # Face center y.
            cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 255), -1)  # Draw center dot.

            cv2.line(frame, (self.center_x, self.center_y), (face_center_x, face_center_y), (0, 255, 255), 2)  # Draw vector line.

            face_area = w * h  # Compute face area.
            cv2.putText(frame, f"Area: {face_area}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)  # Show area.

            if face_area < self.min_face_size:  # Face too far.
                color = (0, 255, 255)  # Yellow.
                status = "TOO FAR"  # Text label.
            elif face_area > self.max_face_size:  # Face too close.
                color = (0, 0, 255)  # Red.
                status = "TOO CLOSE"  # Text label.
            else:  # Face within distance bounds.
                color = (0, 255, 0)  # Green.
                status = "GOOD"  # Text label.

            cv2.putText(frame, f"Distance: {status}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)  # Show status.
        else:  # No face.
            cv2.putText(frame, "NO FACE DETECTED", (self.center_x - 100, self.center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)  # Red warning.

        status_color = (0, 255, 0) if self.movement_enabled else (0, 0, 255)  # Green if enabled else red.
        status_text = "ACTIVE" if self.movement_enabled else "PAUSED"  # Human status.
        cv2.putText(frame, f"Status: {status_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)  # Draw status.

        cmd_names = {'F': 'FORWARD', 'B': 'BACKWARD', 'L': 'LEFT', 'R': 'RIGHT', 'S': 'STOP', 'C': 'CENTER'}  # Display map.
        cmd_text = cmd_names.get(command, 'SEARCHING')  # Convert command letter to text.
        cmd_color = (0, 255, 0) if command == 'S' else (0, 255, 255)  # Color STOP green else yellow.
        cv2.putText(frame, f"Command: {cmd_text}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)  # Draw command.

        mode_text = "SIMULATION" if self.simulation_mode else "ROBOT CONTROL"  # Display mode.
        cv2.putText(frame, f"Mode: {mode_text}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)  # Draw mode.

        if self.no_face_counter > 0:  # Only show if we have missed face frames.
            cv2.putText(frame, f"No face: {self.no_face_counter} frames", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)  # Draw count.

        cv2.putText(frame, "Press 'q': Quit", (10, self.frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)  # Instructions simplified.

        return frame  # Return the modified frame.

    # manual_control_mode removed: per request we only send auto F/L/R/S based on detection.

    def run(self):  # Automatic tracking loop.
        """Main tracking loop"""  # Docstring.
        print("Starting face tracking...")  # Startup message.

        # Per request: do NOT send initial STOP; start in passive state and only send F/L/R/S from detection.

        while True:  # Main capture loop.
            ret, frame = self.cap.read()  # Read one frame from camera.
            if not ret:  # If reading failed.
                print("✗ Error: Could not read frame!")  # Print error.
                break  # Leave loop.

            frame = cv2.flip(frame, 1)  # Mirror horizontally for user-friendly view.

            face_rect = self.detect_face(frame)  # Detect face in current frame.

            command = self.calculate_movement_command(face_rect)  # Decide movement command.

            if command != self.last_command or self.command_count % 5 == 0:  # Reduce serial spam.
                self.send_to_arduino(command)  # Send command.
                self.last_command = command  # Remember last command.

            self.command_count += 1  # Increment counter.

            frame = self.draw_interface(frame, face_rect, command)  # Draw overlays.

            cv2.imshow("Face Tracking Robot", frame)  # Show window.

            key = cv2.waitKey(1) & 0xFF  # Read key.

            if key == ord('q'):  # Quit.
                print("\nShutting down...")  # Tell user.
                break  # Exit loop.
            # Per request: only support quitting; no toggles or extra commands.

        self.cleanup()  # Cleanup resources.

    def cleanup(self):  # Clean up camera and serial.
        """Cleanup resources"""  # Docstring.
        print("\nCleaning up...")  # Notify user.

        if not self.simulation_mode and self.arduino:  # If we have a real Arduino connection.
            self.arduino.write(b'S')  # Send stop byte.
            time.sleep(0.1)  # Give it time.
            self.arduino.close()  # Close serial port.

        self.cap.release()  # Release camera.
        cv2.destroyAllWindows()  # Close OpenCV windows.

        print("✓ Cleanup complete")  # Done.
        print("Goodbye!")  # Final message.


def find_arduino_port():  # Helper to guess Arduino port.
    """Try to automatically find Arduino port"""  # Docstring.
    import platform  # Imported inside function to keep global imports unchanged.
    system = platform.system()  # Get OS name string.

    if system == "Windows":  # Windows uses COM ports.
        ports = [f"COM{i}" for i in range(1, 10)]  # Try COM1..COM9.
    elif system == "Linux":  # Common Linux serial device paths.
        ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]  # Candidate ports.
    elif system == "Darwin":  # macOS.
        ports = ["/dev/tty.usbmodem", "/dev/tty.usbserial"]  # Candidate prefixes.
    else:  # Unknown OS.
        ports = []  # No guesses.

    for port in ports:  # Try each candidate.
        try:  # Opening might fail.
            ser = serial.Serial(port, 115200, timeout=1)  # Attempt to open.
            ser.close()  # Close immediately if successful.
            return port  # Return the first working port.
        except Exception:  # Ignore and keep trying other ports.
            continue  # Next port.

    return None  # No port detected.


def main():  # Script entry point.
    """Main function"""  # Docstring.
    print("="*60)  # Divider.
    print("FACE TRACKING ROBOT - FIXED VERSION")  # Title.
    print("Robot STOPS when no face detected")  # Behavior reminder.
    print("="*60)  # Divider.

    arduino_port = find_arduino_port()  # Try to auto-detect Arduino port.

    if arduino_port:  # If we found something.
        print(f"Auto-detected Arduino on: {arduino_port}")  # Inform user.
        use_port = input(f"Use this port? (y/n): ").lower().strip()  # Ask for confirmation.
        if use_port != 'y':  # If user says no.
            arduino_port = input("Enter Arduino port (or press Enter for simulation): ").strip()  # Ask for manual port.
            if arduino_port == "":  # If user pressed Enter.
                arduino_port = None  # Use simulation.
    else:  # Nothing auto-detected.
        print("Could not auto-detect Arduino")  # Inform user.
        arduino_port = input("Enter Arduino port (or press Enter for simulation): ").strip()  # Ask.
        if arduino_port == "":  # If empty.
            arduino_port = None  # Use simulation.

    camera_id = input("Enter camera ID (0 for default, 1 for external): ").strip()  # Ask user for camera index.
    try:  # Conversion might fail.
        camera_id = int(camera_id)  # Convert to int.
    except Exception:  # If user typed non-number.
        camera_id = 0  # Default to 0.

    robot = FaceTrackingRobot(arduino_port=arduino_port, camera_id=camera_id)  # Create the controller.
    robot.run()  # Run until user quits.


if __name__ == "__main__":  # Standard Python entry check.
    main()  # Call main.