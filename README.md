# 📬 Smart Mailbox (스마트 우편함 모니터링 시스템)

> 라즈베리파이와 MQTT를 활용한 IoT 스마트 우편함 시스템 (2학년 2학기 프로젝트 | 2025.12)

---

## 📖 프로젝트 소개

기존 우편함의 불편함(수시로 직접 확인, 분실 위험 인지 어려움)을 해결하기 위해 개발한 IoT 프로젝트입니다.
다양한 센서로 우편함 상태를 실시간 감지하고, 웹 대시보드를 통해 어디서든 확인 및 원격 제어가 가능합니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 실시간 모니터링 | 초음파/조도/온습도 센서로 우편함 상태 실시간 감지 |
| 상태 알림 | 택배 도착, 문 열림 등 4가지 상태 감지 및 웹 알림 |
| 웹 대시보드 | Flask 기반 대시보드에서 센서 데이터 0.5초마다 갱신 |
| 원격 제어 | 웹에서 [우편물 확인 완료] 버튼으로 알림 상태 원격 리셋 |
| 양방향 통신 | MQTT Publish/Subscribe로 디바이스-웹 서버 간 양방향 통신 구현 |

---

## 🔌 시스템 구성

```
[센서들] → [Raspberry Pi] → [MQTT Broker] → [Flask Web Server] → [브라우저]
```

| 부품 | 용도 |
|------|------|
| HC-SR04 (초음파) | 우편물 유무 감지 (14.0cm 임계값) |
| CDS (조도 센서) | 우편함 문 열림 감지 |
| HTU21D (온습도) | 우편함 내부 환경 데이터 수집 |
| MCP3202 ADC | 조도 센서 아날로그 → 디지털 변환 (SPI 통신) |
| LED | 경고 상태 시각적 알림 |

---

## 📊 우편함 상태 분류

| 상태 | 조건 |
|------|------|
| 정상 (대기 중) | 거리 >= 14cm, 조도 <= 100 |
| 택배 도착 | 거리 < 14cm, 조도 <= 100 |
| 문 열림 (물품 있음) | 거리 < 14cm, 조도 > 100 |
| 문 열림 (물품 없음) | 거리 >= 14cm, 조도 > 100 |

---

## 🛠️ 기술 스택

- **Hardware**: Raspberry Pi 4 Model B, HC-SR04, HTU21D, CDS, MCP3202, LED
- **통신**: MQTT (Mosquitto Broker), GPIO, I2C, SPI
- **Backend**: Python, Flask, paho-mqtt
- **Frontend**: HTML, JavaScript (Fetch API)

---

## 📁 파일 구조

```
smart-mailbox/
├── hardware_core.py      # 센서 데이터 수집 (초음파, 온습도, 조도)
├── alert_processor.py    # 우편함 상태 판단 및 알림 메시지 생성
├── mqtt_client.py        # MQTT 브로커 연결, Publish/Subscribe
├── main_publisher.py     # 메인 루프 - 센서 수집 및 MQTT 발행
├── web_server.py         # Flask 웹 서버 및 API 엔드포인트
└── dashboard.html        # 실시간 모니터링 웹 대시보드
```

---

## 🚀 실행 방법

```bash
# 1. MQTT 브로커 실행
mosquitto -v -c mos.conf

# 2. 센서 데이터 수집 및 발행 시작
python main_publisher.py

# 3. 웹 서버 실행
python web_server.py

# 4. 브라우저에서 접속
http://192.168.x.x:8000
```

---

## 🎥 시연 영상

[![시연 영상](https://img.shields.io/badge/YouTube-시연영상-red)](https://youtu.be/LHyCiVZdbWs)
