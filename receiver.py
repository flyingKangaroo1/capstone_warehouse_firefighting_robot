import socket
import json

# --- Configuration ---
UDP_IP = "0.0.0.0"  # Listen on all interfaces (including Tailscale)
UDP_PORT = 6000     # The NEW control data port
BUFFER_SIZE = 4096  # Increased buffer size for potentially large JSON messages

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Raspberry Pi listening for YOLO data on UDP port {UDP_PORT}...")

    while True:
        try:
            # Wait for data from the PC
            data, addr = sock.recvfrom(BUFFER_SIZE) 
            
            # Decode and parse the JSON message
            message = data.decode('utf-8')
            detections = json.loads(message)
            
            # --- PROCESS RECEIVED DATA ---
            if detections:
                print(f"Received {len(detections)} objects from PC ({addr[0]}):")
                
                for det in detections:
                    label = det['label']
                    center = det['center']
                    confidence = det['confidence']
                    
                    # Example: Log the data for the 'fire' class
                    if label == "fire":
                        center_x, center_y = center
                        print(f"Detected {label}. Center: {center}, Confidence: {confidence}")
                        
                        # **IMPLEMENT YOUR ROBOT CONTROL LOGIC HERE**
                        # Example: if center_x is too far right, move motors left.
                        
                    # Add logic for other classes (e.g., 'fire_extinguisher')

            # else: print("No objects detected in this frame.")

        except json.JSONDecodeError:
            print("Warning: Received invalid JSON data.")
        except KeyboardInterrupt:
            print("Stopping receiver.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

if __name__ == "__main__":
    main()
