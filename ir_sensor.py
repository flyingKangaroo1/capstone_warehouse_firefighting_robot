import RPi.GPIO as GPIO
import time

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define Sensor Pins
SENSOR_LEFT = 22
SENSOR_RIGHT = 23

# Set up pins as input
# We enable the internal pull-up resistor just in case, 
# though the sensor module usually drives the pin High/Low itself.
GPIO.setup(SENSOR_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SENSOR_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("--- IR Sensor Test (Press CTRL+C to stop) ---")
    print(f"Left Sensor connected to GPIO {SENSOR_LEFT}")
    print(f"Right Sensor connected to GPIO {SENSOR_RIGHT}")
    print("---------------------------------------------")

    while True:
        # Read sensor states
        # Usually: 
        # LOW (0) = Obstacle Detected / White Surface (Reflecting light)
        # HIGH (1) = No Obstacle / Black Line (Not reflecting light)
        left_state = GPIO.input(SENSOR_LEFT)
        right_state = GPIO.input(SENSOR_RIGHT)

        # Interpret the reading
        # Note: You may need to flip 'Detected' and 'Clear' depending 
        # on your specific sensor logic.
        left_msg = "Detected" if left_state == 0 else "Clear"
        right_msg = "Detected" if right_state == 0 else "Clear"

        # Print cleanly on one line
        print(f"Left: {left_state} ({left_msg}) | Right: {right_state} ({right_msg})")
        
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nTest stopped by user.")
finally:
    GPIO.cleanup()
    print("GPIO cleanup done.")