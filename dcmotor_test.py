import RPi.GPIO as GPIO
import time

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor 1 (Right Motor)
RPWM_PIN_M1 = 20    # M1 Forward
LPWM_PIN_M1 = 21    # M1 Backward

# Motor 2 (Left Motor)
RPWM_PIN_M2 = 12    # M2 Forward
LPWM_PIN_M2 = 16    # M2 Backward

# Set all pins as output
GPIO.setup([RPWM_PIN_M1, LPWM_PIN_M1, RPWM_PIN_M2, LPWM_PIN_M2], GPIO.OUT)

# --- PWM Setup (1kHz) ---
pwm_m1_fwd = GPIO.PWM(RPWM_PIN_M1, 1000)
pwm_m1_bwd = GPIO.PWM(LPWM_PIN_M1, 1000)
pwm_m2_fwd = GPIO.PWM(RPWM_PIN_M2, 1000)
pwm_m2_bwd = GPIO.PWM(LPWM_PIN_M2, 1000)

# Start all PWM at 0
for pwm in [pwm_m1_fwd, pwm_m1_bwd, pwm_m2_fwd, pwm_m2_bwd]:
    pwm.start(0)

def stop_all():
    """Stop all motors"""
    pwm_m1_fwd.ChangeDutyCycle(0)
    pwm_m1_bwd.ChangeDutyCycle(0)
    pwm_m2_fwd.ChangeDutyCycle(0)
    pwm_m2_bwd.ChangeDutyCycle(0)

def move_forward(speed):
    """
    MOVE FORWARD
    Right Motor (M1) -> Forward
    Left Motor  (M2) -> Forward
    """
    # Right Motor Forward
    pwm_m1_bwd.ChangeDutyCycle(0)
    pwm_m1_fwd.ChangeDutyCycle(speed)
    
    # Left Motor Forward
    pwm_m2_bwd.ChangeDutyCycle(0)
    pwm_m2_fwd.ChangeDutyCycle(speed)

def move_backward(speed):
    """
    MOVE BACKWARD
    Right Motor (M1) -> Backward
    Left Motor  (M2) -> Backward
    """
    # Right Motor Backward
    pwm_m1_fwd.ChangeDutyCycle(0)
    pwm_m1_bwd.ChangeDutyCycle(speed)
    
    # Left Motor Backward
    pwm_m2_fwd.ChangeDutyCycle(0)
    pwm_m2_bwd.ChangeDutyCycle(speed)

def turn_right(speed):
    """
    TURN LEFT (Pivot Turn)
    Right Motor (M1) -> Forward
    Left Motor  (M2) -> Backward (or Stop)
    """
    # To pivot tight: Right Motor Forward, Left Motor Backward
    # Right Motor Forward
    pwm_m1_bwd.ChangeDutyCycle(0)
    pwm_m1_fwd.ChangeDutyCycle(speed)
    
    # Left Motor Backward
    pwm_m2_fwd.ChangeDutyCycle(0)
    pwm_m2_bwd.ChangeDutyCycle(speed)

def turn_left(speed):
    """
    TURN RIGHT (Pivot Turn)
    Right Motor (M1) -> Backward (or Stop)
    Left Motor  (M2) -> Forward
    """
    # To pivot tight: Right Motor Backward, Left Motor Forward
    # Right Motor Backward
    pwm_m1_fwd.ChangeDutyCycle(0)
    pwm_m1_bwd.ChangeDutyCycle(speed)
    
    # Left Motor Forward
    pwm_m2_bwd.ChangeDutyCycle(0)
    pwm_m2_fwd.ChangeDutyCycle(speed)


try:
    print("Starting Motor Control Test...")
    
    while True:
        print(">>> Moving Forward")
        for dc in range(0, 51, 5):
            move_forward(dc)
            time.sleep(0.05)
        time.sleep(1)
        for dc in range(50, -1, -5):
            move_forward(dc)
            time.sleep(0.05)
        stop_all()
        time.sleep(1)

        # print(">>> Moving Backward")
        # for dc in range(0, 51, 5):
        #     move_backward(dc)
        #     time.sleep(0.05)
        # time.sleep(1)
        # for dc in range(50, -1, -5):
        #     move_backward(dc)
        #     time.sleep(0.05)
        # stop_all()
        # time.sleep(1)

        # --- 3. TURN RIGHT ---
        # print(">>> Turning Right")
        # turn_right(40)
        # time.sleep(0.8)
        # stop_all()
        # time.sleep(1)

        # # --- 4. TURN LEFT ---
        # print(">>> Turning Left")
        # turn_left(40)
        # time.sleep(0.8)
        # stop_all()
        # time.sleep(1)

except KeyboardInterrupt:
    print("\nProgram stopped by user")
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