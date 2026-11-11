import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error


# 예측 결과 파일과 그래프 파일의 이름입니다.
INPUT_FILE = "predictions.csv"
OUTPUT_FILE = "prediction_week.png"

# CSV에 실제로 존재하는 열 이름을 사용합니다.
TIME_COLUMN = "target_time"
ACTUAL_COLUMN = "actual_wind_speed_ms"
PERSISTENCE_COLUMN = "persistence_prediction_ms"
LINEAR_COLUMN = "linear_regression_prediction_ms"


def main():
    # 예측 결과를 읽고 target_time을 날짜/시간 형식으로 변환합니다.
    data = pd.read_csv(INPUT_FILE)
    required_columns = [
        TIME_COLUMN,
        ACTUAL_COLUMN,
        PERSISTENCE_COLUMN,
        LINEAR_COLUMN,
    ]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"{INPUT_FILE}에 필요한 열이 없습니다: {missing_columns}")

    data[TIME_COLUMN] = pd.to_datetime(data[TIME_COLUMN])

    # 파일의 시간은 한국 표준시로 기록되어 있으므로 KST 시간대로 표시합니다.
    if data[TIME_COLUMN].dt.tz is None:
        data[TIME_COLUMN] = data[TIME_COLUMN].dt.tz_localize("Asia/Seoul")
    else:
        data[TIME_COLUMN] = data[TIME_COLUMN].dt.tz_convert("Asia/Seoul")

    # MAE는 그림에 표시할 1주가 아니라 12월 전체 744개 행으로 계산합니다.
    december_start = pd.Timestamp("2024-12-01 00:00:00", tz="Asia/Seoul")
    december_end = pd.Timestamp("2024-12-31 23:00:00", tz="Asia/Seoul")
    if len(data) != 744:
        raise ValueError(f"12월 전체 평가 데이터는 744행이어야 하지만 {len(data)}행입니다.")
    if data[TIME_COLUMN].isna().any():
        raise ValueError("target_time에 비어 있는 값이 있습니다.")
    if data[[ACTUAL_COLUMN, PERSISTENCE_COLUMN, LINEAR_COLUMN]].isna().any().any():
        raise ValueError("실제 풍속 또는 예측 풍속에 비어 있는 값이 있습니다.")
    if data[TIME_COLUMN].min() != december_start or data[TIME_COLUMN].max() != december_end:
        raise ValueError("예측 결과의 target_time이 2024년 12월 전체 범위와 일치하지 않습니다.")

    persistence_mae = mean_absolute_error(
        data[ACTUAL_COLUMN], data[PERSISTENCE_COLUMN]
    )
    linear_mae = mean_absolute_error(data[ACTUAL_COLUMN], data[LINEAR_COLUMN])

    # 그래프에는 12월 1일부터 7일까지의 168시간만 사용합니다.
    week_start = pd.Timestamp("2024-12-01 00:00:00", tz="Asia/Seoul")
    week_end = pd.Timestamp("2024-12-07 23:00:00", tz="Asia/Seoul")
    week_data = data.loc[data[TIME_COLUMN].between(week_start, week_end)].sort_values(
        TIME_COLUMN
    )
    if len(week_data) != 168:
        raise ValueError(f"그래프 구간은 168행이어야 하지만 {len(week_data)}행입니다.")

    # 크기와 글자 크기를 지정하고, 조건에 맞는 세 개의 선을 그립니다.
    fig, ax = plt.subplots(figsize=(14, 6), dpi=120)
    ax.plot(
        week_data[TIME_COLUMN],
        week_data[ACTUAL_COLUMN],
        color="black",
        linestyle="-",
        linewidth=1.8,
        label="Actual wind speed",
    )
    ax.plot(
        week_data[TIME_COLUMN],
        week_data[PERSISTENCE_COLUMN],
        color="gray",
        linestyle="--",
        linewidth=1.6,
        label="Persistence",
    )
    ax.plot(
        week_data[TIME_COLUMN],
        week_data[LINEAR_COLUMN],
        color="blue",
        linestyle="-",
        linewidth=1.6,
        label="Linear Regression",
    )

    # 제목, 축 이름, 범례를 추가해 그래프를 읽기 쉽게 만듭니다.
    ax.set_title("Hourly Wind Speed: Actual vs. Predictions (Dec 1-7, 2024)", fontsize=16)
    ax.set_xlabel("Target time (KST)", fontsize=12)
    ax.set_ylabel("Wind speed (m/s)", fontsize=12)
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.autofmt_xdate()
    fig.tight_layout()

    # 그래프를 새 PNG 파일로 저장합니다. predictions.csv는 변경하지 않습니다.
    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    plt.close(fig)

    # 12월 전체 744개 행을 기준으로 계산한 두 모델의 MAE를 출력합니다.
    print(f"12월 전체 데이터 행 수: {len(data)}")
    print(f"그래프 표시 데이터 행 수 (12/01~12/07): {len(week_data)}")
    print(f"Persistence MAE (12월 전체): {persistence_mae:.4f} m/s")
    print(f"Linear Regression MAE (12월 전체): {linear_mae:.4f} m/s")
    print(f"그래프 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
