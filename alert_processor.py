import json

# 경고 판단 상수
DISTANCE_THRESHOLD = 14.0
LUX_THRESHOLD = 100

#  상태 변화에 따른 사용자 친화적 메시지 정의 
USER_MESSAGES = {
    # 상태 1 (정상/복귀) 관련 메시지를 "우편물 대기 중"으로 통일
    'NORMAL_STATUS': "우편물 대기 중", 
    'STATUS_RESET': "우편물 대기 중", # 복귀 시 메시지 통일
    # 상태 2, 3, 4 (경고) 관련 메시지
    2: "택배가 도착했습니다!",
    3: "주의! 우편함 문 열림 (물품 있음)",
    4: "주의! 우편함 문이 열려있습니다. (물품 없음)"
}

# 전역 변수: 현재 우편함의 상태 코드를 저장 (초기값: 1, 비어 있고 닫힌 상태)
current_box_status_code = 1

# 센서 데이터로부터 우편함의 4가지 상태를 파악
def get_current_box_status(data):
    
    current_distance = data["distance"]
    current_lux = data["lux_adc"]
    
    is_item_present = (current_distance <= DISTANCE_THRESHOLD)
    is_door_open = (current_lux >= LUX_THRESHOLD)
    
    if not is_item_present and not is_door_open:
        return 1, "우편함 닫힘 (물품 유무 : X)"
    elif is_item_present and not is_door_open:
        return 2, "우편함 닫힘 (물품 유무 : O)"
    elif is_item_present and is_door_open:
        return 3, "우편함 열림 (물품 유무 : O)"
    elif not is_item_present and is_door_open:
        return 4, "우편함 열림 (물품 유무 : X)"
        
    return 0, "상태 확인불가"

# 상태 변화 감지, 경고 메시지 생성 및 웹 전송
# 이 함수는 MQTT 클라이언트 객체(mqtt_client)를 통해 발행을 요청합니다.
def process_sensor_data_and_alert(data, mqtt_client, client_id, alert_topic):
    
    global current_box_status_code # 전역 변수 current_box_status_code 사용
    
    new_status_code, new_status_message = get_current_box_status(data)
    
    alert_message = None
    
    # 2. 상태 변화 감지 (핵심 로직)
    if new_status_code != current_box_status_code:
        
        # Case 1: 새로운 상태가 경고 상태(2, 3, 4)일 경우
        if new_status_code in [2, 3, 4]:
            # 경고 메시지 발행 (택배 도착, 문 열림 등)
            alert_message = USER_MESSAGES.get(new_status_code)
            
        # Case 2: 새로운 상태가 정상 상태(1)로 복귀할 경우
        elif new_status_code == 1 and current_box_status_code in [2, 3, 4]:
            # 복귀 메시지 발행 ("우편물 대기 중"으로 통일)
            alert_message = USER_MESSAGES['STATUS_RESET']
            
        # 3. 경고 메시지 발행 및 WEB API 전송
        if alert_message:
            
            # MQTT 발행 (통신 기능은 mqtt_client가 담당하지만, 요청은 여기서)
            mqtt_client.publish(alert_topic, alert_message, qos=0)
            print(f"*** ALERT PUBLISH *** -> Topic: {alert_topic} | Message: {alert_message}")
            
        # 4. 상태 코드 업데이트 (상태가 변했을 경우에만 업데이트)
        current_box_status_code = new_status_code
    
    # Day 8: main_publisher에서 LED 제어를 위해 현재 상태 코드를 반환
    return current_box_status_code