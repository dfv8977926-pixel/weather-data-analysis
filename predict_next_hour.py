import pandas as pd
from sklearn.linear_model import LinearRegression


# 관측 자료와 학습 자료를 읽고 예측 결과는 새 파일에 저장합니다.
HOURLY_FILE = "hourly_data.csv"
TRAIN_FILE = "train_dataset.csv"
OUTPUT_FILE = "next_hour_prediction.csv"

# 학습에 사용할 입력 열과 정답 열의 실제 이름입니다.
FEATURE_COLUMNS = [
    "wind_speed_ms",
    "wind_speed_1h_ago_ms",
    "wind_speed_2h_ago_ms",
    "temperature_C",
    "humidity_pct",
]
TARGET_COLUMN = "target_wind_speed_ms"

# 모델 입력값을 만들 때 확인할 관측 시각을 지정합니다.
LATEST_TIME = pd.Timestamp("2024-12-31 23:00:00")
TARGET_TIME = pd.Timestamp("2025-01-01 00:00:00")


def main():
    # 관측 데이터와 훈련 데이터만 읽습니다. 어떤 입력 파일도 수정하지 않습니다.
    hourly_data = pd.read_csv(HOURLY_FILE, parse_dates=["datetime"])
    train_data = pd.read_csv(
        TRAIN_FILE, parse_dates=["prediction_time", "target_time"]
    )

    # 파일에 필요한 실제 열 이름이 모두 있는지 확인합니다.
    if "datetime" not in hourly_data.columns:
        raise ValueError(f"{HOURLY_FILE}에 datetime 열이 없습니다.")
    missing_features = [name for name in FEATURE_COLUMNS if name not in train_data.columns]
    if missing_features or TARGET_COLUMN not in train_data.columns:
        raise ValueError(
            f"{TRAIN_FILE}에 필요한 학습 열이 없습니다: "
            f"{missing_features + ([TARGET_COLUMN] if TARGET_COLUMN not in train_data.columns else [])}"
        )

    # 학습 데이터가 2024년 11월 30일까지인지 확인해 이후 자료의 학습 사용을 막습니다.
    training_cutoff = pd.Timestamp("2024-11-30 23:00:00")
    if train_data["target_time"].max() > training_cutoff:
        raise ValueError("훈련 데이터에 2024년 11월 30일 이후의 행이 포함되어 있습니다.")
    if train_data[FEATURE_COLUMNS + [TARGET_COLUMN]].isna().any().any():
        raise ValueError("훈련 데이터에 입력값 또는 정답의 빈칸이 있습니다.")

    # 모델 학습에는 train_dataset.csv의 입력값과 정답만 사용합니다.
    model = LinearRegression()
    model.fit(train_data[FEATURE_COLUMNS], train_data[TARGET_COLUMN])

    # 지정된 관측 시각이 중복되지 않는지 확인하고 시각별 값을 찾습니다.
    if hourly_data["datetime"].duplicated().any():
        raise ValueError(f"{HOURLY_FILE}에 중복된 datetime 값이 있습니다.")
    observations = hourly_data.set_index("datetime")

    # 예측 시각 및 필요한 입력값 각각의 관측 행을 지정해 가져옵니다.
    required_times = [
        LATEST_TIME,
        LATEST_TIME - pd.Timedelta(hours=1),
        LATEST_TIME - pd.Timedelta(hours=2),
    ]
    missing_times = [time for time in required_times if time not in observations.index]
    if missing_times:
        raise ValueError(f"필요한 관측 시각이 {HOURLY_FILE}에 없습니다: {missing_times}")

    latest = observations.loc[LATEST_TIME]
    one_hour_ago = observations.loc[LATEST_TIME - pd.Timedelta(hours=1)]
    two_hours_ago = observations.loc[LATEST_TIME - pd.Timedelta(hours=2)]
    input_values = {
        "wind_speed_ms": latest["wind_speed_ms"],
        "wind_speed_1h_ago_ms": one_hour_ago["wind_speed_ms"],
        "wind_speed_2h_ago_ms": two_hours_ago["wind_speed_ms"],
        "temperature_C": latest["temperature_C"],
        "humidity_pct": latest["humidity_pct"],
    }

    # 입력값이 모두 실제 관측값과 일치하는지 원본 행으로 교차 확인합니다.
    expected_values = {
        "wind_speed_ms": latest["wind_speed_ms"],
        "wind_speed_1h_ago_ms": observations.loc[
            LATEST_TIME - pd.Timedelta(hours=1), "wind_speed_ms"
        ],
        "wind_speed_2h_ago_ms": observations.loc[
            LATEST_TIME - pd.Timedelta(hours=2), "wind_speed_ms"
        ],
        "temperature_C": latest["temperature_C"],
        "humidity_pct": latest["humidity_pct"],
    }
    for feature_name in FEATURE_COLUMNS:
        if pd.isna(input_values[feature_name]) or input_values[feature_name] != expected_values[feature_name]:
            raise ValueError(f"입력값 {feature_name}이 관측 데이터와 일치하지 않습니다.")

    # 결측 입력을 임의로 채우지 않고, 있으면 예측을 중단합니다.
    model_input = pd.DataFrame([input_values], columns=FEATURE_COLUMNS)
    if model_input.isna().any().any():
        raise ValueError("예측 입력값에 빈칸이 있어 예측을 중단합니다.")

    # 학습한 모델로 다음 시간의 풍속을 예측하고 음수이면 0으로 바꿉니다.
    predicted_wind_speed = float(model.predict(model_input)[0])
    predicted_wind_speed = max(0.0, predicted_wind_speed)

    # 예측 대상 시각, 입력값과 최종 예측값을 새 CSV 파일로 저장합니다.
    result = pd.DataFrame(
        [
            {
                "target_time": TARGET_TIME,
                **input_values,
                "predicted_wind_speed_ms": predicted_wind_speed,
            }
        ]
    )
    result.to_csv(OUTPUT_FILE, index=False)

    # 예측 대상 시각과 사용한 입력값, 최종 예측 풍속을 출력합니다.
    print(f"예측 대상 시각: {TARGET_TIME}")
    print("사용한 입력값 5개 (hourly_data.csv 관측값 확인 완료):")
    for feature_name in FEATURE_COLUMNS:
        print(f"  {feature_name}: {input_values[feature_name]}")
    print(f"최종 예측 풍속: {predicted_wind_speed:.4f} m/s")
    print(f"결과 저장 파일: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
