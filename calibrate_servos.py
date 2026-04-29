import argparse
import belay
import time
import sys
import tty
import termios

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Pico serial port")
    args = parser.parse_args()

    device = belay.Device(args.port)

    device(
    """
    from lib.servo import Servo
    """
    )

    Servo = device.proxy("Servo")

    @device.setup
    def setup_servolimits():
        servo_limits = {
            "TL": (80, 180),  "BL": (0,100),
            "TR": (0,100),   "BR": (100, 170),
            "UD": (30, 150),
            "LR": (30, 150),
        }

    setup_servolimits()

    servo_limits = device.proxy("servo_limits")

    @device.task
    def set_eyelids(l_top, l_bottom, r_top, r_bottom):
        Servo(pin_id=12).write(max(min(l_top, servo_limits["TL"][1]), servo_limits["TL"][0]))
        Servo(pin_id=13).write(max(min(l_bottom, servo_limits["BL"][0]), servo_limits["BL"][1]))
        Servo(pin_id=14).write(max(min(r_top, servo_limits["TR"][1]), servo_limits["TR"][0]))
        Servo(pin_id=15).write(max(min(r_bottom, servo_limits["BR"][0]), servo_limits["BR"][1]))

    @device.task
    def set_eye_position(lr, ud):
        Servo(pin_id=10).write(max(min(lr, servo_limits["LR"][1]), servo_limits["LR"][0]))
        Servo(pin_id=11).write(max(min(ud, servo_limits["UD"][1]), servo_limits["UD"][0]))

    print("Keyboard Control: w/a/s/d for UD/LR, q/e for top eyelids, z/c for bottom eyelids, r/f for right eyelids")
    print("Press 'x' to exit.")

    lr, ud = 90, 90
    l_top, l_bottom, r_top, r_bottom = 90, 90, 90, 90

    while True:
        char = getch()

        if char == 'x':
            break
        elif char == 'w':
            ud = min(ud + 5, servo_limits["UD"][1])
        elif char == 's':
            ud = max(ud - 5, servo_limits["UD"][0])
        elif char == 'a':
            lr = max(lr - 5, servo_limits["LR"][0])
        elif char == 'd':
            lr = min(lr + 5, servo_limits["LR"][1])
        elif char == 'q':
            l_top = min(l_top + 5, servo_limits["TL"][1])
        elif char == 'e':
            l_top = max(l_top - 5, servo_limits["TL"][0])
        elif char == 'z':
            l_bottom = min(l_bottom + 5, servo_limits["BL"][1])
        elif char == 'c':
            l_bottom = max(l_bottom - 5, servo_limits["BL"][0])
        elif char == 'r':
            r_top = min(r_top + 5, servo_limits["TR"][1])
        elif char == 'f':
            r_top = max(r_top - 5, servo_limits["TR"][0])
        elif char == 'v':
            r_bottom = min(r_bottom + 5, servo_limits["BR"][1])
        elif char == 'b':
            r_bottom = max(r_bottom - 5, servo_limits["BR"][0])

        set_eye_position(lr, ud)
        set_eyelids(l_top, l_bottom, r_top, r_bottom)
        print(f"LR: {lr}, UD: {ud}, TL: {l_top}, BL: {l_bottom}, TR: {r_top}, BR: {r_bottom}")

if __name__ == "__main__":
    main()
