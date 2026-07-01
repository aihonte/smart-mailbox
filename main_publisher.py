import time
import json
import mqtt_client
import hardware_core
import alert_processor

# 웹훅 URL (Day 6에서 사용했으나 현재는 주석 처리)
# WEBHOOK_URL = "http://192.168.137.204:8000/webhook/alert"
# 센서 데이터 측정 및 발행 주기 (초)
CORE_INTERVAL = 0.5
# Day 8: 웹 서버로부터 받은 제어 메시지를 처리할 함수 정의
def handle_control_command(payload_str):
    print(f"\n<<< COMMAND RECEIVED >>> Payload: {payload_str}")
    
    try:
        payload = json.loads(payload_str)
        if payload.get("command") == "RESET":
            print("*** [COMMAND] 우편함 확인 완료 명령 수신. 경고 상태 리셋. ***")
            
            # Day 8 핵심: 경고 상태를 강제로 정상(1)으로 리셋
            alert_processor.current_box_status_code = 1
            print(f"*** [STATUS] alert_processor 상태 코드 강제 리셋 완료: {alert_processor.current_box_status_code} ***")
    except json.JSONDecodeError:
        print("COMMAND ERROR: Invalid JSON payload.")

def main_publisher():
    
    # 1. MQTT 클라이언트 초기화 및 연결
    # 제어 메시지 처리 함수(handle_control_command)를 클라이언트 생성 시 전달합니다.
    mqtt_pub_client = mqtt_client.MqttPublisherClient(
        broker_address=mqtt_client.BROKER_ADDRESS,
        port=mqtt_client.PORT,
        client_id=mqtt_client.CLIENT_ID,
        # Day 8 구현: 제어 메시지를 처리할 함수를 클라이언트에 등록
        on_control_message_callback=handle_control_command
    )
    mqtt_pub_client.connect()
    
    # 2. 메인 루프 시작
    try:
        while True:
            # 2-1. 센서 데이터 읽기 
            sensor_data = hardware_core.read_data()
            
            # 2-2. 센서 데이터 발행
            mqtt_pub_client.publish(mqtt_client.TOPIC, sensor_data)
            
            # 2-3. 경고 상태 확인 및 알림 발행 
            # 필수 인자 2개 (client_id, alert_topic) 추가하여 호출
            current_status_code = alert_processor.process_sensor_data_and_alert(
                data=sensor_data, 
                mqtt_client=mqtt_pub_client,
                client_id=mqtt_client.CLIENT_ID,
                alert_topic=mqtt_client.ALERT_TOPIC
            )

            # 2-4. LED 제어 (Day 9 목표)
            # 현재 상태 코드가 1(정상)이 아니면 LED 켜기 (True), 정상이면 끄기 (False)
            hardware_core.set_led_status(current_status_code != 1)

            time.sleep(CORE_INTERVAL)
    except KeyboardInterrupt:
        print("\nPublisher 종료 중...")
    finally:
        mqtt_pub_client.disconnect()
        print("MQTT 클라이언트 연결 해제.")
        hardware_core.cleanup() # GPIO 및 SPI 리소스 해제
        print("하드웨어 리소스 정리 완료.")
if __name__ == '__main__':
    main_publisher()