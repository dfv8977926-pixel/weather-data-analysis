import pandas as pd


# 입력 원본과 새로 저장할 파일의 이름입니다.
SOURCE_FILE = "asos_108_2023_2024.csv"
OUTPUT_FILE = "hourly_data.csv"
TIME_COLUMN = "datetime"

# 정리할 기간의 시작과 끝을 지정합니다.
START_TIME = "2023-01-01 00:00:00"
END_TIME = "2024-12-31 23:00:00"


def main():
    # 원본 파일은 읽기만 합니다. 저장은 별도의 출력 파일에 합니다.
    data = pd.read_csv(SOURCE_FILE)
    data[TIME_COLUMN] = pd.to_datetime(data[TIME_COLUMN])

    # 시간 목록을 기준으로 데이터를 맞추려면 각 시각이 한 번씩만 있어야 합니다.
    if data[TIME_COLUMN].duplicated().any():
        raise ValueError("원본 CSV에 중복된 datetime 값이 있어 시간별 정리를 중단합니다.")

    # 시작부터 끝까지 빠짐없이 1시간 간격의 시각 목록을 만듭니다.
    expected_times = pd.date_range(start=START_TIME, end=END_TIME, freq="h")
    original_times = pd.DatetimeIndex(data[TIME_COLUMN])
    missing_times = expected_times.difference(original_times)

    # datetime을 색인으로 사용해 빠진 시각의 행을 추가합니다.
    # 기존 빈칸이나 새 행의 관측값은 채우지 않아 NaN으로 남습니다.
    hourly_data = data.set_index(TIME_COLUMN).reindex(expected_times)
    hourly_data.index.name = TIME_COLUMN
    hourly_data = hourly_data.reset_index()

    # 정리된 데이터를 새 파일로 저장하며, 원본 파일은 덮어쓰지 않습니다.
    hourly_data.to_csv(OUTPUT_FILE, index=False)

    # 전체 행 수와 각 열의 빈칸 수를 계산합니다.
    blank_counts = hourly_data.isna().sum()

    # 터미널에 행 수, 누락 시간 수, 각 열의 빈칸 수를 출력합니다.
    print(f"정리 후 전체 행 수: {len(hourly_data)}")
    print(f"정리 전에 누락된 시간 수: {len(missing_times)}")
    print("각 열의 빈칸 수:")
    for column, count in blank_counts.items():
        print(f"  {column}: {count}")

    # 정리된 데이터의 처음 다섯 행을 보여줍니다.
    print("\n처음 5행:")
    print(hourly_data.head(5).to_string(index=False))

    # 연속된 누락 시각들을 구간별로 묶습니다.
    missing_blocks = []
    for timestamp in missing_times:
        if not missing_blocks or timestamp - missing_blocks[-1][-1] != pd.Timedelta(hours=1):
            missing_blocks.append([timestamp])
        else:
            missing_blocks[-1].append(timestamp)

    # 누락 구간 중 처음 세 구간을 골라, 앞뒤 한 시간과 함께 출력합니다.
    print("\n누락된 시간대가 있던 구간 예시 (최대 3개):")
    if not missing_blocks:
        print("누락된 시간대가 없습니다.")
    else:
        for block in missing_blocks[:3]:
            block_start = block[0]
            block_end = block[-1]
            print(f"\n누락 구간: {block_start} ~ {block_end}")
            example_start = max(expected_times[0], block_start - pd.Timedelta(hours=1))
            example_end = min(expected_times[-1], block_end + pd.Timedelta(hours=1))
            example_rows = hourly_data[
                hourly_data[TIME_COLUMN].between(example_start, example_end)
            ]
            print(example_rows.to_string(index=False))


if __name__ == "__main__":
    main()
