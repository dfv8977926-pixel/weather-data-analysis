import pandas as pd


# 시간별 데이터를 읽고, 학습 데이터는 별도 파일로 저장합니다.
INPUT_FILE = "hourly_data.csv"
OUTPUT_FILE = "wind_dataset.csv"
TIME_COLUMN = "datetime"

# 입력값 이름과 실제 원본 열, 예측 시각 기준 과거 시간을 연결합니다.
INPUT_FEATURES = {
    "wind_speed_ms": ("wind_speed_ms", 0),
    "wind_speed_1h_ago_ms": ("wind_speed_ms", 1),
    "wind_speed_2h_ago_ms": ("wind_speed_ms", 2),
    "temperature_C": ("temperature_C", 0),
    "humidity_pct": ("humidity_pct", 0),
}
TARGET_COLUMN = "target_wind_speed_ms"


def main():
    # hourly_data.csv를 읽습니다. 이 입력 파일은 수정하지 않습니다.
    data = pd.read_csv(INPUT_FILE)
    data[TIME_COLUMN] = pd.to_datetime(data[TIME_COLUMN])

    # 시각으로 값을 찾기 때문에 datetime이 중복되면 안전하게 중단합니다.
    if data[TIME_COLUMN].duplicated().any():
        raise ValueError("hourly_data.csv에 중복된 datetime 값이 있습니다.")

    # datetime을 색인으로 사용해 원하는 시각의 관측값을 찾습니다.
    observations = data.set_index(TIME_COLUMN)
    prediction_times = pd.DatetimeIndex(observations.index)
    target_times = prediction_times + pd.Timedelta(hours=1)

    # 각 입력값과 정답은 행의 순서가 아니라 해당 시각을 기준으로 찾습니다.
    dataset = pd.DataFrame(
        {
            "prediction_time": prediction_times,
            "target_time": target_times,
        }
    )
    for feature_name, (source_column, hours_before) in INPUT_FEATURES.items():
        feature_times = prediction_times - pd.Timedelta(hours=hours_before)
        dataset[feature_name] = observations[source_column].reindex(
            feature_times
        ).to_numpy()

    # 정답은 예측 시각보다 정확히 1시간 뒤인 시각의 풍속입니다.
    dataset[TARGET_COLUMN] = observations["wind_speed_ms"].reindex(
        target_times
    ).to_numpy()

    # 예측 시각과 정답 시각의 차이가 정확히 1시간인지 확인합니다.
    if not (dataset["target_time"] - dataset["prediction_time"]).eq(
        pd.Timedelta(hours=1)
    ).all():
        raise ValueError("target_time이 prediction_time보다 정확히 1시간 뒤가 아닙니다.")

    # 입력값이나 정답 중 하나라도 비어 있는 행은 제거합니다.
    required_columns = list(INPUT_FEATURES) + [TARGET_COLUMN]
    dataset = dataset.dropna(subset=required_columns).reset_index(drop=True)

    # 완성된 학습 데이터를 새 CSV 파일로 저장합니다.
    dataset.to_csv(OUTPUT_FILE, index=False)

    # 전체 행 수와 처음 다섯 행을 터미널에 출력합니다.
    print(f"전체 데이터 행 수: {len(dataset)}")
    print("\n처음 5행:")
    print(dataset.head(5).to_string(index=False))

    # 첫 번째 학습 데이터의 시각, 입력값, 정답 풍속을 따로 출력합니다.
    if dataset.empty:
        print("\n유효한 학습 데이터가 없어 첫 번째 데이터가 없습니다.")
    else:
        first_row = dataset.iloc[0]
        print("\n첫 번째 데이터 상세:")
        print(f"예측 시각 (prediction_time): {first_row['prediction_time']}")
        print(f"정답 시각 (target_time): {first_row['target_time']}")
        print("입력값 5개:")
        for feature_name in INPUT_FEATURES:
            print(f"  {feature_name}: {first_row[feature_name]}")
        print(f"정답 풍속 ({TARGET_COLUMN}): {first_row[TARGET_COLUMN]}")


if __name__ == "__main__":
    main()
