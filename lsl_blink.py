from pupil_labs.realtime_api.simple import discover_one_device
import time

def main():
    # Connect to the eye tracker
    print("Looking for Pupil Labs eye tracker...")
    device = discover_one_device(max_search_duration_seconds=10.0)
    if device is None:
        print("No device found.")
        return

    print(f"Connected to {device}")

    # Subscribe to eye events
    print("Subscribing to eye events...")
    device.receive_eye_events(on_data=process_eye_event)

    # Keep the connection alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        device.close()

def process_eye_event(eye_event):
    """Process incoming eye events and detect blinks"""
    # Check if this is a blink event
    if eye_event.blink:
        print(f"Blink detected! Timestamp: {eye_event.timestamp_unix_seconds} s")
        print(f"  Eye: {eye_event.eye_id}")
        print(f"  Confidence: {eye_event.confidence:.2f}")
        print("---")

if __name__ == "__main__":
    main()