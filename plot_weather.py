"""
plot_weather.py
weather.csv를 읽어 기온 시계열 그래프를 만들고 기본 통계를 출력합니다.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "weather.csv"
IMAGE_PATH = BASE_DIR / "temperature.png"


def main():
    if not CSV_PATH.exists():
        print("weather.csv 파일이 없습니다.")
        print("먼저 python3 collect_weather.py --sample 을 실행하거나 실제 API를 수집하세요.")
        return

    df = pd.read_csv(CSV_PATH)
    required = {"datetime", "temperature_C", "humidity_pct", "wind_speed_ms"}
    missing_columns = required - set(df.columns)
    if missing_columns:
        print("CSV에 필요한 열이 없습니다:", ", ".join(sorted(missing_columns)))
        return

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    for column in ["temperature_C", "humidity_pct", "wind_speed_ms"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["datetime"]).sort_values("datetime")
    if df.empty:
        print("그래프를 그릴 수 있는 시간 자료가 없습니다.")
        return

    # 누락된 시각은 빈 행으로 보충하여 그래프 선이 끊어지게 합니다.
    df = df.set_index("datetime")
    hourly_index = pd.date_range(df.index.min(), df.index.max(), freq="h")
    df = df.reindex(hourly_index)

    print("===== 기상자료 요약 =====")
    print("데이터 행 수:", len(df))
    print("기온 결측 수:", int(df["temperature_C"].isna().sum()))
    print("평균 기온:", round(df["temperature_C"].mean(), 2), "°C")
    print("최고 기온:", round(df["temperature_C"].max(), 2), "°C")
    print("최저 기온:", round(df["temperature_C"].min(), 2), "°C")
    print("평균 습도:", round(df["humidity_pct"].mean(), 2), "%")
    print("평균 풍속:", round(df["wind_speed_ms"].mean(), 2), "m/s")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["temperature_C"], label="Temperature", linewidth=1.5)
    ax.set_title("Temperature over time")
    ax.set_xlabel("Time (KST)")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(IMAGE_PATH, dpi=150)
    print("\n그래프 저장 완료:", IMAGE_PATH)
    plt.show()


if __name__ == "__main__":
    main()
