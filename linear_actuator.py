import RPi.GPIO as GPIO
import time

# --- 설정 (메인 코드와 동일한 핀) ---
ACT_PIN_A = 19
ACT_PIN_B = 26

# 작동 시간 (초) - 액추에이터가 끝까지 나가는 데 걸리는 시간만큼 설정
MOVE_TIME = 3.0 

# --- GPIO 설정 ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup([ACT_PIN_A, ACT_PIN_B], GPIO.OUT)

def stop_actuator():
    """정지 (전력 차단)"""
    GPIO.output(ACT_PIN_A, GPIO.LOW)
    GPIO.output(ACT_PIN_B, GPIO.LOW)
    print("   [정지] 전원 차단")

def push_actuator():
    """전진 (밀기)"""
    print(">>> [PUSH] 앞으로 미는 중...")
    # 극성 설정: A=High, B=Low
    GPIO.output(ACT_PIN_A, GPIO.HIGH)
    GPIO.output(ACT_PIN_B, GPIO.LOW)

def pull_actuator():
    """후진 (당기기)"""
    print("<<< [PULL] 뒤로 당기는 중...")
    # 극성 반대: A=Low, B=High
    GPIO.output(ACT_PIN_A, GPIO.LOW)
    GPIO.output(ACT_PIN_B, GPIO.HIGH)

try:
    print("--- 리니어 액추에이터 테스트 시작 ---")
    print(f"핀 설정: GPIO {ACT_PIN_A}, {ACT_PIN_B}")
    
    # 1. 전진 테스트
    push_actuator()
    time.sleep(MOVE_TIME)
    
    #stop_actuator()
    time.sleep(1.0) # 1초 대기

    # 2. 후진 테스트
    pull_actuator()
    time.sleep(MOVE_TIME)

    #stop_actuator()
    print("--- 테스트 완료 ---")

except KeyboardInterrupt:
    print("\n강제 종료")
finally:
    stop_actuator()
    GPIO.cleanup()
    print("GPIO 정리 완료")