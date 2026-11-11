import pandas as pd


# 검사할 CSV 파일과 주요 열 이름을 지정합니다.
CSV_FILE = "asos_108_2023_2024.csv"
TIME_COLUMN = "datetime"
WEATHER_COLUMNS = ["wind_speed_ms", "temperature_C", "humidity_pct"]


def main():
    # CSV 파일을 읽습니다. 원본 파일은 읽기만 하며 변경하지 않습니다.
    data = pd.read_csv(CSV_FILE)

    # 관측 시각을 날짜와 시간 데이터로 변환합니다.
    data[TIME_COLUMN] = pd.to_datetime(data[TIME_COLUMN])

    # 전체 행 수와 관측 기간의 시작 및 끝을 계산합니다.
    row_count = len(data)
    first_time = data[TIME_COLUMN].min()
    last_time = data[TIME_COLUMN].max()

    # 처음 나온 시각은 제외하고, 중복된 관측 시각의 추가 행 수를 셉니다.
    duplicate_time_count = data[TIME_COLUMN].duplicated().sum()

    # 처음부터 마지막까지 1시간 간격으로 있어야 할 시각을 만듭니다.
    expected_times = pd.date_range(start=first_time, end=last_time, freq="h")
    observed_times = pd.DatetimeIndex(data[TIME_COLUMN].drop_duplicates())
    missing_time_count = len(expected_times.difference(observed_times))

    # 풍속, 기온, 습도 열에서 값이 비어 있는 칸의 수를 각각 셉니다.
    blank_counts = data[WEATHER_COLUMNS].isna().sum()

    # 데이터의 처음 세 행을 출력합니다.
    print("처음 3행:")
    print(data.head(3).to_string(index=False))

    # 요청한 검사 결과를 터미널에 출력합니다.
    print("\n검사 결과:")
    print(f"전체 행 수: {row_count}")
    print(f"처음 관측 시각: {first_time}")
    print(f"마지막 관측 시각: {last_time}")
    print(f"중복 관측 시각 수: {duplicate_time_count}")
    print(f"1시간 간격 기준 누락된 시각 수: {missing_time_count}")
    print("빈칸 수:")
    print(f"  풍속 ({WEATHER_COLUMNS[0]}): {blank_counts[WEATHER_COLUMNS[0]]}")
    print(f"  기온 ({WEATHER_COLUMNS[1]}): {blank_counts[WEATHER_COLUMNS[1]]}")
    print(f"  습도 ({WEATHER_COLUMNS[2]}): {blank_counts[WEATHER_COLUMNS[2]]}")


if __name__ == "__main__":
    main()
