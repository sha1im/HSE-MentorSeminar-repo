import os

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")


SENSOR_COLUMNS = [
    "temperature",
    "vibration",
    "current",
    "rpm",
    "pressure",
]


def get_postgres_engine():
    db_url = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    return create_engine(db_url)


def clean_pump_sensors(pump_sensors: pd.DataFrame) -> pd.DataFrame:
    df = pump_sensors.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    for column in SENSOR_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].fillna(df[column].mean())

    df = df[df["temperature"] >= 0]
    df = df[df["vibration"] >= 0]
    df = df[df["current"] >= 0]
    df = df[df["rpm"] >= 0]
    df = df[df["pressure"] >= 0]

    return df


def add_z_score_anomalies(sensor_data: pd.DataFrame) -> pd.DataFrame:
    df = sensor_data.copy()

    z_columns = []

    for column in SENSOR_COLUMNS:
        mean_value = df[column].mean()
        std_value = df[column].std(ddof=0)

        z_column = f"{column}_z_score"
        z_columns.append(z_column)

        if std_value == 0:
            df[z_column] = 0
        else:
            df[z_column] = (df[column] - mean_value) / std_value

    df["max_abs_z_score"] = df[z_columns].abs().max(axis=1)

    df["is_anomaly"] = df["max_abs_z_score"] >= 2.0

    return df


def add_failure_labels(
    sensor_data: pd.DataFrame,
    pump_failures: pd.DataFrame,
) -> pd.DataFrame:
    sensors = sensor_data.copy()
    failures = pump_failures.copy()

    failures["failure_date"] = pd.to_datetime(failures["failure_date"])

    sensors["is_pre_failure"] = 0
    sensors["failure_date"] = pd.NaT
    sensors["failure_type"] = None
    sensors["hours_to_failure"] = None

    for _, failure in failures.iterrows():
        pump_id = failure["pump_id"]
        failure_date = failure["failure_date"]

        mask_same_pump = sensors["pump_id"] == pump_id
        mask_before_failure = sensors["timestamp"] <= failure_date
        mask_24h_before_failure = sensors["timestamp"] >= (
            failure_date - pd.Timedelta(hours=24)
        )

        mask = mask_same_pump & mask_before_failure & mask_24h_before_failure

        sensors.loc[mask, "is_pre_failure"] = 1
        sensors.loc[mask, "failure_date"] = failure_date
        sensors.loc[mask, "failure_type"] = failure["failure_type"]
        sensors.loc[mask, "hours_to_failure"] = (
            (failure_date - sensors.loc[mask, "timestamp"])
            .dt.total_seconds()
            / 3600
        )

    return sensors


def train_failure_model(sensor_data: pd.DataFrame):
    df = sensor_data.copy()

    X = df[SENSOR_COLUMNS]
    y = df["is_pre_failure"]

    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X,
        y,
        df.index,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)

    if y_test.nunique() > 1:
        roc_auc = roc_auc_score(y_test, y_proba)
    else:
        roc_auc = None

    metrics = pd.DataFrame(
        [
            {
                "model_name": "RandomForestClassifier",
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "roc_auc": roc_auc,
                "train_rows": len(X_train),
                "test_rows": len(X_test),
                "positive_rows": int(y.sum()),
                "negative_rows": int((y == 0).sum()),
            }
        ]
    )

    df["risk_score"] = model.predict_proba(X)[:, 1]

    return df, metrics


def build_mart_pump_anomalies(sensor_data: pd.DataFrame) -> pd.DataFrame:
    mart = sensor_data.copy()

    mart = mart[
        [
            "record_id",
            "pump_id",
            "timestamp",
            "temperature",
            "vibration",
            "current",
            "rpm",
            "pressure",
            "temperature_z_score",
            "vibration_z_score",
            "current_z_score",
            "rpm_z_score",
            "pressure_z_score",
            "max_abs_z_score",
            "is_anomaly",
            "is_pre_failure",
            "risk_score",
        ]
    ]

    return mart


def build_mart_vibration_before_failure(sensor_data: pd.DataFrame) -> pd.DataFrame:
    mart = sensor_data.copy()

    mart = mart[mart["failure_date"].notna()]

    mart = mart[
        [
            "pump_id",
            "timestamp",
            "failure_date",
            "failure_type",
            "hours_to_failure",
            "temperature",
            "vibration",
            "current",
            "rpm",
            "pressure",
            "risk_score",
        ]
    ]

    return mart.sort_values(["pump_id", "timestamp"])


def build_mart_pump_risk_score(
    sensor_data: pd.DataFrame,
    pumps: pd.DataFrame,
    pump_failures: pd.DataFrame,
) -> pd.DataFrame:
    mart = (
        sensor_data
        .groupby("pump_id", as_index=False)
        .agg(
            sensor_records=("record_id", "count"),
            anomaly_count=("is_anomaly", "sum"),
            avg_risk_score=("risk_score", "mean"),
            max_risk_score=("risk_score", "max"),
            latest_timestamp=("timestamp", "max"),
            avg_temperature=("temperature", "mean"),
            max_temperature=("temperature", "max"),
            avg_vibration=("vibration", "mean"),
            max_vibration=("vibration", "max"),
            avg_current=("current", "mean"),
            max_current=("current", "max"),
        )
    )

    latest_risk = sensor_data.sort_values("timestamp").groupby("pump_id").tail(1)
    latest_risk = latest_risk[["pump_id", "risk_score"]].rename(
        columns={"risk_score": "latest_risk_score"}
    )

    mart = mart.merge(latest_risk, on="pump_id", how="left")

    failures_count = (
        pump_failures
        .groupby("pump_id", as_index=False)
        .agg(failure_count=("failure_id", "count"))
    )

    mart = mart.merge(failures_count, on="pump_id", how="left")
    mart["failure_count"] = mart["failure_count"].fillna(0).astype(int)

    mart = mart.merge(
        pumps,
        on="pump_id",
        how="left",
    )

    def get_risk_level(score):
        if score >= 0.7:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"

    mart["risk_level"] = mart["max_risk_score"].apply(get_risk_level)

    mart = mart[
        [
            "pump_id",
            "well_id",
            "type",
            "manufacturer",
            "model",
            "sensor_records",
            "anomaly_count",
            "failure_count",
            "avg_risk_score",
            "max_risk_score",
            "latest_risk_score",
            "risk_level",
            "avg_temperature",
            "max_temperature",
            "avg_vibration",
            "max_vibration",
            "avg_current",
            "max_current",
            "latest_timestamp",
        ]
    ]

    return mart


def main():
    engine = get_postgres_engine()

    pumps = pd.read_sql("SELECT * FROM pumps", engine)
    pump_sensors = pd.read_sql("SELECT * FROM pump_sensors", engine)
    pump_failures = pd.read_sql("SELECT * FROM pump_failures", engine)

    pump_sensor_clean = clean_pump_sensors(pump_sensors)
    pump_sensor_clean = add_z_score_anomalies(pump_sensor_clean)
    pump_sensor_clean = add_failure_labels(pump_sensor_clean, pump_failures)

    pump_sensor_scored, model_metrics = train_failure_model(pump_sensor_clean)

    mart_pump_anomalies = build_mart_pump_anomalies(pump_sensor_scored)
    mart_vibration_before_failure = build_mart_vibration_before_failure(
        pump_sensor_scored
    )
    mart_pump_risk_score = build_mart_pump_risk_score(
        pump_sensor_scored,
        pumps,
        pump_failures,
    )

    pump_sensor_scored.to_sql(
        "pump_sensor_clean",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_pump_anomalies.to_sql(
        "mart_pump_anomalies",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_vibration_before_failure.to_sql(
        "mart_vibration_before_failure",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_pump_risk_score.to_sql(
        "mart_pump_risk_score",
        engine,
        if_exists="replace",
        index=False,
    )

    model_metrics.to_sql(
        "mart_failure_model_metrics",
        engine,
        if_exists="replace",
        index=False,
    )

    print("pump_sensor_clean:", len(pump_sensor_scored), "rows")
    print("mart_pump_anomalies:", len(mart_pump_anomalies), "rows")
    print(
        "mart_vibration_before_failure:",
        len(mart_vibration_before_failure),
        "rows",
    )
    print("mart_pump_risk_score:", len(mart_pump_risk_score), "rows")
    print("mart_failure_model_metrics:", len(model_metrics), "rows")

    print("Anomalies found:", int(mart_pump_anomalies["is_anomaly"].sum()))
    print("Pre-failure rows:", int(pump_sensor_scored["is_pre_failure"].sum()))

    print("Failure analysis created successfully")


if __name__ == "__main__":
    main()