import pandas as pd


# 원본 학습 데이터와 분리 후 저장할 파일 이름입니다.
INPUT_FILE = "wind_dataset.csv"
TRAIN_FILE = "train_dataset.csv"
TEST_FILE = "test_dataset.csv"
TIME_COLUMN = "target_time"

# 학습 및 테스트에 포함할 target_time의 시작과 끝입니다.
TRAIN_START = pd.Timestamp("2023-01-01 00:00:00")
TRAIN_END = pd.Timestamp("2024-11-30 23:00:00")
TEST_START = pd.Timestamp("2024-12-01 00:00:00")
TEST_END = pd.Timestamp("2024-12-31 23:00:00")


def main():
    # 원본 파일은 읽기만 하며 변경하지 않습니다.
    data = pd.read_csv(INPUT_FILE, parse_dates=[TIME_COLUMN])

    # 날짜 기준 분리를 위해 target_time이 모두 있는지 확인합니다.
    if data[TIME_COLUMN].isna().any():
        raise ValueError("target_time이 비어 있는 행이 있습니다.")

    # 무작위 섞기 없이 target_time의 지정된 범위로 각각 분리합니다.
    train_mask = data[TIME_COLUMN].between(TRAIN_START, TRAIN_END, inclusive="both")
    test_mask = data[TIME_COLUMN].between(TEST_START, TEST_END, inclusive="both")
    train_data = data.loc[train_mask].copy()
    test_data = data.loc[test_mask].copy()

    # 출력 전에 범위, 데이터 누락 및 두 구간 간 겹침이 없는지 확인합니다.
    outside_ranges = ~(train_mask | test_mask)
    if outside_ranges.any():
        raise ValueError(
            f"지정된 학습/테스트 기간 바깥의 데이터가 "
            f"{outside_ranges.sum()}행 있습니다."
        )
    if (train_mask & test_mask).any():
        raise ValueError("학습 데이터와 테스트 데이터의 기간이 겹칩니다.")
    if len(train_data) + len(test_data) != len(data):
        raise ValueError("분리 후 행 수가 원본 행 수와 일치하지 않습니다.")
    if not train_data[TIME_COLUMN].between(TRAIN_START, TRAIN_END).all():
        raise ValueError("학습 데이터에 지정 범위 밖의 target_time이 있습니다.")
    if not test_data[TIME_COLUMN].between(TEST_START, TEST_END).all():
        raise ValueError("테스트 데이터에 지정 범위 밖의 target_time이 있습니다.")

    # 각 데이터셋을 별도 파일로 저장합니다. 입력 wind_dataset.csv는 그대로 둡니다.
    train_data.to_csv(TRAIN_FILE, index=False)
    test_data.to_csv(TEST_FILE, index=False)

    # 각 파일의 행 수와 target_time의 첫 번째/마지막 시각을 출력합니다.
    print("학습 데이터:")
    print(f"  행 수: {len(train_data)}")
    print(f"  첫 번째 target_time: {train_data[TIME_COLUMN].min()}")
    print(f"  마지막 target_time: {train_data[TIME_COLUMN].max()}")

    print("\n테스트 데이터:")
    print(f"  행 수: {len(test_data)}")
    print(f"  첫 번째 target_time: {test_data[TIME_COLUMN].min()}")
    print(f"  마지막 target_time: {test_data[TIME_COLUMN].max()}")

    # 테스트 데이터의 첫 행에서 예측 시각과 정답 시각을 따로 출력합니다.
    if test_data.empty:
        print("\n테스트 데이터가 없어 첫 번째 행의 시각을 출력할 수 없습니다.")
    else:
        first_test_row = test_data.iloc[0]
        print("\n테스트 데이터 첫 번째 행:")
        print(f"  prediction_time: {first_test_row['prediction_time']}")
        print(f"  target_time: {first_test_row[TIME_COLUMN]}")

    print("\n검증 성공: 날짜 범위가 정확하며, 행 누락이나 학습/테스트 구간 겹침이 없습니다.")


if __name__ == "__main__":
    main()
