import socket
import json
import time
import RPi.GPIO as GPIO

# --- Configuration ---
UDP_IP = "0.0.0.0"
UDP_PORT = 6000

# 속도 설정
SPEED_BASE = 15        
SPEED_TURN_HIGH = 35   
SPEED_TURN_LOW = 5    

# 회전 시간 (바닥 마찰력에 따라 튜닝 필요)
TIME_TURN_90 = 1.8
TIME_TURN_180 = 3.6

# 스텝 모터 & 액추에이터 설정
STEPS_TO_LEVEL_2 = 6000
MIN_DELAY = 0.0008
START_DELAY = 0.001
RAMP_STEPS = 200
ACT_EXTEND_TIME = 3.0
ACT_RETRACT_TIME = 3.0

class RobotHardware:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Pins
        self.RPWM_PIN_M1 = 20; self.LPWM_PIN_M1 = 21  # Right
        self.RPWM_PIN_M2 = 12; self.LPWM_PIN_M2 = 16  # Left
        self.SENSOR_LEFT = 22; self.SENSOR_RIGHT = 23
        self.DIR_PIN = 17; self.STEP_PIN = 18; self.ENABLE_PIN = 27
        self.ACT_PIN_A =19; self.ACT_PIN_B = 26

        # Setup
        GPIO.setup([self.RPWM_PIN_M1, self.LPWM_PIN_M1, self.RPWM_PIN_M2, self.LPWM_PIN_M2], GPIO.OUT)
        GPIO.setup([self.DIR_PIN, self.STEP_PIN, self.ENABLE_PIN], GPIO.OUT)
        GPIO.setup([self.ACT_PIN_A, self.ACT_PIN_B], GPIO.OUT)
        GPIO.setup([self.SENSOR_LEFT, self.SENSOR_RIGHT], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # PWM
        self.pwm_m1_fwd = GPIO.PWM(self.RPWM_PIN_M1, 1000)
        self.pwm_m1_bwd = GPIO.PWM(self.LPWM_PIN_M1, 1000)
        self.pwm_m2_fwd = GPIO.PWM(self.RPWM_PIN_M2, 1000)
        self.pwm_m2_bwd = GPIO.PWM(self.LPWM_PIN_M2, 1000)

        for p in [self.pwm_m1_fwd, self.pwm_m1_bwd, self.pwm_m2_fwd, self.pwm_m2_bwd]: p.start(0)

        self.current_level = 1
        GPIO.output(self.ENABLE_PIN, GPIO.HIGH)
        
        # 교차로 감지 변수
        self.on_cross_line = False   
        self.last_cross_time = 0     

    def _set_motor(self, pwm_fwd, pwm_bwd, speed):
        pwm_bwd.ChangeDutyCycle(0)
        pwm_fwd.ChangeDutyCycle(max(0, min(100, speed)))

    def drive_differential(self, left, right):
        self._set_motor(self.pwm_m2_fwd, self.pwm_m2_bwd, left)
        self._set_motor(self.pwm_m1_fwd, self.pwm_m1_bwd, right)

    def stop_move(self):
        self.drive_differential(0, 0)

    def turn_spot(self, direction, duration):
        self.stop_move()
        time.sleep(0.2)
        if direction == "RIGHT":
            self._set_motor(self.pwm_m2_fwd, self.pwm_m2_bwd, SPEED_BASE) 
            self._set_motor(self.pwm_m1_bwd, self.pwm_m1_fwd, SPEED_BASE) 
        else: # LEFT
            self._set_motor(self.pwm_m2_bwd, self.pwm_m2_fwd, SPEED_BASE) 
            self._set_motor(self.pwm_m1_fwd, self.pwm_m1_bwd, SPEED_BASE) 
        time.sleep(duration)
        self.stop_move()
        time.sleep(0.2)

    # --- Line Following (교차로 카운팅) ---
    def follow_line_step(self):
        """ 0=검정, 1=흰색. 교차로 통과 시 True 반환 """
        l = GPIO.input(self.SENSOR_LEFT)
        r = GPIO.input(self.SENSOR_RIGHT)
        passed_new_cross = False

        # 1. 검은 선(Cross) 진입
        if l == 0 and r == 0:
            self.on_cross_line = True  
            self.drive_differential(SPEED_BASE, SPEED_BASE) 

             # 3. 라인 보정
        elif l == 0 and r == 1:
            self.drive_differential(SPEED_TURN_LOW, SPEED_TURN_HIGH)
        elif l == 1 and r == 0:
            self.drive_differential(SPEED_TURN_HIGH, SPEED_TURN_LOW)

        # 2. 흰 배경(White) 복귀 (통과 완료)
        elif l == 1 and r == 1:
            if self.on_cross_line:
                # 디바운싱: 1.5초 이내 중복 감지 무시
                if time.time() - self.last_cross_time > 1.5:
                    passed_new_cross = True
                    self.last_cross_time = time.time() 
                self.on_cross_line = False 
            self.drive_differential(SPEED_BASE, SPEED_BASE)

       
        return passed_new_cross

    # --- Hardware Actions ---
    def set_lift_level(self, target_level):
        if target_level == self.current_level: return
        print(f"--- Lift: {self.current_level} -> {target_level} ---")
        
        GPIO.output(self.ENABLE_PIN, GPIO.LOW)
        GPIO.output(self.DIR_PIN, GPIO.HIGH if target_level == 2 else GPIO.LOW)
        time.sleep(0.01)
        
        d = START_DELAY
        dec = (START_DELAY - MIN_DELAY) / RAMP_STEPS
        for i in range(STEPS_TO_LEVEL_2):
            GPIO.output(self.STEP_PIN, GPIO.HIGH); time.sleep(d)
            GPIO.output(self.STEP_PIN, GPIO.LOW); time.sleep(d)
            if i < RAMP_STEPS and d > MIN_DELAY: d -= dec
        
        GPIO.output(self.ENABLE_PIN, GPIO.HIGH)
        self.current_level = target_level

    def action_extinguisher(self):
        print(">>> [ACTUATOR] PUSH (Extinguish)")
        GPIO.output(self.ACT_PIN_A, GPIO.HIGH); GPIO.output(self.ACT_PIN_B, GPIO.LOW)
        time.sleep(ACT_EXTEND_TIME)
        
        GPIO.output(self.ACT_PIN_A, GPIO.LOW); GPIO.output(self.ACT_PIN_B, GPIO.LOW)
        time.sleep(1.0) 

        print(">>> [ACTUATOR] PULL (Return)")
        GPIO.output(self.ACT_PIN_A, GPIO.LOW); GPIO.output(self.ACT_PIN_B, GPIO.HIGH)
        time.sleep(ACT_RETRACT_TIME)
        
        GPIO.output(self.ACT_PIN_A, GPIO.LOW); GPIO.output(self.ACT_PIN_B, GPIO.LOW)

    def cleanup(self):
        self.stop_move()
        GPIO.cleanup()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print("System Ready...")
    robot = RobotHardware()
    current_spot = 0 

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            try:
                parsed_data = json.loads(data.decode('utf-8'))
                msg = parsed_data[0] if isinstance(parsed_data, list) and parsed_data else (parsed_data if isinstance(parsed_data, dict) else {})
                
                target_spot = msg.get("spot", 0)
                target_level = msg.get("level", 1)

                if target_spot == 0 or target_spot == current_spot: continue

                print(f"=== Command: Move {current_spot} -> {target_spot} ===")

                # 1. 이동 (전진)
                if target_spot > current_spot:
                    print(" -> Moving Forward")
                    while current_spot < target_spot:
                        if robot.follow_line_step():
                            current_spot += 1
                            print(f"   [+] Spot: {current_spot}")
                            robot.drive_differential(SPEED_BASE, SPEED_BASE)
                            time.sleep(0.2) 

                # 2. 화재 진압 시퀀스
                robot.stop_move()
                print(" -> Fire Sequence Started")
                time.sleep(0.5)

                # (1) 화재 방향(왼쪽)으로 90도 회전
                robot.turn_spot("LEFT", TIME_TURN_90) 
                
                # (2) 진압 (높이 조절 -> 액추에이터)
                robot.set_lift_level(target_level)
                robot.action_extinguisher()
                
                # (3) 리프트 원위치
                robot.set_lift_level(1)
                
                # (4) [복귀 준비] 왼쪽으로 90도 더 회전 (총 180도) -> 뒤를 보게 됨
                print(" -> Turning LEFT again to face Home")
                robot.turn_spot("LEFT", TIME_TURN_90)
                
                print(f"=== Mission Complete at Spot {current_spot} ===")

                # 3. 베이스 복귀 (라인 트레이싱)
                if current_spot != 0:
                    print("🚀 Returning to Base...")
                    
                    # [중요] 회전 직후 검은 선이 센서 뒤에 있을 수 있으므로
                    # 잠시 직진하여 '현재 위치' 라인을 물리적으로 벗어남 (카운트 꼬임 방지)
                    robot.drive_differential(SPEED_BASE, SPEED_BASE)
                    time.sleep(0.5)

                    # 복귀 루프 (One less line 고려됨: 이미 현재 라인은 지났다고 가정)
                    while current_spot > 0:
                        if robot.follow_line_step():
                            current_spot -= 1
                            print(f"   [Return] Reached Spot: {current_spot}")
                            robot.drive_differential(SPEED_BASE, SPEED_BASE)
                            time.sleep(0.2)
                    
                    # 0번 도착 후 정지 및 정면 보기 (180도 회전)
                    robot.stop_move()
                    time.sleep(0.5)
                    print(" -> Arrived at Base. Re-orienting 180...")
                    robot.turn_spot("RIGHT", TIME_TURN_180)
                    print("🏁 Returned to Base.")
                
                print("🛑 System Off.")
                break 

            except json.JSONDecodeError: pass
            except Exception as e: print(f"Error: {e}")

    except KeyboardInterrupt:
        print("Shutdown")
    finally:
        sock.close()
        robot.cleanup()

if __name__ == "__main__":
    main()