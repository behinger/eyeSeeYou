import argparse
import belay
import time

# Argument parsing
parser = argparse.ArgumentParser(description="Animatronic Eye Controller")
parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Serial port of the Pico")
args = parser.parse_args()

# Initialize belay connection
device = belay.Device(args.port)  # Don't sync since servo is already on device
print("Connected to Pico via Belay")

# Initialize hardware and functions on the Pico
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

# Servo limits (adjust based on your mechanical setup)
servo_limits = {
    "TL": (90, 170),  # Min (closed), Max (open)
    "BL": (90, 10),   # Min (closed), Max (open) - reversed
    "TR": (90, 10),   # Min (closed), Max (open) - reversed
    "BR": (90, 160),  # Min (closed), Max (open)
}

# Onboard LED for debugging
led = Pin(25, Pin.OUT)

def blink():
    '''Close all eyelids (blink)'''
    led.on()
    servos["TL"].write(servo_limits["TL"][0])
    servos["TR"].write(servo_limits["TR"][0])
    servos["BL"].write(servo_limits["BL"][0])
    servos["BR"].write(servo_limits["BR"][0])
    time.sleep(0.1)
    led.off()

def open_lid():
    '''Open all eyelids to max position'''
    servos["TL"].write(servo_limits["TL"][1])
    servos["TR"].write(servo_limits["TR"][1])
    servos["BL"].write(servo_limits["BL"][1])
    servos["BR"].write(servo_limits["BR"][1])

def set_servo_limit(servo_name, min_angle, max_angle):
    '''Update limits for a specific servo'''
    servo_limits[servo_name] = (min_angle, max_angle)

def get_servo_limits():
    '''Return current servo limits'''
    return servo_limits
"""
)

# Define remote functions (execute on Pico)
@device.task
def initialize_eye():
    """Initialize eye to default open position"""
    open_lid()
    print("Eye initialized to open position")

@device.task
def blink_eye(duration_ms=100):
    """Trigger a blink with optional duration"""
    blink()
    time.sleep(duration_ms/1000)
    print(f"Blinked for {duration_ms}ms")

@device.task
def test_sequence(blinks=3, interval=200):
    """Run a test sequence of multiple blinks"""
    for i in range(blinks):
        blink()
        time.sleep(interval/1000)
        open_lid()
        time.sleep(interval/1000)
    print(f"Test sequence complete: {blinks} blinks at {interval}ms intervals")

@device.task
def calibrate_servo(servo, min_angle, max_angle):
    """Update servo calibration limits"""
    set_servo_limit(servo, min_angle, max_angle)
    print(f"Updated {servo} limits: {min_angle}-{max_angle}")

@device.task
def get_limits():
    """Get current servo limits"""
    limits = get_servo_limits()
    print("Current servo limits:")
    for servo, (min_lim, max_lim) in limits.items():
        print(f"{servo}: {min_lim}-{max_lim}")
    return limits

@device.task
def check_connection():
    """Verify connection to Pico"""
    led.on()
    time.sleep(0.1)
    led.off()
    return "Pico connection verified (LED blinked)"

# Main program
if __name__ == "__main__":
    print("\nAnimatronic Eye Controller")
    print("1. Initialize Eye")
    print("2. Blink Eye")
    print("3. Run Test Sequence")
    print("4. Calibrate Servo")
    print("5. Check Servo Limits")
    print("6. Verify Connection")
    print("7. Exit")

    initialize_eye()  # Auto-initialize on startup

    while True:
        try:
            choice = input("\nEnter choice (1-7): ").strip()

            if choice == "1":
                initialize_eye()
            elif choice == "2":
                duration = input("Enter blink duration (ms, default 100): ")
                blink_eye(100 if not duration else int(duration))
            elif choice == "3":
                blinks = int(input("Number of blinks (default 3): ") or 3)
                interval = int(input("Interval between blinks (ms, default 200): ") or 200)
                test_sequence(blinks, interval)
            elif choice == "4":
                servo = input("Servo to calibrate (TL/BL/TR/BR): ").upper()
                min_lim = int(input("Min angle: "))
                max_lim = int(input("Max angle: "))
                calibrate_servo(servo, min_lim, max_lim)
            elif choice == "5":
                get_limits()
            elif choice == "6":
                print(check_connection())
            elif choice == "7":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try 1-7.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print