import RPi.GPIO as GPIO
import time

# 핀 번호 설정 (BCM 모드)
DIR_PIN = 17
STEP_PIN = 18
ENABLE_PIN = 27

# 1: 핀 모드 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(ENABLE_PIN, GPIO.OUT)

# --- 설정값 수정 ---
STEPS_PER_REVOLUTION = 100 # 200
REVOLUTIONS = 3
total_steps = STEPS_PER_REVOLUTION * REVOLUTIONS

# [수정됨] 가속 관련 설정
MIN_DELAY = 0.0010  # 목표 최고 속도 (기존 설정값)
START_DELAY = 0.001 # 시작 속도 (천천히 시작, 0.002초 = 2ms)
RAMP_STEPS = 100    # 가속에 사용할 스텝 수 (처음 200스텝 동안 가속)

def move_motor(direction, steps):
    # 방향 설정
    GPIO.output(DIR_PIN, direction)
    
    # 현재 딜레이를 시작 속도로 초기화
    current_delay = START_DELAY
    
    # 딜레이 감소량 계산 (선형 가속)
    # (시작속도 - 목표속도) / 가속구간
    decrement = (START_DELAY - MIN_DELAY) / RAMP_STEPS

    for i in range(steps):
        # 펄스 생성
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(current_delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(current_delay)
        
        # 가속 로직: 목표 속도에 도달할 때까지 딜레이를 줄임
        if i < RAMP_STEPS:
            current_delay -= decrement
            if current_delay < MIN_DELAY:
                current_delay = MIN_DELAY
        
        # (선택사항) 감속 로직: 마지막 부분에서 천천히 멈추고 싶다면 추가 구현 필요

try:
    print("모터 동작 시작")
    GPIO.output(ENABLE_PIN, GPIO.LOW) # 활성화
    time.sleep(0.1)

    # 1. 위로 이동
    #print("위로 이동 중 (가속 적용)...")
    #move_motor(GPIO.HIGH, total_steps)
    
    time.sleep(1.0)

    # 2. 아래로 이동
    print("아래로 이동 중 (가속 적용)...")
    move_motor(GPIO.LOW, total_steps)

finally:
    print("\n종료 및 정리")
    GPIO.output(ENABLE_PIN, GPIO.HIGH)
    GPIO.cleanup()