import argparse
import cv2
import numpy as np
import socket
import json
from ultralytics import YOLO

try:
    import torch
except ImportError:
    print("Warning: torch module not found.")
    torch = None

# --- Configuration ---
# IP of the Raspberry Pi (Receiver)
RASPBERRY_TAILSCALE_IP = "add your tailscale ip here"
RASPBERRY_PORT = 6000                 

# --- Grid Configuration ---
RECT_WIDTH = 640
RECT_HEIGHT = 480
BOTTOM_ROW_HEIGHT = 230 
SPLIT_Y = RECT_HEIGHT - BOTTOM_ROW_HEIGHT 
DEBUG = True

# --- YOLO Setup ---
CONFIDENCE_THRESHOLD = 0.3

if torch and torch.cuda.is_available():
    INFERENCE_DEVICE = 0
    print(f"YOLO will use GPU (Device: {INFERENCE_DEVICE}).")
else:
    INFERENCE_DEVICE = 'cpu'
    print("YOLO will use CPU.")

MODEL = YOLO('config/best.pt') 

# UDP Socket Setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def draw_grid_visuals(img):
    """Draws lines and labels for Spot/Level visualization."""
    h, w = img.shape[:2]
    color = (0, 255, 0)
    col_w = w // 3
    
    # Draw Vertical Lines (Columns)
    cv2.line(img, (col_w, 0), (col_w, h), color, 2)
    cv2.line(img, (col_w * 2, 0), (col_w * 2, h), color, 2)

    # Draw Horizontal Line (Split Level)
    cv2.line(img, (0, SPLIT_Y), (w, SPLIT_Y), color, 2)
    
    # Add Overlay Text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "S:3 L:2", (10, 30), font, 0.6, color, 2)
    cv2.putText(img, "S:2 L:2", (col_w + 10, 30), font, 0.6, color, 2)
    cv2.putText(img, "S:1 L:2", (col_w * 2 + 10, 30), font, 0.6, color, 2)
    cv2.putText(img, "S:3 L:1", (10, SPLIT_Y + 30), font, 0.6, color, 2)
    cv2.putText(img, "S:2 L:1", (col_w + 10, SPLIT_Y + 30), font, 0.6, color, 2)
    cv2.putText(img, "S:1 L:1", (col_w * 2 + 10, SPLIT_Y + 30), font, 0.6, color, 2)
    return img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="add your tailscale ip here", help="Jetson IP")
    parser.add_argument("--port", type=int, default=8081, help="Motion Port")
    args = parser.parse_args()

    stream_url = f"http://{args.host}:{args.port}"
    print(f"Connecting to: {stream_url}")

    cap = cv2.VideoCapture(stream_url, cv2.CAP_ANY)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open stream: {stream_url}")

    # --- Calibration Points ---
    src_pts = np.array([
        [80, 90],    # TL
        [610, 100],  # TR
        [580, 420],  # BR
        [100, 410]   # BL
    ], dtype=np.float32)

    dst_pts = np.array([
        [0, 0], 
        [RECT_WIDTH - 1, 0], 
        [RECT_WIDTH - 1, RECT_HEIGHT - 1], 
        [0, RECT_HEIGHT - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    col_width = RECT_WIDTH // 3

    print("Running... Press CTRL+C to stop.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame.")
                break

            # 1. Warp Perspective
            warped_frame = cv2.warpPerspective(frame, M, (RECT_WIDTH, RECT_HEIGHT))

            # 2. YOLO Inference
            results = MODEL(
                warped_frame, 
                verbose=False, 
                device=INFERENCE_DEVICE,
                conf=CONFIDENCE_THRESHOLD,          # 1. Raise Confidence 
                iou=0.1,           # 2. Lower IoU Threshold (Default is 0.7)
                agnostic_nms=True, # 3. Merge different classes
                max_det=6          # 4. Limit total detections
            )            

            detections_to_send = []

            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        if conf < CONFIDENCE_THRESHOLD:
                            continue

                        # Coordinates
                        coords = box.xyxy[0].tolist()
                        cx = int((coords[0] + coords[2]) / 2)
                        cy = int((coords[1] + coords[3]) / 2)
                        
                        # Logic
                        if cx < col_width: spot = 3
                        elif cx < col_width * 2: spot = 2
                        else: spot = 1

                        if cy < SPLIT_Y: level = 2
                        else: level = 1

                        # --- DATA FORMAT ---
                        detections_to_send.append({
                            "spot": spot,
                            "level": level
                        })

                        cv2.putText(warped_frame, f"S:{spot} L:{level}", (cx, cy - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            # 3. Send Data via UDP
            if True:
                try:
                    # Convert list to JSON string -> bytes
                    test_payload = {"spot": 1, "level": 1}
                
                    # Convert to JSON -> Encode to Bytes
                    msg = json.dumps(test_payload).encode('utf-8')
                    sock.sendto(msg, (RASPBERRY_TAILSCALE_IP, RASPBERRY_PORT))
                    print(f"Sent: {msg}") # Debug print
                except Exception as e:
                    print(f"UDP Send Error: {e}")

            # 4. Visualization
            visual_frame = draw_grid_visuals(warped_frame)
            for r in results:
                if r.boxes:
                    for box in r.boxes:
                        # 1. Get Coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # 2. Get Confidence
                        conf = float(box.conf[0])

                        # 3. Draw the Bounding Box (Blue)
                        cv2.rectangle(visual_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        
                        # 4. Create Label and put text above the top-left corner
                        label = f"{conf:.2f}"
                        
                        # Ensure text stays on screen even if box is at the very top edge
                        text_y = max(y1 - 10, 20) 
                        
                        cv2.putText(visual_frame, label, (x1, text_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            cv2.imshow("Rectified + Logic", visual_frame)
            
            if DEBUG:
                debug_frame = frame.copy()
                cv2.polylines(debug_frame, [src_pts.astype(np.int32)], True, (0, 0, 255), 2)
                cv2.imshow("Original Source ROI", debug_frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break
    
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()