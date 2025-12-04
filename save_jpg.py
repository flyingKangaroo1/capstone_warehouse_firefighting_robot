import argparse
import cv2
import numpy as np
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="add your tailscale ip here", help="Tailscale IP of the Jetson Nano")
    parser.add_argument("--port", type=int, default=8081, help="Stream port")
    args = parser.parse_args()
    stream_url = f"http://{args.host}:{args.port}"

    # --- Setup Output Directory & Smart Counter ---
    output_folder = "images"
    os.makedirs(output_folder, exist_ok=True)
    
    # Check existing files to determine start index
    existing_files = [f for f in os.listdir(output_folder) if f.startswith("image_") and f.endswith(".png")]
    indices = []
    for f in existing_files:
        try:
            # Extract the number part: "image_12.png" -> "12"
            num_part = f.replace("image_", "").replace(".png", "")
            indices.append(int(num_part))
        except ValueError:
            pass # Skip files that don't have a valid number

    # Start counter at max existing index + 1, or 0 if folder is empty
    img_counter = max(indices) + 1 if indices else 0
    print(f"Starting image counter at: {img_counter}")
    # ----------------------------------------------

    cap = cv2.VideoCapture(stream_url, cv2.CAP_ANY) 

    # Coordinates of quad in image (order: TL, TR, BR, BL)
    src_pts = np.array([[80,90], [610,100], [580,420], [100,410]], dtype=np.float32)

    width, height = 640, 480
    dst_pts = np.array([[0,0], [width-1,0], [width-1,height-1], [0,height-1]], dtype=np.float32)

    print(f"Stream opened.")
    print(f"Press [SPACE] to save to '{output_folder}/'.")
    print(f"Press [ESC] to exit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to grab frame or stream ended.")
            break

        # Perspective transform
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(frame, M, (width, height))
        
        cv2.imshow("Rectified", warped)

        # --- Key Handling ---
        key = cv2.waitKey(1) & 0xFF

        if key == 27: # ESC key to exit
            break
        elif key == 32: # SPACE key to save
            img_name = f"image_{img_counter}.png"
            path = os.path.join(output_folder, img_name)
            
            # Write the 'warped' image to disk
            cv2.imwrite(path, warped)
            print(f"Saved: {path}")
            
            # Visual Feedback
            cv2.putText(warped, f"SAVED #{img_counter}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Rectified", warped)
            cv2.waitKey(200) 
            
            img_counter += 1
        # --------------------

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()