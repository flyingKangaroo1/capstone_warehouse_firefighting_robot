import socket
import json
import time

# --- 설정 ---
UDP_IP = "0.0.0.0"
UDP_PORT = 6000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"📡 수신 대기 중... ({UDP_IP}:{UDP_PORT})")
print("-" * 40)

try:
    while True:
        data, addr = sock.recvfrom(1024)
        timestamp = time.strftime("%H:%M:%S")

        print(f"\n[{timestamp}] 데이터 도착! (From: {addr[0]})")
        
        try:
            decoded_str = data.decode('utf-8')
            parsed_data = json.loads(decoded_str)

            print(f"   ▶ 파싱 데이터: {parsed_data}")

            # [수정된 부분] 리스트인지 딕셔너리인지 확인하고 처리
            target_data = None

            if isinstance(parsed_data, list):
                if len(parsed_data) > 0:
                    target_data = parsed_data[0] # 리스트의 첫 번째 항목 선택
                else:
                    print("   ⚠️ 빈 리스트가 도착했습니다.")
                    continue
            elif isinstance(parsed_data, dict):
                target_data = parsed_data
            else:
                print("   ⚠️ 알 수 없는 데이터 형식입니다.")
                continue

            # 이제 .get() 사용 가능
            spot = target_data.get("spot", 0)
            level = target_data.get("level", 0)

            print("-" * 20)
            print(f"   ✅ [추출 성공] 목표 지점(SPOT): {spot}")
            print(f"   ✅ [추출 성공] 목표 층수(LEVEL): {level}")
            print("-" * 20)

        except json.JSONDecodeError:
            print("   ⚠️ JSON 파싱 실패")
        except Exception as e:
            print(f"   ⚠️ 에러 발생: {e}")

except KeyboardInterrupt:
    print("\n종료합니다.")
finally:
    sock.close()