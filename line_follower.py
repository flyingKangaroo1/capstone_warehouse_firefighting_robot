import RPi.GPIO as GPIO
import time

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# --- Motor Pins ---
# Motor 1 (Right Motor)
RPWM_PIN_M1 = 20    # M1 Forward
LPWM_PIN_M1 = 21    # M1 Backward

# Motor 2 (Left Motor)
RPWM_PIN_M2 = 12    # M2 Forward
LPWM_PIN_M2 = 16    # M2 Backward

# --- Sensor Pins ---
SENSOR_LEFT = 22
SENSOR_RIGHT = 23

# --- Pin Setup ---
# Motors as Output
GPIO.setup([RPWM_PIN_M1, LPWM_PIN_M1, RPWM_PIN_M2, LPWM_PIN_M2], GPIO.OUT)

# Sensors as Input
GPIO.setup(SENSOR_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SENSOR_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- PWM Setup (1kHz) ---
pwm_m1_fwd = GPIO.PWM(RPWM_PIN_M1, 1000)
pwm_m1_bwd = GPIO.PWM(LPWM_PIN_M1, 1000)
pwm_m2_fwd = GPIO.PWM(RPWM_PIN_M2, 1000)
pwm_m2_bwd = GPIO.PWM(LPWM_PIN_M2, 1000)

# Start all PWM at 0
for pwm in [pwm_m1_fwd, pwm_m1_bwd, pwm_m2_fwd, pwm_m2_bwd]:
    pwm.start(0)

# --- Helper Functions ---

def stop_all():
    """Stop all motors"""
    pwm_m1_fwd.ChangeDutyCycle(0)
    pwm_m1_bwd.ChangeDutyCycle(0)
    pwm_m2_fwd.ChangeDutyCycle(0)
    pwm_m2_bwd.ChangeDutyCycle(0)

def set_motor(pwm_fwd, pwm_bwd, speed):
    """
    Sets motor speed and direction.
    speed: -100 to 100 (Negative = Backward, Positive = Forward)
    """
    # Constrain speed to -100 to 100
    if speed > 50: speed = 50
    if speed < -50: speed = -50

    if speed >= 0:
        pwm_bwd.ChangeDutyCycle(0)
        pwm_fwd.ChangeDutyCycle(speed)
    else:
        pwm_fwd.ChangeDutyCycle(0)
        pwm_bwd.ChangeDutyCycle(abs(speed))

# --- PID Variables ---
# Tune these values for your specific robot!
Kp = 20   # Proportional (Main turning force)
Kd = 15   # Derivative (Dampening, reduces oscillation)
Ki = 0    # Integral (Usually 0 for line followers)

BASE_SPEED = 20  # Default forward speed
last_error = 0
integral = 0

try:
    print("--- PID Line Follower Started ---")
    print(f"Params: Kp={Kp}, Kd={Kd}, Base={BASE_SPEED}")
    print("Press CTRL+C to stop")
    
    while True:
        # Read Sensors
        # 0 = White (Surface), 1 = Black (Line)
        left_val = GPIO.input(SENSOR_LEFT)
        right_val = GPIO.input(SENSOR_RIGHT)

        # --- 1. Calculate Error ---
        error = 0
        
        if left_val == 0 and right_val == 0:
            # Centered on line (or lost line, assuming previous error)
            error = 0
        elif left_val == 1 and right_val == 0:
            # Line is to the Left
            error = -1
        elif left_val == 0 and right_val == 1:
            # Line is to the Right
            error = 1
        elif left_val == 1 and right_val == 1:
            # Intersection (Stop or treat as 0)
            stop_all()
            print("Intersection Detected - Stopping")
            time.sleep(0.1)
            continue

        # --- 2. PID Calculation ---
        P = error
        I = integral + error
        D = error - last_error
        
        correction = (Kp * P) + (Ki * I) + (Kd * D)
        
        # Save history
        last_error = error
        integral = I

        # --- 3. Apply to Motors ---
        # If Error is Positive (Line Right) -> Turn Right -> Left Motor Speed Up, Right Motor Slow Down
        # If Error is Negative (Line Left)  -> Turn Left  -> Left Motor Slow Down, Right Motor Speed Up
        
        m1_speed = BASE_SPEED - correction  # Right Motor
        m2_speed = BASE_SPEED + correction  # Left Motor

        # Use the helper to apply speeds (handles negative values by reversing motors)
        set_motor(pwm_m1_fwd, pwm_m1_bwd, m1_speed)
        set_motor(pwm_m2_fwd, pwm_m2_bwd, m2_speed)

        # Small delay
        time.sleep(0.005)

except KeyboardInterrupt:
    print("\nStopped by user")
except Exception as e:
    print(f"\nError: {e}")
finally:
    stop_all()
    pwm_m1_fwd.stop()
    pwm_m1_bwd.stop()
    pwm_m2_fwd.stop()
    pwm_m2_bwd.stop()
    GPIO.cleanup()
    print("GPIO Cleaned up.")