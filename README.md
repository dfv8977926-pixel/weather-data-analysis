# Weather Data Collection and Visualization

## 1. 프로젝트 소개
이 프로젝트는 기상자료의 시간별 관측 형식을 학습하고, 자료를 CSV로 정리한 뒤 기온 시계열 그래프를 만드는 Python 실습입니다. 기상청 ASOS 시간자료 API 수집 코드와 API 인증 없이 실행할 수 있는 모의 데이터 실행 방법을 함께 제공합니다.

## 2. 데이터 출처와 정확성 안내
- 참고한 API: 기상청 API허브 종관기상관측(ASOS) 시간자료(기간 조회)
- API 주소: https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php
- 참고 관측소 번호: 108
- 예시 조회 기간: 2025-10-01 00:00 ~ 2025-10-07 23:00 (KST)
- **현재 저장소에 포함된 `weather.csv`와 `temperature.png`는 API에서 내려받은 실제 관측값이 아니라, 코드 실행과 그래프 실습을 위한 모의 데이터입니다.** 실제 관측자료로 오인하지 않도록 구분했습니다.

## 3. 파일 구성
- `collect_weather.py`: 기상청 API 요청 및 CSV 저장, 모의 데이터 생성
- `plot_weather.py`: CSV 읽기, 시간순 정렬, 통계 출력, 기온 그래프 저장
- `weather.csv`: 168시간 모의 데이터
- `temperature.png`: 모의 데이터의 기온 그래프
- `requirements.txt`: 필요한 Python 라이브러리
- `.gitignore`: 불필요하거나 개인적인 파일 제외

## 4. 실행 환경
- Python 3
- Visual Studio Code
- 터미널

## 5. 설치 방법
프로젝트 폴더를 VS Code에서 연 뒤 터미널에서 실행합니다.

```bash
pip3 install -r requirements.txt
```

## 6. API 없이 예시 데이터로 실행하기
기상청 API허브 가입이나 인증키 없이 전체 흐름을 확인할 수 있습니다.

```bash
python3 collect_weather.py --sample
python3 plot_weather.py
```

첫 번째 명령은 2025년 10월 1일부터 7일까지 1시간 간격의 168행 모의 데이터를 `weather.csv`로 저장합니다. 두 번째 명령은 CSV를 읽어 통계를 출력하고 `temperature.png`를 저장합니다.

## 7. 실제 기상청 API로 실행하기
실제 관측자료 수집에는 기상청 API허브 회원가입, 인증키 발급, ASOS 1.2 시간자료(기간 조회) 활용신청이 모두 필요합니다. API 활용신청과 인증키 발급은 별도 절차입니다.

1. https://apihub.kma.go.kr/ 에서 인증키를 확인합니다.
2. ASOS 1.2 시간자료(기간 조회) 활용신청을 완료합니다.
3. `collect_weather.py`에서 조회 기간과 관측소를 필요에 따라 수정합니다.
4. 다음 명령을 실행하고 터미널에 인증키를 입력합니다.

```bash
python3 collect_weather.py
```

인증키는 코드에 직접 입력하지 않습니다. 프로그램이 `getpass`로 실행 중 입력받으며, 인증키와 인증키가 포함된 요청 주소를 출력하지 않습니다. API 요청이 성공하면 실제 응답을 정리해 `weather.csv`와 `raw_response.txt`를 저장합니다.

## 8. CSV 열 설명
| 열 이름 | 의미 | 단위 |
|---|---|---|
| `datetime` | 관측 시각 | KST |
| `temperature_C` | 기온 | °C |
| `humidity_pct` | 상대습도 | % |
| `wind_speed_ms` | 풍속 | m/s |

API 응답은 PDF 실습 자료의 원본 열 번호(TM 1열, WS 4열, TA 12열, HM 14열)를 기준으로 정리합니다. 기온의 음수는 정상값일 수 있으므로 일괄 삭제하지 않습니다.

## 9. 결과 확인
모의 데이터 실행 시 168행이며, 시작 시각은 2025-10-01 00:00, 마지막 시각은 2025-10-07 23:00입니다. 모의 데이터는 재현 가능하도록 난수 시드를 고정했습니다. 실제 API 실행 결과의 행 수와 결측값은 실제 응답에 따라 달라질 수 있습니다.

## 10. 데이터 해석
생성된 기온 그래프에서 하루 중 시간대에 따른 기온의 오르내림을 확인할 수 있습니다. 이 그래프는 모의 데이터의 패턴을 보여주는 학습 결과이며, 실제 2025년 서울의 기온을 설명하는 근거로 사용할 수 없습니다.

## 11. 참고
- 강의자료: 코딩과 응용 Week 7 - API 데이터 수집
- 기상청 API허브: https://apihub.kma.go.kr/
- 기상자료개방포털: https://data.kma.go.kr/
