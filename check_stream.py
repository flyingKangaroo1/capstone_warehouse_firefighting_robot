# receiver_motion.py (Run this on the Linux PC)

import argparse
import cv2

def main():
    parser = argparse.ArgumentParser()
    # The host is now the Jetson Nano's Tailscale IP
    parser.add_argument("--host", default="add your tailscale ip here", help="Tailscale IP of the Jetson Nano running Motion")
    parser.add_argument("--port", type=int, default=8081, help="Stream port set in motion.conf")
    args = parser.parse_args()

    # Construct the URL for the Motion MJPEG stream
    stream_url = f"http://{args.host}:{args.port}"
    print(f"Connecting to Motion stream at: {stream_url}")

    # Use CAP_ANY or CAP_FFMPEG to handle the HTTP URL stream
    # CAP_ANY lets OpenCV choose the best backend (usually FFMPEG)
    cap = cv2.VideoCapture(stream_url, cv2.CAP_ANY) 

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        print(f"Check: 1. Is Motion running on {args.host}? 2. Is Tailscale running on both devices?")
        return

    print("Stream opened successfully. Press ESC to exit.")

    while True:
        ok, frame = cap.read()
        
        if not ok:
            print("Failed to read frame or end of stream. Reconnecting...")
            # Attempt to reconnect if stream drops
            cap.release()
            cap = cv2.VideoCapture(stream_url, cv2.CAP_ANY)
            if not cap.isOpened():
                 break
            continue

        cv2.imshow("Jetson Nano Motion Stream", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()