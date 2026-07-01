import paho.mqtt.client as mqtt
import json

# MQTT 브로커 설정
BROKER_ADDRESS = "192.168.137.204"
PORT = 1883
TOPIC = "sensor"
ALERT_TOPIC = "alert/parcel_status"

# Day 8: 제어 명령 토픽 추가 (web_server.py와 동일해야 함)
CONTROL_TOPIC = "command/reset_alert"

CLIENT_ID = "ALERT_DATA_PUBLISHER" # 발행자 클라이언트 ID

class MqttPublisherClient:
    
    # on_control_message_callback 인수를 추가하여, 제어 메시지 처리 함수를 받음
    def __init__(self, broker_address, port, client_id, on_control_message_callback=None):
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        
        # 제어 메시지를 받았을 때 main_publisher.py로 전달할 콜백 함수 저장
        self.on_control_message_callback = on_control_message_callback
        
        # 콜백 함수 설정
        self.client.on_connect = self._on_connect
        # 메시지 수신 시 실행될 _on_message 콜백 함수 연결
        self.client.on_message = self._on_message 

    def connect(self):
        try:
            # connect 함수에 loop_start() 호출을 추가하여 연결 후 즉시 통신 시작
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT 연결 실패: {e}")
            
    # 연결 종료를 위한 메서드 추가
    def disconnect(self):
        try:
            self.client.loop_stop() # 루프 종료
            self.client.disconnect() # 연결 종료
            print("MQTT Broker 연결이 안전하게 종료되었습니다.")
        except Exception as e:
            print(f"MQTT 연결 종료 오류: {e}")
            
    # 연결 관련 콜백 함수
    def _on_connect(self, client, userdata, flags, rc, prop=None):
        if rc == 0:
            print("MQTT Broker 연결 성공")
            # 발행자도 제어 토픽을 구독하도록 추가
            client.subscribe(CONTROL_TOPIC, qos=0) 
            print(f"제어 토픽 구독 시작: {CONTROL_TOPIC}")
        else:
            print(f"MQTT Broker 연결 실패 - 결과 코드: {rc}")

    # 메시지 수신 시 실행될 콜백 함수 추가
    def _on_message(self, client, userdata, msg):
        # CONTROL_TOPIC 메시지만 처리
        if msg.topic == CONTROL_TOPIC and self.on_control_message_callback:
            # 제어 메시지 페이로드를 콜백 함수로 전달하여 처리
            self.on_control_message_callback(msg.payload.decode('utf-8'))
            
    #  publish 메서드 (한글 인코딩 문제 해결)
    def publish(self, topic, data, qos=0):
        try:
            if isinstance(data, (dict, list)):
                # 딕셔너리나 리스트 등 복합 데이터 타입은 JSON으로 변환
                # ensure_ascii=False 옵션을 추가하여 한글을 유니코드 이스케이프하지 않도록 함 (핵심 수정)
                payload = json.dumps(data, ensure_ascii=False)
            elif isinstance(data, str):
                # 문자열(예: 경고 메시지)은 그대로 사용 (불필요한 인코딩 방지)
                payload = data
            else:
                # 기타 타입은 문자열로 변환
                payload = str(data)

            # MQTT는 바이트열(bytes)을 보내야 하므로 최종적으로 UTF-8로 인코딩하여 발행
            self.client.publish(topic, payload, qos=0) 
            # print(f"Publish 성공 - Topic: {topic} | Data: {payload}")
        except Exception as e:
            print(f"MQTT 발행 오류: {e}")