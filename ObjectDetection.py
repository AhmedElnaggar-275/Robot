#!/usr/bin/env python3
"""
Face Tracking Robot Controller - FIXED VERSION
Stops when no face detected
"""

import cv2
import serial
import time
import numpy as np
from collections import deque
import threading
import sys
import os

class FaceTrackingRobot:
    def __init__(self, arduino_port=None, camera_id=0):
        """
        Initialize face tracking robot
        If arduino_port is None, runs in simulation mode
        """
        # Arduino connection
        self.arduino = None
        self.simulation_mode = False
        
        if arduino_port:
            try:
                self.arduino = serial.Serial(arduino_port, 115200, timeout=1)
                time.sleep(2)  # Wait for Arduino
                print(f"✓ Connected to Arduino on {arduino_port}")
            except Exception as e:
                print(f"✗ Could not connect to Arduino: {e}")
                print("Running in SIMULATION MODE (no robot movement)")
                self.simulation_mode = True
        else:
            print("Running in SIMULATION MODE (no robot movement)")
            self.simulation_mode = True
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            print("✗ Error: Could not open camera!")
            sys.exit(1)
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Load face detection model (Haar Cascade - built into OpenCV)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        if self.face_cascade.empty():
            print("✗ Error: Could not load face detection model!")
            sys.exit(1)
        
        print("✓ Face detection model loaded")
        
        # Tracking parameters
        self.frame_width = 640
        self.frame_height = 480
        self.center_x = self.frame_width // 2
        self.center_y = self.frame_height // 2
        
        # Control parameters - ADJUST THESE FOR YOUR ROBOT
        self.dead_zone = 80  # Center area where robot doesn't turn
        self.min_face_size = 15000  # Minimum pixels to move forward (adjust based on distance)
        self.max_face_size = 60000  # Maximum pixels before stopping (face too close)
        
        # Search parameters
        self.no_face_counter = 0
        self.search_direction = 'L'
        self.last_face_time = time.time()
        self.search_timeout = 2.0  # Seconds before starting search
        
        # Face position history for smoothing
        self.face_positions = deque(maxlen=5)
        
        # Movement control
        self.movement_enabled = True
        self.last_command = None
        self.command_count = 0
        
        print("\n" + "="*50)
        print("FACE TRACKING ROBOT CONTROLS - FIXED")
        print("="*50)
        print("When NO FACE detected: Robot STOPS")
        print("Press 'q' to quit")
        print("Press 's' to toggle movement on/off")
        print("Press 'm' for manual control mode")
        print("="*50 + "\n")
    
    def detect_face(self, frame):
        """Detect faces in frame using Haar Cascade"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast for better detection
        gray = cv2.equalizeHist(gray)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=6,  # Increased for fewer false positives
            minSize=(80, 80),  # Increased minimum size
            maxSize=(400, 400),  # Maximum face size
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            return None
        
        # Get the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        return (x, y, w, h)
    
    def calculate_movement_command(self, face_rect):
        """Calculate movement command based on face position"""
        if face_rect is None:
            # No face detected - STOP instead of turning
            self.no_face_counter += 1
            
            # Option: Search mode after timeout (uncomment if you want search)
            # if time.time() - self.last_face_time > self.search_timeout:
            #     # Alternate search direction
            #     if self.no_face_counter % 20 == 0:
            #         self.search_direction = 'R' if self.search_direction == 'L' else 'L'
            #     return self.search_direction
            
            return 'S'  # STOP when no face detected
        
        # Reset counters when face is detected
        self.no_face_counter = 0
        self.last_face_time = time.time()
        
        x, y, w, h = face_rect
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        face_area = w * h
        
        # Add to history for smoothing
        self.face_positions.append((face_center_x, face_center_y, face_area))
        
        # Calculate average from history
        if len(self.face_positions) > 0:
            avg_x = int(sum(pos[0] for pos in self.face_positions) / len(self.face_positions))
            avg_y = int(sum(pos[1] for pos in self.face_positions) / len(self.face_positions))
            avg_area = int(sum(pos[2] for pos in self.face_positions) / len(self.face_positions))
        else:
            avg_x, avg_y, avg_area = face_center_x, face_center_y, face_area
        
        # Calculate horizontal offset from center
        offset_x = avg_x - self.center_x
        
        # Decision logic
        if avg_area < self.min_face_size:
            # Face too small (far away) - move forward
            return 'F'
        elif avg_area > self.max_face_size:
            # Face too large (too close) - stop or move backward
            return 'S'  # Changed from 'B' to 'S' for safety
        elif abs(offset_x) < self.dead_zone:
            # Face is centered - move forward
            return 'F'
        elif offset_x < -self.dead_zone:
            # Face is left of center - turn left
            return 'L'
        else:
            # Face is right of center - turn right
            return 'R'
    
    def send_to_arduino(self, command):
        """Send command to Arduino"""
        if not self.simulation_mode and self.arduino and self.movement_enabled:
            try:
                self.arduino.write(command.encode())
                return True
            except Exception as e:
                print(f"✗ Error sending to Arduino: {e}")
                return False
        elif self.simulation_mode:
            # Print simulated command
            cmd_names = {'F': 'FORWARD', 'B': 'BACKWARD', 'L': 'LEFT', 
                        'R': 'RIGHT', 'S': 'STOP', 'C': 'CENTER'}
            if command in cmd_names:
                print(f"[SIM] Command: {cmd_names[command]}")
            return True
        return False
    
    def draw_interface(self, frame, face_rect, command):
        """Draw tracking interface on frame"""
        # Draw center lines
        cv2.line(frame, (self.center_x, 0), (self.center_x, self.frame_height), 
                (0, 255, 0), 1)
        cv2.line(frame, (0, self.center_y), (self.frame_width, self.center_y), 
                (0, 255, 0), 1)
        
        # Draw dead zone
        cv2.rectangle(frame, 
                     (self.center_x - self.dead_zone, 0),
                     (self.center_x + self.dead_zone, self.frame_height),
                     (0, 100, 0), 1)
        
        # Draw face if detected
        if face_rect:
            x, y, w, h = face_rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Draw face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 255), -1)
            
            # Draw line from center to face
            cv2.line(frame, (self.center_x, self.center_y), 
                    (face_center_x, face_center_y), (0, 255, 255), 2)
            
            # Face area text
            face_area = w * h
            cv2.putText(frame, f"Area: {face_area}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Draw target zone
            if face_area < self.min_face_size:
                color = (0, 255, 255)  # Yellow - too far
                status = "TOO FAR"
            elif face_area > self.max_face_size:
                color = (0, 0, 255)  # Red - too close
                status = "TOO CLOSE"
            else:
                color = (0, 255, 0)  # Green - good distance
                status = "GOOD"
            
            cv2.putText(frame, f"Distance: {status}", (x, y - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            # Draw "NO FACE" text in center
            cv2.putText(frame, "NO FACE DETECTED", 
                       (self.center_x - 100, self.center_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Status text
        status_color = (0, 255, 0) if self.movement_enabled else (0, 0, 255)
        status_text = "ACTIVE" if self.movement_enabled else "PAUSED"
        
        cv2.putText(frame, f"Status: {status_text}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Command text
        cmd_names = {'F': 'FORWARD', 'B': 'BACKWARD', 'L': 'LEFT', 
                    'R': 'RIGHT', 'S': 'STOP', 'C': 'CENTER'}
        cmd_text = cmd_names.get(command, 'SEARCHING')
        cmd_color = (0, 255, 0) if command == 'S' else (0, 255, 255)
        
        cv2.putText(frame, f"Command: {cmd_text}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)
        
        # Mode text
        mode_text = "SIMULATION" if self.simulation_mode else "ROBOT CONTROL"
        cv2.putText(frame, f"Mode: {mode_text}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # No face counter
        if self.no_face_counter > 0:
            cv2.putText(frame, f"No face: {self.no_face_counter} frames", 
                       (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Instructions
        cv2.putText(frame, "Press 'q': Quit | 's': Toggle | 'm': Manual", 
                   (10, self.frame_height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def manual_control_mode(self):
        """Manual control mode using keyboard"""
        print("\n" + "="*50)
        print("MANUAL CONTROL MODE")
        print("="*50)
        print("Use keys to control robot:")
        print("  W - Move Forward")
        print("  S - Move Backward")
        print("  A - Turn Left")
        print("  D - Turn Right")
        print("  Space - Stop")
        print("  C - Center")
        print("  X - Emergency Stop")
        print("  Q - Return to Auto Mode")
        print("="*50)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('w'):
                self.send_to_arduino('F')
                print("Command: FORWARD")
            elif key == ord('s'):
                self.send_to_arduino('B')
                print("Command: BACKWARD")
            elif key == ord('a'):
                self.send_to_arduino('L')
                print("Command: LEFT")
            elif key == ord('d'):
                self.send_to_arduino('R')
                print("Command: RIGHT")
            elif key == ord(' '):
                self.send_to_arduino('S')
                print("Command: STOP")
            elif key == ord('c'):
                self.send_to_arduino('C')
                print("Command: CENTER")
            elif key == ord('x'):
                self.send_to_arduino('X')
                print("Command: EMERGENCY STOP")
            elif key == ord('q'):
                print("Returning to Auto Mode...")
                return
            
            # Display manual control image
            blank = np.zeros((200, 600, 3), dtype=np.uint8)
            cv2.putText(blank, "MANUAL CONTROL MODE", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(blank, "Press Q to return to auto mode", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            cv2.putText(blank, "WASD to move, Space to stop", (50, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            cv2.imshow("Face Tracking Robot", blank)
    
    def run(self):
        """Main tracking loop"""
        print("Starting face tracking...")
        
        # Send initial stop command
        self.send_to_arduino('S')
        
        while True:
            # Read frame from camera
            ret, frame = self.cap.read()
            if not ret:
                print("✗ Error: Could not read frame!")
                break
            
            # Flip frame horizontally (mirror view)
            frame = cv2.flip(frame, 1)
            
            # Detect face
            face_rect = self.detect_face(frame)
            
            # Calculate movement command
            command = self.calculate_movement_command(face_rect)
            
            # Send command to Arduino
            if command != self.last_command or self.command_count % 5 == 0:
                self.send_to_arduino(command)
                self.last_command = command
            
            self.command_count += 1
            
            # Draw interface
            frame = self.draw_interface(frame, face_rect, command)
            
            # Show frame
            cv2.imshow("Face Tracking Robot", frame)
            
            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nShutting down...")
                break
            elif key == ord('s'):
                self.movement_enabled = not self.movement_enabled
                if not self.movement_enabled:
                    self.send_to_arduino('S')
                status = "ENABLED" if self.movement_enabled else "DISABLED"
                print(f"Movement {status}")
            elif key == ord('m'):
                self.manual_control_mode()
            elif key == ord('c'):
                self.send_to_arduino('C')
            elif key == ord('x'):
                self.send_to_arduino('X')
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        
        # Send stop command
        if not self.simulation_mode and self.arduino:
            self.arduino.write(b'S')
            time.sleep(0.1)
            self.arduino.close()
        
        # Release camera
        self.cap.release()
        cv2.destroyAllWindows()
        
        print("✓ Cleanup complete")
        print("Goodbye!")


def find_arduino_port():
    """Try to automatically find Arduino port"""
    import platform
    system = platform.system()
    
    if system == "Windows":
        ports = [f"COM{i}" for i in range(1, 10)]
    elif system == "Linux":
        ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]
    elif system == "Darwin":  # macOS
        ports = ["/dev/tty.usbmodem", "/dev/tty.usbserial"]
    else:
        ports = []
    
    for port in ports:
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.close()
            return port
        except:
            continue
    
    return None


def main():
    """Main function"""
    print("="*60)
    print("FACE TRACKING ROBOT - FIXED VERSION")
    print("Robot STOPS when no face detected")
    print("="*60)
    
    # Try to find Arduino automatically
    arduino_port = find_arduino_port()
    
    if arduino_port:
        print(f"Auto-detected Arduino on: {arduino_port}")
        use_port = input(f"Use this port? (y/n): ").lower().strip()
        if use_port != 'y':
            arduino_port = input("Enter Arduino port (or press Enter for simulation): ").strip()
            if arduino_port == "":
                arduino_port = None
    else:
        print("Could not auto-detect Arduino")
        arduino_port = input("Enter Arduino port (or press Enter for simulation): ").strip()
        if arduino_port == "":
            arduino_port = None
    
    # Camera selection
    camera_id = input("Enter camera ID (0 for default, 1 for external): ").strip()
    try:
        camera_id = int(camera_id)
    except:
        camera_id = 0
    
    # Create and run robot
    robot = FaceTrackingRobot(arduino_port=arduino_port, camera_id=camera_id)
    robot.run()


if __name__ == "__main__":
    main()