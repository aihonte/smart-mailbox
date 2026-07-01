# 파일명: hardware_core.py
# 라이브러리 가져오기 (Imports)
import RPi.GPIO as GPIO         # 라즈베리 파이 GPIO 핀 제어 (초음파, LED)
import time                     # 시간 지연 및 측정 함수 (time.time(), time.sleep)
import board                    # I2C 통신 핀 정의 (SCL, SDA)
import busio                    # I2C 버스 통신 객체 생성 모듈
import adafruit_htu21d          # HTU21D 온습도 센서 사용을 위한 드라이버
import spidev                   # SPI 하드웨어 버스 직접 제어 드라이버
import json                     # 센서 데이터를 JSON 문자열로 변환하기 위해 사용
import datetime                 # TimeStamp 생성을 위해 추가

# 핀 번호 및 초기 설정 (BCM 모드)
TRIG_PIN = 20                   # 초음파 센서: 트리거 펄스 출력 핀
ECHO_PIN = 16                   # 초음파 센서: 에코 펄스 수신 핀
LED_PIN = 6                     # 상태 표시용 LED 핀
  
GPIO.setmode(GPIO.BCM)          # BCM 모드 사용 설정
GPIO.setwarnings(False)         # GPIO 경고 메시지 비활성화
  
# 핀 모드 설정 (입력/출력)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
  
# 초기 출력 상태 설정 (모두 OFF 상태로 초기화)
GPIO.output(TRIG_PIN, GPIO.LOW) 
GPIO.output(LED_PIN, GPIO.LOW)
  
# 센서 및 통신 객체 초기화 (프로그램 시작 시 단 한 번 실행)
  
# I2C 통신 객체 생성 (온습도 센서)
try:
    i2c = busio.I2C(board.SCL, board.SDA) # I2C 버스 객체 생성
    htu_sensor = adafruit_htu21d.HTU21D(i2c) # HTU21D 센서 객체 생성
except Exception as e:
    # 초기화 실패 시, None으로 설정하여 데이터 오류 없이 0을 반환하도록 함
    htu_sensor = None
  
# MCP3202 SPI 통신 객체 생성 및 초기화 (조도 센서 ADC)
spi = spidev.SpiDev() 
try:
    spi.open(0, 0) # SPI 버스 0의 장치 0을 열어 직접 통신 
    spi.max_speed_hz = 1000000 # 통신 속도 설정 (1MHz)
    mcp_ready = True # SPI 통신 플래그
except Exception as e:
    mcp_ready = False # SPI 통신 실패 플래그

# 상태 표시 LED 제어 함수 추가 
def set_led_status(status):
    GPIO.output(LED_PIN, status)
  
#  센서 제어 함수 (개별 센서 데이터 읽기)
# MCP3202 칩으로부터 아날로그 값을 읽는 기능을 함
def read_adc(channel):
  
    if channel == 0:
        # 채널 0, 단일 종단 모드 명령 바이트 설정 (SGL/DIFF와 채널 정보를 묶어 전송)
        adc = spi.xfer2([1, (8+channel)<<4, 0])
    else: 
        adc = spi.xfer2([1, (8+channel)<<4, 0])
        
    # 수신된 데이터(adc[1], adc[2])에서 유효한 12비트만 추출하여 하나의 숫자로 합침
    data = ((adc[1] & 0x0F) << 8) | adc[2]
    return data
  
# GPIO 통신을 사용하여 초음파 센서로 거리를 측정
def measureDistance(trig, echo):
   
    # 1. 펄스 시간 변수 초기화 
    pulse_start = time.time()
    pulse_end = time.time()
    
    # 2. 트리거 펄스 생성
    GPIO.output(trig, GPIO.HIGH) 
    time.sleep(0.00001) 
    GPIO.output(trig, GPIO.LOW)
    
    # 3. 초음파 발사 시간 기록 
    timeout = time.time() + 0.05
    while GPIO.input(echo) == GPIO.LOW and pulse_start < timeout:
        pulse_start = time.time()
        
    # 4. 초음파 수신 시간 기록
    timeout = time.time() + 0.05
    while GPIO.input(echo) == GPIO.HIGH and pulse_end < timeout:
        pulse_end = time.time()
        
    # 5. 거리 계산 (단위: cm)
    pulse_duration = pulse_end - pulse_start 
    distance = pulse_duration * 17150 # 경과 시간 * (음속/2)
    
    return round(distance, 2)
# I2C 통신을 사용하여 HTU21D 센서에서 온도와 습도 값을 읽음
def read_htu_sensor():
   
    if htu_sensor is None: return 0.0, 0.0 # 센서 초기화 실패 시 0 반환
    try:
        temperature = htu_sensor.temperature
        humidity = htu_sensor.relative_humidity
        return humidity, temperature # 습도, 온도 반환
    except Exception:
        return 0.0, 0.0
# MCP3202를 통해 조도 센서(채널 0)의 SPI 통신 값을 읽음
def read_lux_sensor():
    
    global mcp_ready
    if not mcp_ready: return 0 # SPI 초기화 실패 시 0 반환
    try:
        lux_value = read_adc(0) # CH0에서 아날로그 값 읽기
        return lux_value
    except Exception:
        return 0
        
# 함수 이름 변경: read_all_sensors -> read_data
def read_data():
    
    distance = measureDistance(TRIG_PIN, ECHO_PIN)
    humidity, temperature = read_htu_sensor() 
    lux_value = read_lux_sensor()
    
    # TimeStamp 필드 추가
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 딕셔너리 구성 
    sensor_data = {
        "distance": float(f"{distance:.1f}"),
        "temperature": float(f"{temperature:.1f}"),
        "humidity": float(f"{humidity:.1f}"),
        "lux_adc": lux_value,
        "timestamp": current_time # TimeStamp 필드 추가
    }
    return sensor_data
  
# 메인 프로그램 종료 시 호출되어 GPIO 및 SPI 통신을 안전하게 종료
def cleanup():
    if mcp_ready:
        spi.close() # SPI 통신 종료
    GPIO.cleanup() # 사용된 GPIO 핀을 모두 초기 상태로 리셋