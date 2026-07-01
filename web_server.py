from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import json
import threading
import time

# 전역 MQTT 클라이언트 객체를 위한 변수 선언 (NULL 초기화)
mqtt_subscriber_client = None

# 1. 웹 서버 및 MQTT 설정 상수
# Flask 애플리케이션 초기화 (웹 서버의 중심 객체)
app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

# MQTT 설정 (Publisher와 동일하게 설정하여 통신 준비)
BROKER_ADDRESS = "192.168.137.204"  # MQTT 브로커(라즈베리 파이) 주소
PORT = 1883
TOPIC = "sensor"                    # 센서 데이터 발행 토픽 (구독 대상 1)
ALERT_TOPIC = "alert/parcel_status" # 경고 메시지 발행 토픽 (구독 대상 2)
CLIENT_ID = "WEB_SERVER_SUBSCRIBER" # 이 클라이언트의 고유 ID
CONTROL_TOPIC = "command/reset_alert" # Day 8: 제어 명령 토픽 추가

# 2. 실시간 데이터 저장소 
# 웹 페이지에 표시될 최신 센서 데이터를 저장하는 전역 변수
current_sensor_data = {
    "distance": 0.0,
    "temperature": 0.0,
    "humidity": 0.0,
    "lux_adc": 0,
    "timestamp": "N/A"
}
# 웹 페이지에 표시될 최신 경고 메시지 저장
current_alert_message = "우편물 대기 중"

# 현재 우편함 상태 코드 저장 (1: 정상, 2: 택배 도착, 3/4: 문 열림 등)
current_alert_status = 1 

# 3. MQTT 구독자 콜백 함수 
# MQTT 연결 성공 시 실행되는 콜백 함수
def on_connect(client, userdata, flags, rc, prop=None):
    if rc == 0:
        print("MQTT Broker 연결 성공 (Subscriber)")
        # 구독 시작: 센서 데이터 토픽과 경고 토픽을 동시에 구독 설정
        client.subscribe([(TOPIC, 0), (ALERT_TOPIC, 0)])
        print(f"토픽 구독 시작: {TOPIC}, {ALERT_TOPIC}")
    else:
        print(f"MQTT Broker 연결 실패 - 결과 코드: {rc}")

# 메시지 수신 시 실행되는 콜백 함수
def on_message(client, userdata, msg):
    global current_sensor_data, current_alert_message, current_alert_status
    
    # 센서 데이터 수신 처리 (sensor 토픽)
    if msg.topic == TOPIC:
        try:
            # 수신된 JSON 데이터를 문자열로 변환 후, 파이썬 객체로 로드
            payload = json.loads(msg.payload.decode('utf-8'))
            current_sensor_data = payload # 전역 변수 업데이트
            print(f"수신: {TOPIC} | {payload['timestamp']}")
        except json.JSONDecodeError:
            print(f"JSON 디코딩 오류: {msg.payload}")
    # 경고 메시지 수신 처리 (alert/parcel_status 토픽)
    elif msg.topic == ALERT_TOPIC:
        alert_message = msg.payload.decode('utf-8')
        current_alert_message = alert_message # 전역 변수 업데이트
        
        # 경고 메시지 내용에 따라 상태 코드 업데이트
        if "택배가 도착했습니다" in alert_message:
            current_alert_status = 2
        elif "주의!" in alert_message:
            if "물품 있음" in alert_message:
                 current_alert_status = 3
            elif "물품 없음" in alert_message:
                 current_alert_status = 4
            else: # 물품 유무가 명확하지 않은 경우, 경고 상태 유지
                 current_alert_status = 4 # 3 또는 4 둘 중 하나로 설정
                 
        # 상태 복귀 메시지가 '우편물 대기 중'으로 통일되었기 때문에 해당 메시지로 판단합니다.
        elif "우편물 대기 중" in alert_message:
            current_alert_status = 1
            
        print(f"수신: {ALERT_TOPIC} | {alert_message}")

# 4. MQTT 구독 실행 함수 (별도 스레드에서 실행)
def mqtt_subscribe_thread():
    global mqtt_subscriber_client # ❗ 전역 변수 사용 선언
    # MQTT 클라이언트 객체 생성 및 콜백 함수 설정
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_subscriber_client = client # 전역 변수에 클라이언트 객체 저장
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        # loop_forever(): 연결이 끊어지지 않도록 무한 루프로 MQTT 통신을 지속 처리
        client.loop_forever() 
    except Exception as e:
        print(f"MQTT 구독 스레드 오류: {e}")
        time.sleep(5)
    
# 5. Flask 라우트 정의 (웹 페이지 주소)
# '/' 루트로 접속했을 때 실행되는 함수
@app.route('/')
def index():
    return render_template('dashboard.html')

# '/api/data' 경로로 접속했을 때 실행되는 API
@app.route('/api/data')
def api_data():
    
    global current_alert_message #	
    # 만약 현재 상태 코드가 1이지만, 메시지가 경고 상태로 남아있다면 '우편물 대기 중'으로 덮어씌웁니다.
    # 이는 reset 버튼을 눌러 상태 코드가 1로 선제적 업데이트 되었을 때 메시지까지 통일하기 위함입니다.
    if current_alert_status == 1:
        current_alert_message = "우편물 대기 중"

    # 현재 저장된 센서 데이터와 경고 정보를 JSON 형태로 반환
    return jsonify({
        "sensor": current_sensor_data,
        "alert": current_alert_message,
        "status_code": current_alert_status
    })

# Day 8: 제어 명령 발행 라우트 (POST 요청)
@app.route('/control/reset', methods=['POST'])
def control_reset():
    global mqtt_subscriber_client, current_alert_status
    if mqtt_subscriber_client:
        # 제어 명령 페이로드 생성
        command_payload = json.dumps({"command": "RESET", "source": "WEB"})
        
        # MQTT로 제어 명령 발행
        mqtt_subscriber_client.publish(CONTROL_TOPIC, command_payload, qos=0)
        
        # 웹 페이지에 즉시 상태 복귀를 반영 (선제적 업데이트)
        current_alert_status = 1 
        
        global current_alert_message
        current_alert_message = "우편물 대기 중"
        
        print(f"COMMAND PUBLISH -> Topic: {CONTROL_TOPIC} | Payload: {command_payload}")
        return jsonify({"status": "success", "message": "경고 리셋 명령 발행됨."})
    else:
        return jsonify({"status": "error", "message": "MQTT 클라이언트가 연결되지 않았습니다."})
    
# 6. 메인 실행 블록
if __name__ == '__main__':
    # Flask 서버는 메인 스레드에서 실행되므로, MQTT 구독은 별도의 백그라운드 스레드에서 시작해야 함
    
    # threading.Thread를 사용하여 mqtt_subscribe_thread 함수를 타겟으로 지정
    mqtt_thread = threading.Thread(target=mqtt_subscribe_thread, daemon=True)
    # daemon=True: 메인 프로그램(Flask)이 종료될 때 이 스레드도 자동 종료되도록 설정
    mqtt_thread.start()
    
    # Flask 웹 서버 시작
    print("Starting Flask Web Server...")
    # host='0.0.0.0': 외부(네트워크)에서 접속 가능하도록 설정
    # port=8000: 서버 포트 설정 (기존 웹훅 설정 주소와 동일)
    # debug=True: 개발 모드 설정 (코드 변경 시 서버 자동 재시작)
    app.run(host='0.0.0.0', port=8000, debug=True)