import os

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")


def get_postgres_engine():
    db_url = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    return create_engine(db_url)


def build_telemetry_daily(well_telemetry: pd.DataFrame) -> pd.DataFrame:
    telemetry = well_telemetry.copy()

    telemetry["timestamp"] = pd.to_datetime(telemetry["timestamp"])
    telemetry["date"] = telemetry["timestamp"].dt.date
    telemetry["date"] = pd.to_datetime(telemetry["date"])

    numeric_columns = [
        "pump_speed_rpm",
        "pump_current",
        "pressure_in",
        "pressure_out",
        "temperature",
        "vibration",
        "oil_flow_rate",
    ]

    for column in numeric_columns:
        telemetry[column] = pd.to_numeric(telemetry[column], errors="coerce")

    telemetry_daily = (
        telemetry
        .groupby(["well_id", "date"], as_index=False)
        .agg(
            avg_pump_speed_rpm=("pump_speed_rpm", "mean"),
            avg_pump_current=("pump_current", "mean"),
            avg_pressure_in=("pressure_in", "mean"),
            avg_pressure_out=("pressure_out", "mean"),
            avg_telemetry_temperature=("temperature", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_oil_flow_rate=("oil_flow_rate", "mean"),
            telemetry_records=("record_id", "count"),
        )
    )

    return telemetry_daily


def build_ml_dataset(
    well_targets: pd.DataFrame,
    production_clean: pd.DataFrame,
    telemetry_daily: pd.DataFrame,
) -> pd.DataFrame:
    targets = well_targets.copy()
    production = production_clean.copy()

    targets["date"] = pd.to_datetime(targets["date"])
    production["date"] = pd.to_datetime(production["date"])

    targets["daily_oil_ton"] = pd.to_numeric(
        targets["daily_oil_ton"],
        errors="coerce",
    )

    numeric_columns = [
        "pressure",
        "temperature",
        "energy_kwh",
        "downtime_hours",
    ]

    for column in numeric_columns:
        production[column] = pd.to_numeric(production[column], errors="coerce")

    dataset = targets.merge(
        production[
            [
                "well_id",
                "date",
                "pressure",
                "temperature",
                "energy_kwh",
                "downtime_hours",
            ]
        ],
        on=["well_id", "date"],
        how="left",
    )

    dataset = dataset.merge(
        telemetry_daily,
        on=["well_id", "date"],
        how="left",
    )

    dataset["feature_pressure"] = dataset["pressure"]
    dataset["feature_temperature"] = dataset["temperature"]
    dataset["feature_energy_kwh"] = dataset["energy_kwh"]
    dataset["feature_pump_work_hours"] = 24 - dataset["downtime_hours"]

    feature_columns = [
        "feature_pressure",
        "feature_temperature",
        "feature_energy_kwh",
        "feature_pump_work_hours",
    ]

    for column in feature_columns:
        dataset[column] = dataset[column].fillna(dataset[column].mean())

    dataset = dataset.dropna(subset=["daily_oil_ton"])

    return dataset


def train_model(dataset: pd.DataFrame):
    feature_columns = [
        "feature_pressure",
        "feature_temperature",
        "feature_energy_kwh",
        "feature_pump_work_hours",
    ]

    X = dataset[feature_columns]
    y = dataset["daily_oil_ton"]

    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X,
        y,
        dataset.index,
        test_size=0.25,
        random_state=42,
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5

    predictions = dataset.loc[
        test_idx,
        [
            "well_id",
            "date",
            "daily_oil_ton",
            "feature_pressure",
            "feature_temperature",
            "feature_energy_kwh",
            "feature_pump_work_hours",
        ],
    ].copy()

    predictions["predicted_daily_oil_ton"] = y_pred
    predictions["error"] = (
        predictions["daily_oil_ton"] - predictions["predicted_daily_oil_ton"]
    )
    predictions["absolute_error"] = predictions["error"].abs()

    predictions = predictions.sort_values(["date", "well_id"])

    metrics = pd.DataFrame(
        [
            {
                "model_name": "RandomForestRegressor",
                "mae": mae,
                "rmse": rmse,
                "train_rows": len(X_train),
                "test_rows": len(X_test),
            }
        ]
    )

    return predictions, metrics


def main():
    engine = get_postgres_engine()

    well_targets = pd.read_sql("SELECT * FROM well_targets", engine)
    production_clean = pd.read_sql("SELECT * FROM production_clean", engine)
    well_telemetry = pd.read_sql("SELECT * FROM well_telemetry", engine)

    telemetry_daily = build_telemetry_daily(well_telemetry)
    ml_dataset = build_ml_dataset(
        well_targets,
        production_clean,
        telemetry_daily,
    )

    predictions, metrics = train_model(ml_dataset)

    telemetry_daily.to_sql(
        "telemetry_daily",
        engine,
        if_exists="replace",
        index=False,
    )

    ml_dataset.to_sql(
        "ml_debit_dataset",
        engine,
        if_exists="replace",
        index=False,
    )

    predictions.to_sql(
        "mart_debit_predictions",
        engine,
        if_exists="replace",
        index=False,
    )

    metrics.to_sql(
        "mart_debit_model_metrics",
        engine,
        if_exists="replace",
        index=False,
    )

    print("telemetry_daily:", len(telemetry_daily), "rows")
    print("ml_debit_dataset:", len(ml_dataset), "rows")
    print("mart_debit_predictions:", len(predictions), "rows")
    print("mart_debit_model_metrics:", len(metrics), "rows")
    print("MAE:", round(metrics.loc[0, "mae"], 4))
    print("RMSE:", round(metrics.loc[0, "rmse"], 4))
    print("Debit forecast model created successfully")


if __name__ == "__main__":
    main()