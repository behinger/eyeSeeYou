import argparse
import belay
import pyautogui
from pynput import mouse
import time
import threading
from collections import deque

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

blink_requested = False

def on_click(x, y, button, pressed):
    global blink_requested
    if button == mouse.Button.left and pressed:
        blink_requested = True

def main():
    global blink_requested

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Pico serial port")
    args = parser.parse_args()

    device = belay.Device(args.port)
    device(
    """
    from lib.servo import Servo
    from machine import Pin
    mode_switch = Pin(7, Pin.IN, Pin.PULL_UP)
    def get_mode(): return mode_switch.value()
    """
    )
    Servo = device.proxy("Servo")
    get_mode = device.proxy("get_mode")

    @device.setup
    def setup_servolimits():
        global servo_limits
        servo_limits = {
            "TL": (80, 175),
            "BL": (90, 10),
            "TR": (95, 5),
            "BR": (90, 10),
            "UD": (70, 150),
            "LR": (60, 120),
        }

    setup_servolimits()

    @device.task
    def set_eyelids(l_top, l_bottom, r_top, r_bottom):
        Servo(pin_id=12).write(max(min(l_top, servo_limits["TL"][1]), servo_limits["TL"][0]))
        Servo(pin_id=13).write(max(min(l_bottom, servo_limits["BL"][0]), servo_limits["BL"][1]))
        Servo(pin_id=14).write(max(min(r_top, servo_limits["TR"][0]), servo_limits["TR"][1]))
        Servo(pin_id=15).write(max(min(r_bottom, servo_limits["BR"][1]), servo_limits["BR"][0]))

    @device.task
    def set_eye_position(lr, ud):
        Servo(pin_id=10).write(max(min(lr, servo_limits["LR"][1]), servo_limits["LR"][0]))
        Servo(pin_id=11).write(max(min(ud, servo_limits["UD"][1]), servo_limits["UD"][0]))

    @device.task
    def blink():
        wait_time = 0.02
        Servo(pin_id=12).write(servo_limits["TL"][0])
        time.sleep(wait_time)
        Servo(pin_id=14).write(servo_limits["TR"][0])
        time.sleep(wait_time)
        Servo(pin_id=13).write(servo_limits["BL"][0])
        time.sleep(0.2)
        
        Servo(pin_id=12).write(servo_limits["TL"][1])
        time.sleep(wait_time)
        Servo(pin_id=14).write(servo_limits["TR"][1])
        time.sleep(wait_time)
        Servo(pin_id=13).write(servo_limits["BL"][1])
        time.sleep(0.01)

    screen_width, screen_height = pyautogui.size()
    eye_buffer = deque()

    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    try:
        while True:
            x, y = pyautogui.position()
            lr = map_value(x, 0, screen_width, 60, 120)
            ud = map_value(y, 0, screen_height, 150, 70)

            # Check if delay mode is active (0 = Closed/Connected to GND)
            if get_mode() == 0:
                eye_buffer.append((time.time(), lr, ud))
                if eye_buffer and (time.time() - eye_buffer[0][0] >= 0.5):
                    _, buffered_lr, buffered_ud = eye_buffer.popleft()
                    set_eye_position(buffered_lr, buffered_ud)
            else:
                # Direct mode
                eye_buffer.clear()
                set_eye_position(lr, ud)

            if blink_requested:
                blink()
                blink_requested = False

            time.sleep(0.01)

    except KeyboardInterrupt:
        mouse_listener.stop()
    finally:
        mouse_listener.stop()

if __name__ == "__main__":
    main()