import argparse
import belay
import math
from pupil_labs.realtime_api.simple import discover_one_device, Device
import time
import numpy as np
from collections import deque

def norm(pos):
    return pos * (180/np.pi)

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Pico serial port")
    args = parser.parse_args()

    device = belay.Device(args.port)

    device("""
    from lib.servo import Servo
    from machine import Pin
    mode_switch = Pin(7, Pin.IN, Pin.PULL_UP)
    def get_mode(): return mode_switch.value() # 0 = Delay, 1 = Direct
    """)

    Servo = device.proxy("Servo")
    get_mode = device.proxy("get_mode")

    @device.setup
    def setup_servolimits():
        global servo_limits
        servo_limits = {
            "TL": (80, 175), "BL": (90, 10), "TR": (95, 5),
            "BR": (90, 90), "UD": (70, 150), "LR": (60, 120),
        }

    setup_servolimits()

    @device.task
    def set_eyelids(l_top, l_bottom, r_top, r_bottom):
        wait_time = 0.02
        Servo(pin_id=12).write(max(min(l_top, servo_limits["TL"][1]), servo_limits["TL"][0]))
        time.sleep(wait_time)
        Servo(pin_id=13).write(max(min(l_bottom, servo_limits["BL"][0]), servo_limits["BL"][1]))
        time.sleep(wait_time)
        Servo(pin_id=14).write(max(min(r_top, servo_limits["TR"][0]), servo_limits["TR"][1]))
        time.sleep(wait_time)
        Servo(pin_id=15).write(max(min(r_top, servo_limits["BR"][1]), servo_limits["BR"][0]))
        time.sleep(wait_time)

    @device.task
    def set_eye_position(lr, ud):
        Servo(pin_id=10).write(max(min(lr, servo_limits["LR"][1]), servo_limits["LR"][0]))
        time.sleep(0.02)
        Servo(pin_id=11).write(max(min(ud, servo_limits["UD"][1]), servo_limits["UD"][0]))
        time.sleep(0.02)

    tracker = discover_one_device(max_search_duration_seconds=1)
    if not tracker:
        tracker = Device(address="192.168.1.181", port="8080")
        if not tracker: raise RuntimeError("No eye tracker found")

    print(f"Connected to {tracker}")
    
    eye_buffer = deque()
    last_lr, last_ud = None, None
    last_time = time.time()

    try:
        while True:
            gaze = tracker.receive_gaze_datum()

            TL = map_value((gaze.eyelid_angle_top_left), -0.6, 0.9, 80, 175)
            BL = map_value((gaze.eyelid_angle_bottom_left), -1, -0.2, 10, 90)
            TR = map_value((gaze.eyelid_angle_top_right), -1.15, 1.05, 95, 5)
            
            lr_avg = map_value((norm(gaze.optical_axis_left_x) + norm(gaze.optical_axis_right_x)) / 2, -37.72, 44.73, 60, 120)
            ud_avg = map_value((norm(gaze.optical_axis_left_y) + norm(gaze.optical_axis_right_y)) / 2, -38.33, 36.94, 150, 70)

            now = time.time()
            
            if get_mode() == 0: # DELAY MODE
                eye_buffer.append((now, TL, BL, TR, lr_avg, ud_avg))
                if eye_buffer and (now - eye_buffer[0][0] >= 0.5):
                    _, b_TL, b_BL, b_TR, b_lr, b_ud = eye_buffer.popleft()
                    set_eyelids(b_TL, b_BL, b_TR, 90)
                    set_eye_position(b_lr, b_ud)
                    last_lr, last_ud = b_lr, b_ud
            else: # DIRECT MODE
                eye_buffer.clear()
                if (last_lr is None or abs(lr_avg - last_lr) > 1 or abs(ud_avg - last_ud) > 1 or (now - last_time) > 0.05):
                    set_eyelids(TL, BL, TR, 90)
                    set_eye_position(lr_avg, ud_avg)
                    last_lr, last_ud = lr_avg, ud_avg
                    last_time = now
            
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        tracker.close()

if __name__ == "__main__":
    main()