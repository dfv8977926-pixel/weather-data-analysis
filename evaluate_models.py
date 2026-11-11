import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


# 학습/테스트 입력 파일과 예측 결과 파일 이름입니다.
TRAIN_FILE = "train_dataset.csv"
TEST_FILE = "test_dataset.csv"
OUTPUT_FILE = "predictions.csv"

# CSV에서 확인한 실제 열 이름을 그대로 사용합니다.
FEATURE_COLUMNS = [
    "wind_speed_ms",
    "wind_speed_1h_ago_ms",
    "wind_speed_2h_ago_ms",
    "temperature_C",
    "humidity_pct",
]
TARGET_COLUMN = "target_wind_speed_ms"


def main():
    # 두 파일을 각각 읽습니다. 학습 데이터와 테스트 데이터는 섞지 않습니다.
    train_data = pd.read_csv(TRAIN_FILE, parse_dates=["prediction_time", "target_time"])
    test_data = pd.read_csv(TEST_FILE, parse_dates=["prediction_time", "target_time"])

    # 필요한 실제 열 이름이 파일에 모두 들어 있는지 확인합니다.
    required_columns = [
        "prediction_time",
        "target_time",
        *FEATURE_COLUMNS,
        TARGET_COLUMN,
    ]
    for file_name, data in [(TRAIN_FILE, train_data), (TEST_FILE, test_data)]:
        missing_columns = [column for column in required_columns if column not in data.columns]
        if missing_columns:
            raise ValueError(f"{file_name}에 필요한 열이 없습니다: {missing_columns}")

    # 회귀 모델이 사용할 입력값과 정답에 빈칸이 없는지 확인합니다.
    model_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    if train_data[model_columns].isna().any().any():
        raise ValueError("학습 데이터의 입력값 또는 정답에 빈칸이 있습니다.")
    if test_data[model_columns].isna().any().any():
        raise ValueError("테스트 데이터의 입력값 또는 정답에 빈칸이 있습니다.")

    # 지정된 과제 데이터가 온전히 들어왔는지 확인합니다.
    if len(test_data) != 744:
        raise ValueError(f"테스트 데이터는 744행이어야 하지만 {len(test_data)}행입니다.")

    # 날짜가 분리되어 있어 학습 데이터가 테스트 데이터보다 앞서는지 확인합니다.
    if train_data["target_time"].max() >= test_data["target_time"].min():
        raise ValueError("학습 데이터와 테스트 데이터의 날짜 범위가 겹치거나 순서가 잘못되었습니다.")

    # 두 시각 사이의 예측 간격이 정확히 1시간인지 확인합니다.
    for file_name, data in [(TRAIN_FILE, train_data), (TEST_FILE, test_data)]:
        one_hour_ahead = data["target_time"] - data["prediction_time"]
        if not one_hour_ahead.eq(pd.Timedelta(hours=1)).all():
            raise ValueError(f"{file_name}에 1시간 예측이 아닌 행이 있습니다.")

    # 정답을 분리합니다. 모델 학습에는 학습 파일의 입력과 정답만 전달합니다.
    X_train = train_data[FEATURE_COLUMNS]
    y_train = train_data[TARGET_COLUMN]
    X_test = test_data[FEATURE_COLUMNS]
    y_test = test_data[TARGET_COLUMN]

    # 기준 모델은 현재 풍속을 1시간 뒤 풍속의 예측값으로 사용합니다.
    persistence_predictions = test_data["wind_speed_ms"].to_numpy()

    # 선형 회귀 모델은 학습 데이터만으로 학습한 뒤 테스트 데이터를 예측합니다.
    model = LinearRegression()
    model.fit(X_train, y_train)
    linear_predictions = model.predict(X_test)

    # 풍속이 음수가 되지 않도록 선형 회귀 예측의 최솟값을 0으로 제한합니다.
    linear_predictions = linear_predictions.clip(min=0)

    # 두 예측 방법의 오차를 동일한 테스트 정답으로 계산합니다.
    persistence_mae = mean_absolute_error(y_test, persistence_predictions)
    linear_mae = mean_absolute_error(y_test, linear_predictions)

    # 시각, 실제 풍속, 두 모델의 예측값을 새 파일에 저장합니다.
    predictions = pd.DataFrame(
        {
            "prediction_time": test_data["prediction_time"],
            "target_time": test_data["target_time"],
            "actual_wind_speed_ms": y_test,
            "persistence_prediction_ms": persistence_predictions,
            "linear_regression_prediction_ms": linear_predictions,
        }
    )
    predictions.to_csv(OUTPUT_FILE, index=False)

    # 각 데이터 행 수와 모델 평가 결과를 터미널에 출력합니다.
    print(f"학습 데이터 행 수: {len(train_data)}")
    print(f"테스트 데이터 행 수: {len(test_data)}")
    print(f"Persistence MAE: {persistence_mae:.4f}")
    print(f"LinearRegression MAE: {linear_mae:.4f}")

    # 첫 번째 테스트 행의 실제 풍속과 두 모델의 예측값을 출력합니다.
    first_prediction = predictions.iloc[0]
    print("\n첫 번째 테스트 데이터:")
    print(f"예측 시각: {first_prediction['prediction_time']}")
    print(f"정답 시각: {first_prediction['target_time']}")
    print(f"실제 풍속: {first_prediction['actual_wind_speed_ms']:.4f}")
    print(f"기준 모델 예측 풍속: {first_prediction['persistence_prediction_ms']:.4f}")
    print(
        "선형 회귀 예측 풍속: "
        f"{first_prediction['linear_regression_prediction_ms']:.4f}"
    )


if __name__ == "__main__":
    main()
