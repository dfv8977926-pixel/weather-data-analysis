import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


# 읽어 올 파일과 날짜 및 풍속 열 이름을 지정합니다.
INPUT_FILE = "wind_dataset.csv"
PREDICTION_TIME_COLUMN = "prediction_time"
TARGET_TIME_COLUMN = "target_time"
WIND_SPEED_COLUMN = "target_wind_speed_ms"
FEATURE_COLUMNS = [
    "wind_speed_ms",
    "wind_speed_1h_ago_ms",
    "wind_speed_2h_ago_ms",
    "temperature_C",
    "humidity_pct",
]
OUTPUT_FILE = "classification_predictions.csv"
SCORES_FILE = "classification_scores.csv"

# 학습 데이터는 2023-01-01부터 2024-11-30까지 사용합니다.
TRAIN_START = pd.Timestamp("2023-01-01")
EVALUATION_START = pd.Timestamp("2024-12-01")

# 평가 데이터는 2024-12-01부터 2024-12-31까지 사용합니다.
EVALUATION_END = pd.Timestamp("2025-01-01")


def main():
    # 두 시간 열을 날짜와 시간으로 읽어 옵니다.
    data = pd.read_csv(
        INPUT_FILE,
        parse_dates=[PREDICTION_TIME_COLUMN, TARGET_TIME_COLUMN],
    )

    # 정답 풍속이 4.0 m/s 이상이면 1, 아니면 0으로 표시합니다.
    data["strong_wind"] = (data[WIND_SPEED_COLUMN] >= 4.0).astype(int)

    # 정답 시각을 기준으로 이른 시간부터 정렬합니다.
    data = data.sort_values(TARGET_TIME_COLUMN).reset_index(drop=True)

    # 예측 시각과 정답 시각의 차이가 모두 정확히 1시간인지 확인합니다.
    time_difference = data[TARGET_TIME_COLUMN] - data[PREDICTION_TIME_COLUMN]
    invalid_time_rows = time_difference != pd.Timedelta(hours=1)
    if invalid_time_rows.any():
        raise SystemExit(
            f"오류: prediction_time과 target_time의 차이가 1시간이 아닌 "
            f"행이 {invalid_time_rows.sum()}개 있습니다."
        )

    # 정답 시각이 지정된 날짜 범위에 들어가는 행만 각각 선택합니다.
    train_data = data.loc[
        (data[TARGET_TIME_COLUMN] >= TRAIN_START)
        & (data[TARGET_TIME_COLUMN] < EVALUATION_START)
    ].copy()
    evaluation_data = data.loc[
        (data[TARGET_TIME_COLUMN] >= EVALUATION_START)
        & (data[TARGET_TIME_COLUMN] < EVALUATION_END)
    ].copy()

    # 요청한 12월 데이터가 정확히 744행인지 확인합니다.
    if len(evaluation_data) != 744:
        raise ValueError(
            f"평가 데이터는 744행이어야 하지만 {len(evaluation_data)}행입니다."
        )

    # 학습 데이터와 평가 데이터의 전체 행 수 및 클래스별 개수를 출력합니다.
    for data_name, split_data in [
        ("학습 데이터", train_data),
        ("평가 데이터", evaluation_data),
    ]:
        class_counts = split_data["strong_wind"].value_counts().reindex(
            [0, 1], fill_value=0
        )
        print(f"{data_name}:")
        print(f"  전체 행 수: {len(split_data)}")
        print(f"  strong_wind가 0인 행 수: {class_counts[0]}")
        print(f"  strong_wind가 1인 행 수: {class_counts[1]}")

    # 평가 데이터에서 가장 이른 시각의 행을 출력합니다.
    print("\n평가 데이터의 첫 번째 행:")
    if evaluation_data.empty:
        print("평가 데이터가 없습니다.")
    else:
        print(evaluation_data.iloc[0])

    # 모델 학습에는 지정한 5개 입력 열과 학습 기간의 정답만 사용합니다.
    train_features = train_data[FEATURE_COLUMNS]
    train_labels = train_data["strong_wind"]
    evaluation_features = evaluation_data[FEATURE_COLUMNS]

    # 표준화 기준은 학습 데이터에서만 계산하고, 그 기준을 평가 데이터에 적용합니다.
    scaler = StandardScaler()
    train_features_scaled = scaler.fit_transform(train_features)
    evaluation_features_scaled = scaler.transform(evaluation_features)

    # 로지스틱 회귀 모델도 학습 데이터만 사용해 학습합니다.
    model = LogisticRegression(max_iter=1000)
    model.fit(train_features_scaled, train_labels)

    # 비교를 위해 항상 0을 예측하는 방법과 현재 풍속 기준 예측을 만듭니다.
    always_zero_prediction = pd.Series(0, index=evaluation_data.index)
    current_wind_prediction = (
        evaluation_data["wind_speed_ms"] >= 4.0
    ).astype(int)

    # 평가 데이터의 강풍 확률을 구하고, 0.50 이상이면 강풍으로 예측합니다.
    strong_wind_probability = model.predict_proba(evaluation_features_scaled)[:, 1]
    logistic_prediction = (strong_wind_probability >= 0.50).astype(int)

    # 결과 파일에는 요청한 시각, 실제 값, 비교 예측값만 저장합니다.
    predictions = pd.DataFrame(
        {
            "prediction_time": evaluation_data[PREDICTION_TIME_COLUMN],
            "target_time": evaluation_data[TARGET_TIME_COLUMN],
            "실제 풍속(target_wind_speed_ms)": evaluation_data[WIND_SPEED_COLUMN],
            "실제 정답(strong_wind)": evaluation_data["strong_wind"],
            "현재 풍속(wind_speed_ms)": evaluation_data["wind_speed_ms"],
            "항상 0 예측": always_zero_prediction,
            "현재 상태 유지 예측": current_wind_prediction,
            "로지스틱 회귀 강풍 확률": strong_wind_probability,
            "로지스틱 회귀 최종 예측": logistic_prediction,
        }
    )
    predictions.to_csv(OUTPUT_FILE, index=False)

    # 저장된 CSV 파일을 다시 읽어 실제 파일의 첫 5행을 출력합니다.
    saved_predictions = pd.read_csv(OUTPUT_FILE)
    print(f"\n예측 결과를 {OUTPUT_FILE} 파일로 저장했습니다.")
    print("\n예측 결과 첫 5행:")
    print(saved_predictions.head(5).to_string(index=False))

    # 세 예측 방법을 같은 12월 평가 행과 비교합니다.
    actual = saved_predictions["실제 정답(strong_wind)"]
    prediction_methods = {
        "항상 0 예측": saved_predictions["항상 0 예측"],
        "현재 상태 유지 예측": saved_predictions["현재 상태 유지 예측"],
        "로지스틱 회귀 0.50 기준 예측": saved_predictions[
            "로지스틱 회귀 최종 예측"
        ],
    }

    # 요청한 평가 자료 행 수와 실제 강풍 건수를 확인합니다.
    if len(saved_predictions) != 744:
        raise ValueError(
            f"평가 행은 744개여야 하지만 {len(saved_predictions)}개입니다."
        )
    actual_strong_wind_count = int((actual == 1).sum())
    if actual_strong_wind_count != 39:
        raise ValueError(
            f"실제 강풍은 39건이어야 하지만 {actual_strong_wind_count}건입니다."
        )
    print("\n평가 데이터 확인:")
    print(f"  세 방법이 공통으로 사용한 평가 행 수: {len(saved_predictions)}")
    print(f"  실제 강풍 수: {actual_strong_wind_count}")

    # 각 방법의 TP, FN, FP, TN과 정확도, 정밀도, 재현율을 계산합니다.
    score_rows = []
    for method_name, predicted in prediction_methods.items():
        if len(predicted) != len(actual):
            raise ValueError(f"{method_name}의 예측 행 수가 평가 데이터와 다릅니다.")

        true_positive = int(((actual == 1) & (predicted == 1)).sum())
        false_negative = int(((actual == 1) & (predicted == 0)).sum())
        false_positive = int(((actual == 0) & (predicted == 1)).sum())
        true_negative = int(((actual == 0) & (predicted == 0)).sum())

        accuracy = (true_positive + true_negative) / len(actual)
        predicted_positive_count = true_positive + false_positive
        if predicted_positive_count == 0:
            precision = "해당 없음"
        else:
            precision = true_positive / predicted_positive_count
        recall = true_positive / (true_positive + false_negative)

        score_rows.append(
            {
                "예측 방법": method_name,
                "적중(TP)": true_positive,
                "놓침(FN)": false_negative,
                "오경보(FP)": false_positive,
                "정상 판정(TN)": true_negative,
                "정확도(Accuracy)": accuracy,
                "정밀도(Precision)": precision,
                "재현율(Recall)": recall,
            }
        )

    # 계산한 비교 결과를 CSV 파일로 저장하고 읽기 쉬운 표로 출력합니다.
    scores = pd.DataFrame(score_rows)
    scores.to_csv(SCORES_FILE, index=False)
    display_scores = scores.copy()
    display_scores["정확도(Accuracy)"] = display_scores["정확도(Accuracy)"].map(
        lambda value: f"{value:.4f}"
    )
    display_scores["정밀도(Precision)"] = display_scores[
        "정밀도(Precision)"
    ].map(
        lambda value: value if isinstance(value, str) else f"{value:.4f}"
    )
    display_scores["재현율(Recall)"] = display_scores["재현율(Recall)"].map(
        lambda value: f"{value:.4f}"
    )
    print(f"\n평가 결과를 {SCORES_FILE} 파일로 저장했습니다.")
    print(display_scores.to_string(index=False))


def add_lower_threshold_results():
    # 실습 3에서 저장한 예측과 확률을 읽어 옵니다.
    # 이 단계에서는 모델을 학습하거나 확률을 다시 계산하지 않습니다.
    predictions = pd.read_csv(OUTPUT_FILE)
    scores = pd.read_csv(SCORES_FILE)

    probability_column = "로지스틱 회귀 강풍 확률"
    actual_column = "실제 정답(strong_wind)"
    wind_column = "실제 풍속(target_wind_speed_ms)"
    old_prediction_column = "로지스틱 회귀 최종 예측"
    new_prediction_column = "로지스틱 회귀 0.20 기준 예측"
    old_method_name = "로지스틱 회귀 0.50 기준 예측"
    new_method_name = "로지스틱 회귀 0.20 기준 예측"

    # 12월 평가 데이터가 같은 744개 행인지와 실제 강풍 건수를 확인합니다.
    predictions[TARGET_TIME_COLUMN] = pd.to_datetime(predictions[TARGET_TIME_COLUMN])
    is_december = predictions[TARGET_TIME_COLUMN].between(
        EVALUATION_START, EVALUATION_END, inclusive="left"
    )
    if len(predictions) != 744 or not is_december.all():
        raise ValueError("저장된 예측 파일이 12월 평가 데이터 744행과 일치하지 않습니다.")
    if int(predictions[actual_column].sum()) != 39:
        raise ValueError("저장된 예측 파일의 실제 강풍 수가 39건이 아닙니다.")

    # 저장된 실제 풍속으로 기존 4.0 m/s 강풍 기준이 유지됐는지 확인합니다.
    expected_actual = (predictions[wind_column] >= 4.0).astype(int)
    if not expected_actual.equals(predictions[actual_column].astype(int)):
        raise ValueError("실제 정답이 target_wind_speed_ms의 4.0 m/s 기준과 다릅니다.")

    # 기존 로지스틱 회귀 확률만 사용해 0.20 기준 예측을 추가합니다.
    predictions[new_prediction_column] = (
        predictions[probability_column] >= 0.20
    ).astype(int)
    predictions.to_csv(OUTPUT_FILE, index=False)

    # 저장된 실제 정답과 각 예측값으로 점수를 계산합니다.
    actual = predictions[actual_column].astype(int)

    def calculate_scores(predicted):
        predicted = predicted.astype(int)
        true_positive = int(((actual == 1) & (predicted == 1)).sum())
        false_negative = int(((actual == 1) & (predicted == 0)).sum())
        false_positive = int(((actual == 0) & (predicted == 1)).sum())
        true_negative = int(((actual == 0) & (predicted == 0)).sum())
        predicted_positive_count = true_positive + false_positive
        precision = (
            "해당 없음"
            if predicted_positive_count == 0
            else true_positive / predicted_positive_count
        )
        return {
            "적중(TP)": true_positive,
            "놓침(FN)": false_negative,
            "오경보(FP)": false_positive,
            "정상 판정(TN)": true_negative,
            "정확도(Accuracy)": (true_positive + true_negative) / len(actual),
            "정밀도(Precision)": precision,
            "재현율(Recall)": true_positive / (true_positive + false_negative),
        }

    # 0.50 기준의 기존 점수를 그대로 가져오고, 0.20 점수를 새로 계산합니다.
    old_score = scores.loc[scores["예측 방법"] == old_method_name]
    if len(old_score) != 1:
        raise ValueError("기존 0.50 기준 점수를 정확히 하나 찾을 수 없습니다.")
    old_score = old_score.iloc[0]
    new_score = calculate_scores(predictions[new_prediction_column])

    # 모든 기준이 동일한 평가 행 수를 사용했는지 확인합니다.
    if len(predictions[old_prediction_column]) != len(
        predictions[new_prediction_column]
    ):
        raise ValueError("0.50과 0.20 기준의 평가 행 수가 서로 다릅니다.")
    print("\n평가 데이터 확인:")
    print(f"  0.50 기준 평가 행 수: {len(predictions)}")
    print(f"  0.20 기준 평가 행 수: {len(predictions)}")
    print(f"  실제 강풍 수(풍속 4.0 m/s 이상): {int(actual.sum())}")

    # 점수 파일에 0.20 기준 결과를 새 행으로 추가합니다.
    new_score_row = {"예측 방법": new_method_name, **new_score}
    scores = scores.loc[scores["예측 방법"] != new_method_name]
    scores = pd.concat([scores, pd.DataFrame([new_score_row])], ignore_index=True)
    scores.to_csv(SCORES_FILE, index=False)

    # 두 로지스틱 회귀 기준의 TP, FN, FP, 정밀도, 재현율을 나란히 출력합니다.
    comparison = pd.DataFrame(
        [
            {
                "확률 기준": "0.50",
                "적중(TP)": int(old_score["적중(TP)"]),
                "놓침(FN)": int(old_score["놓침(FN)"]),
                "오경보(FP)": int(old_score["오경보(FP)"]),
                "정밀도(Precision)": old_score["정밀도(Precision)"],
                "재현율(Recall)": float(old_score["재현율(Recall)"]),
            },
            {
                "확률 기준": "0.20",
                "적중(TP)": new_score["적중(TP)"],
                "놓침(FN)": new_score["놓침(FN)"],
                "오경보(FP)": new_score["오경보(FP)"],
                "정밀도(Precision)": new_score["정밀도(Precision)"],
                "재현율(Recall)": new_score["재현율(Recall)"],
            },
        ]
    )
    comparison["정밀도(Precision)"] = comparison["정밀도(Precision)"].map(
        lambda value: value if isinstance(value, str) else f"{float(value):.4f}"
    )
    comparison["재현율(Recall)"] = comparison["재현율(Recall)"].map(
        lambda value: f"{float(value):.4f}"
    )
    print(f"\n예측 결과에 '{new_prediction_column}' 열을 추가했습니다.")
    print(f"평가 결과에 '{new_method_name}' 행을 추가했습니다.")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    add_lower_threshold_results()
