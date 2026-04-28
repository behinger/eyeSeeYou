import argparse
import belay
from pupil_labs.realtime_api.simple import discover_one_device
import time

# Argument parsing
parser = argparse.ArgumentParser(description="Animatronic Eye Controller with Blink Detection")
parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Serial port of the Pico")
args = parser.parse_args()

# Initialize belay connection
device = belay.Device(args.port)
print("Pico connected")

# Initialize hardware on Pico
device(
    """
from lib.servo import Servo
from machine import Pin
import time

# Servo setup
servos = {
    "TL": Servo(pin_id=12),  # Top Left eyelid
    "BL": Servo(pin_id=13),  # Bottom Left eyelid
    "TR": Servo(pin_id=14),  # Top Right eyelid
    "BR": Servo(pin_id=15),  # Bottom Right eyelid
}

# Servo limits (adjust to your mechanical setup)
servo_limits = {
    "TL": (90, 170),
    "BL": (90, 10),
    "TR": (90, 10),
    "BR": (90, 160),
}

def blink():
    '''Close and immediately reopen eyelids'''
    servos["TL"].write(servo_limits["TL"][0])
    servos["TR"].write(servo_limits["TR"][0])
    servos["BL"].write(servo_limits["BL"][0])
    servos["BR"].write(servo_limits["BR"][0])
    time.sleep(0.3)
    servos["TL"].write(servo_limits["TL"][1])
    servos["TR"].write(servo_limits["TR"][1])
    servos["BL"].write(servo_limits["BL"][1])
    servos["BR"].write(servo_limits["BR"][1])
"""
)

# Single remote function
@device.task
def blink_eye():
    """Trigger a blink"""
    blink()

def main():
    print("Looking for Pupil Labs eye tracker...")
    eye_tracker = discover_one_device(max_search_duration_seconds=10.0)

    if eye_tracker is None:
        print("No eye tracker found. Running in manual mode.")
        print("Press Ctrl+C to exit")
        try:
            while True:
                # In manual mode, just blink periodically
                blink_eye()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    else:
        print(f"Connected to {eye_tracker}")
        print("Listening for blink events...")

        # Subscribe to eye events
        eye_tracker.receive_eye_events(on_data=process_eye_event)

        # Keep the connection alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            eye_tracker.close()

def process_eye_event(eye_event):
    """Process incoming eye events and trigger animatronic blink when human blinks"""
    # Check if this is a blink event with sufficient confidence
    if eye_event.blink and eye_event.confidence > 0.6:  # Confidence threshold
        print(f"Human blink detected! Timestamp: {eye_event.timestamp_unix_seconds} s")
        print(f"  Eye: {eye_event.eye_id}, Confidence: {eye_event.confidence:.2f}")

        # Trigger animatronic blink
        blink_eye()
        print("  Animatronic blink triggered")

if __name__ == "__main__":
    main()