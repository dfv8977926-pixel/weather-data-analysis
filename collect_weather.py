"""
collect_weather.py
기상청 ASOS 시간자료 수집 프로그램

기본 실행: python3 collect_weather.py
오프라인 예시자료 생성: python3 collect_weather.py --sample

주의:
- --sample은 과제 실행 연습용 모의 데이터이며 실제 관측자료가 아닙니다.
- 실제 API 수집에는 기상청 API허브 인증키와 ASOS 1.2 시간자료(기간 조회) 활용신청이 필요합니다.
- 인증키는 실행 중 터미널에서만 입력하며 코드/로그에 저장하지 않습니다.
"""
import argparse
import getpass
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
API_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
STATION = "108"
START_TIME = "202510010000"
END_TIME = "202510072300"
OUTPUT_CSV = BASE_DIR / "weather.csv"
RAW_OUTPUT = BASE_DIR / "raw_response.txt"
COLUMNS = ["datetime", "temperature_C", "humidity_pct", "wind_speed_ms"]


def generate_sample_data():
    """168시간 분량의 재현 가능한 모의 데이터를 생성합니다."""
    import numpy as np

    np.random.seed(42)
    times = pd.date_range("2025-10-01 00:00", "2025-10-07 23:00", freq="h")
    rows = []
    for i, timestamp in enumerate(times):
        hour = timestamp.hour
        day_effect = 0.7 * np.sin((timestamp.day - 1) * 2 * np.pi / 7)
        daily_cycle = 3.8 * np.sin((hour - 9) * 2 * np.pi / 24)
        temperature = 20.0 + day_effect + daily_cycle + np.random.normal(0, 0.75)
        humidity = np.clip(66 - 1.8 * (temperature - 20) + np.random.normal(0, 4), 30, 95)
        wind = np.clip(np.random.gamma(shape=2.0, scale=0.7), 0.1, 7.0)
        rows.append({
            "datetime": timestamp,
            "temperature_C": round(float(temperature), 1),
            "humidity_pct": round(float(humidity), 1),
            "wind_speed_ms": round(float(wind), 1),
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print("모의 데이터 저장 완료:", OUTPUT_CSV)
    print("주의: 이 자료는 실제 기상청 관측값이 아닌 학습용 모의 데이터입니다.")
    report_summary(df)
    return df


def parse_api_response(raw_text):
    """PDF에 제시된 원본 열 번호(TM 1, WS 4, TA 12, HM 14)를 추출합니다."""
    rows = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 14:
            continue
        if not (parts[0].isdigit() and len(parts[0]) == 12):
            continue
        try:
            timestamp = datetime.strptime(parts[0], "%Y%m%d%H%M")
        except ValueError:
            continue
        rows.append({
            "datetime": timestamp,
            "temperature_C": parts[11],  # TA: 12번째 열
            "humidity_pct": parts[13],    # HM: 14번째 열
            "wind_speed_ms": parts[3],    # WS: 4번째 열
        })

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(rows, columns=COLUMNS)
    for column in COLUMNS[1:]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime")
    duplicate_count = int(df.duplicated(subset=["datetime"]).sum())
    if duplicate_count:
        print("중복 관측 시각:", duplicate_count, "- 첫 번째 자료를 사용합니다.")
        df = df.drop_duplicates(subset=["datetime"], keep="first")
    return df.reset_index(drop=True)


def report_summary(df):
    print("\n===== 저장 결과 확인 =====")
    print("데이터 행 수:", len(df))
    print("\n열별 결측값:")
    print(df.isna().sum().to_string())
    if not df.empty:
        print("\n첫 관측 시각:", df["datetime"].min())
        print("마지막 관측 시각:", df["datetime"].max())
        print("중복 관측 시각:", int(df.duplicated(subset=["datetime"]).sum()))
    print("저장 위치:", OUTPUT_CSV)


def collect_from_api():
    """기상청 API에 요청합니다. 인증키 및 인증키가 포함된 URL은 출력하지 않습니다."""
    auth_key = getpass.getpass("기상청 API 인증키를 입력하세요: ").strip()
    if not auth_key:
        print("인증키가 입력되지 않았습니다.")
        return False

    params = {
        "tm1": START_TIME,
        "tm2": END_TIME,
        "stn": STATION,
        "help": "1",
        "authKey": auth_key,
    }
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        if not response.encoding:
            response.encoding = response.apparent_encoding
        print("HTTP 상태 코드:", response.status_code)

        if response.status_code != 200:
            body = response.text.replace(auth_key, "[인증키 숨김]")
            print("요청 실패 본문:", body[:1000])
            if response.status_code == 403:
                print("해결 방법: API허브에서 ASOS 1.2 시간자료(기간 조회) 활용신청 여부를 확인하세요.")
            elif response.status_code == 401:
                print("해결 방법: 인증키가 올바른지 확인하세요.")
            return False

        response.raise_for_status()
        raw_text = response.text
        if not raw_text.strip():
            print("응답 본문이 비어 있습니다.")
            return False

        # 원본 응답의 앞부분과 실제 자료 일부를 확인합니다.
        lines = raw_text.splitlines()
        print("\n[응답 본문 앞 15줄]")
        for line in lines[:15]:
            print(line.replace(auth_key, "[인증키 숨김]"))
        data_lines = [
            line for line in lines
            if line.strip() and not line.lstrip().startswith("#")
            and len(line.split()) >= 14
            and line.split()[0].isdigit()
            and len(line.split()[0]) == 12
        ]
        print("\n[실제 데이터 행 3개]")
        for line in data_lines[:3]:
            print(line)

        df = parse_api_response(raw_text)
        if df.empty:
            print("정리할 관측자료가 없습니다. 조회 기간과 API 응답 형식을 확인하세요.")
            return False

        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        # 응답 본문만 저장하며 요청 URL/인증키는 저장하지 않습니다.
        RAW_OUTPUT.write_text(raw_text, encoding="utf-8")
        report_summary(df)
        print("\n원본 응답 저장 위치:", RAW_OUTPUT)
        return True

    except requests.exceptions.Timeout:
        print("요청 시간이 초과되었습니다. 인터넷 연결 또는 조회 기간을 확인하세요.")
    except requests.exceptions.RequestException as exc:
        # 예외 문자열에는 URL이 포함될 수 있으므로 출력하지 않습니다.
        print("API 요청 중 통신 오류가 발생했습니다:", type(exc).__name__)
    return False


def main():
    parser = argparse.ArgumentParser(description="기상청 ASOS 시간자료 수집")
    parser.add_argument(
        "--sample", action="store_true",
        help="실제 API 대신 학습용 모의 데이터 168행을 생성합니다."
    )
    args = parser.parse_args()
    if args.sample:
        generate_sample_data()
    else:
        collect_from_api()


if __name__ == "__main__":
    main()
