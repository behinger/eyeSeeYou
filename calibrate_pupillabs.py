import argparse
from pupil_labs.realtime_api.simple import discover_one_device, Device
import time

def norm(pos):
    return pos * (180/3.14159265359)

def main():
    print("Looking for Pupil Labs device...")
    tracker = discover_one_device(max_search_duration_seconds=1)

    if not tracker:
        tracker = Device(address="192.168.1.181", port="8080")
        if not tracker:
            raise RuntimeError("No eye tracker found")

    print(f"Connected to {tracker}")
    print("Measuring extremas. Look as far left, right, up, down, and blink as possible.")
    print("Press Ctrl+C to stop and see the results.")

    min_lr = float('inf')
    max_lr = float('-inf')
    min_ud = float('inf')
    max_ud = float('-inf')
    min_blink_l = float('inf')
    max_blink_l = float('-inf')
    min_blink_r = float('inf')
    max_blink_r = float('-inf')

    try:
        while True:
            gaze = tracker.receive_gaze_datum()

            lr_avg = norm(gaze.optical_axis_left_x + gaze.optical_axis_right_x) / 2
            ud_avg = norm(gaze.optical_axis_left_y + gaze.optical_axis_right_y) / 2

            min_lr = min(min_lr, lr_avg)
            max_lr = max(max_lr, lr_avg)
            min_ud = min(min_ud, ud_avg)
            max_ud = max(max_ud, ud_avg)

            min_blink_l = min(min_blink_l, gaze.eyelid_angle_top_left, gaze.eyelid_angle_bottom_left)
            max_blink_l = max(max_blink_l, gaze.eyelid_angle_top_left, gaze.eyelid_angle_bottom_left)
            min_blink_r = min(min_blink_r, gaze.eyelid_angle_top_right, gaze.eyelid_angle_bottom_right)
            max_blink_r = max(max_blink_r, gaze.eyelid_angle_top_right, gaze.eyelid_angle_bottom_right)

            print(f"LR: {lr_avg:.2f}, UD: {ud_avg:.2f}, Blink L: {gaze.eyelid_angle_top_left:.2f}/{gaze.eyelid_angle_bottom_left:.2f}, Blink R: {gaze.eyelid_angle_top_right:.2f}/{gaze.eyelid_angle_bottom_right:.2f}")

    except KeyboardInterrupt:
        print("\nExtremas:")
        print(f"Left/Right: min={min_lr:.2f}, max={max_lr:.2f}")
        print(f"Up/Down: min={min_ud:.2f}, max={max_ud:.2f}")
        print(f"Blink Left: min={min_blink_l:.2f}, max={max_blink_l:.2f}")
        print(f"Blink Right: min={min_blink_r:.2f}, max={max_blink_r:.2f}")
    finally:
        tracker.close()

if __name__ == "__main__":
    main()
