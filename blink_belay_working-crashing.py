import argparse
import belay
import math
from pupil_labs.realtime_api.simple import discover_one_device, Device
import time
import numpy as np

def norm(pos):
    return pos * (180/np.pi)

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", default="/dev/ttyACM0", help="Pico serial port")
    args = parser.parse_args()

    # Initialize hardware
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
            "TL": (80, 175),  # close, open
            "BL": (90, 10),   # close, open
            "TR": (95, 5),    # close, open
            "BR": (90, 90),    # close, open
            "UD": (70, 150),  # bottommost, topmost
            "LR": (60, 120),  # rightmost, leftmost
        }

    setup_servolimits()

    @device.task
    def set_eyelids(l_top, l_bottom, r_top, r_bottom):
        Servo(pin_id=12).write(max(min(l_top, servo_limits["TL"][1]), servo_limits["TL"][0]))
        Servo(pin_id=13).write(max(min(l_bottom, servo_limits["BL"][0]), servo_limits["BL"][1]))
        Servo(pin_id=14).write(max(min(r_top, servo_limits["TR"][0]), servo_limits["TR"][1]))
        Servo(pin_id=15).write(max(min(r_top, servo_limits["BR"][1]), servo_limits["BR"][0]))

    @device.task
    def set_eye_position(lr, ud):
        Servo(pin_id=10).write(max(min(lr, servo_limits["LR"][1]), servo_limits["LR"][0]))
        Servo(pin_id=11).write(max(min(ud, servo_limits["UD"][1]), servo_limits["UD"][0]))

    # Connect to eye tracker
    print("Looking for Pupil Labs device...")
    tracker = discover_one_device(max_search_duration_seconds=1)

    if not tracker:
        tracker = Device(address="192.168.1.181", port="8080")
        if not tracker:
            raise RuntimeError("No eye tracker found")

    print(f"Connected to {tracker}")
    print("Streaming eye data...")
    last_lr, last_ud = None, None
    last_time = time.time()
    try:
        while True:
            gaze = tracker.receive_gaze_datum()

            # Map blink angles to servo ranges
            TL = map_value((gaze.eyelid_angle_top_left), -0.6, 0.9, 80, 175)
            BL = map_value((gaze.eyelid_angle_bottom_left), -1, -0.2, 10, 90)
            TR = map_value((gaze.eyelid_angle_top_right), -1.15, 1.05, 95, 5)
            BR = map_value((gaze.eyelid_angle_bottom_right), -1.15, 1.05, 90, 90) # NOT CALIBRATED


            # Map optical axis to servo angles
            lr_avg = map_value((norm(gaze.optical_axis_left_x) + norm(gaze.optical_axis_right_x)) / 2, -37.72, 44.73, 60, 120)
            ud_avg = map_value((norm(gaze.optical_axis_left_y) + norm(gaze.optical_axis_right_y)) / 2, -38.33, 36.94, 150, 70)

            now = time.time()
            if (last_lr is None or
                abs(lr_avg - last_lr) > 1 or
                abs(ud_avg - last_ud) > 1 or
                (now - last_time) > 0.05):  # 50ms minimum update interval
                print(TL,BL,TR,lr_avg,ud_avg)
                set_eyelids(TL, BL, TR, 90)
                time.sleep(0.01)
                set_eye_position(lr_avg, ud_avg)
                last_lr, last_ud = lr_avg, ud_avg
                last_time = now
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
