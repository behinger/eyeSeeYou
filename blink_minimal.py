import argparse
import belay

# Argument parsing
parser = argparse.ArgumentParser(description="Animatronic Eye Controller")
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

if __name__ == "__main__":
    print("Ready - Waiting for LSL blink signals")
    blink_eye()  # Initialize with one test blink