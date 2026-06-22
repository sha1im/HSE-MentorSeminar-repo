import os

import pandas as pd
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


def clean_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    df = deliveries.copy()

    df["date"] = pd.to_datetime(df["date"])

    numeric_columns = [
        "volume_ton",
        "cost_usd",
        "delay_hours",
        "distance_km",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in numeric_columns:
        df[column] = df[column].fillna(df[column].median())

    df["weather_conditions"] = df["weather_conditions"].fillna("Unknown")
    df["product_type"] = df["product_type"].fillna("Unknown")
    df["source"] = df["source"].fillna("Unknown")
    df["destination"] = df["destination"].fillna("Unknown")

    df = df[df["volume_ton"] >= 0]
    df = df[df["cost_usd"] >= 0]
    df = df[df["delay_hours"] >= 0]
    df = df[df["distance_km"] > 0]

    df["route"] = df["source"] + " -> " + df["destination"]
    df["cost_per_km"] = df["cost_usd"] / df["distance_km"]
    df["is_delayed"] = df["delay_hours"] > 0

    return df


def build_delivery_clean(
    deliveries: pd.DataFrame,
    drivers: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> pd.DataFrame:
    df = deliveries.copy()

    df = df.merge(
        drivers,
        on="driver_id",
        how="left",
    )

    df = df.rename(
        columns={
            "name": "driver_name",
            "region": "driver_region",
        }
    )

    df = df.merge(
        vehicles,
        on="vehicle_id",
        how="left",
    )

    return df


def build_mart_delay_weather(delivery_clean: pd.DataFrame) -> pd.DataFrame:
    mart = (
        delivery_clean
        .groupby("weather_conditions", as_index=False)
        .agg(
            deliveries_count=("delivery_id", "count"),
            avg_delay_hours=("delay_hours", "mean"),
            max_delay_hours=("delay_hours", "max"),
            delayed_count=("is_delayed", "sum"),
            avg_distance_km=("distance_km", "mean"),
            avg_cost_per_km=("cost_per_km", "mean"),
        )
    )

    mart["delay_rate_percent"] = (
        mart["delayed_count"] / mart["deliveries_count"] * 100
    ).round(2)

    return mart.sort_values("avg_delay_hours", ascending=False)


def build_mart_cost_distance(delivery_clean: pd.DataFrame) -> pd.DataFrame:
    mart = delivery_clean[
        [
            "delivery_id",
            "date",
            "route",
            "source",
            "destination",
            "product_type",
            "volume_ton",
            "cost_usd",
            "distance_km",
            "cost_per_km",
            "delay_hours",
            "weather_conditions",
            "driver_id",
            "driver_name",
            "vehicle_id",
            "plate_number",
        ]
    ].copy()

    return mart


def build_mart_driver_kpi(delivery_clean: pd.DataFrame) -> pd.DataFrame:
    mart = (
        delivery_clean
        .groupby(
            [
                "driver_id",
                "driver_name",
                "experience_years",
                "driver_region",
            ],
            as_index=False,
        )
        .agg(
            deliveries_count=("delivery_id", "count"),
            total_volume_ton=("volume_ton", "sum"),
            total_cost_usd=("cost_usd", "sum"),
            avg_cost_per_km=("cost_per_km", "mean"),
            avg_delay_hours=("delay_hours", "mean"),
            max_delay_hours=("delay_hours", "max"),
            delayed_count=("is_delayed", "sum"),
            avg_distance_km=("distance_km", "mean"),
        )
    )

    mart["delay_rate_percent"] = (
        mart["delayed_count"] / mart["deliveries_count"] * 100
    ).round(2)

    return mart.sort_values(["avg_delay_hours", "delay_rate_percent"])


def build_mart_route_optimization(delivery_clean: pd.DataFrame) -> pd.DataFrame:
    mart = (
        delivery_clean
        .groupby(["route", "source", "destination", "product_type"], as_index=False)
        .agg(
            deliveries_count=("delivery_id", "count"),
            total_volume_ton=("volume_ton", "sum"),
            avg_distance_km=("distance_km", "mean"),
            avg_cost_usd=("cost_usd", "mean"),
            avg_cost_per_km=("cost_per_km", "mean"),
            avg_delay_hours=("delay_hours", "mean"),
            delayed_count=("is_delayed", "sum"),
        )
    )

    mart["delay_rate_percent"] = (
        mart["delayed_count"] / mart["deliveries_count"] * 100
    ).round(2)

    mart["route_score"] = (
        mart["avg_cost_per_km"] + mart["avg_delay_hours"] * 10
    ).round(2)

    mart["route_rank"] = mart["route_score"].rank(
        ascending=True,
        method="dense",
    ).astype(int)

    def get_recommendation(row):
        if row["avg_delay_hours"] == 0 and row["avg_cost_per_km"] <= mart["avg_cost_per_km"].median():
            return "preferred"
        if row["avg_delay_hours"] >= mart["avg_delay_hours"].quantile(0.75):
            return "review"
        return "normal"

    mart["recommendation"] = mart.apply(get_recommendation, axis=1)

    return mart.sort_values("route_score")


def main():
    engine = get_postgres_engine()

    deliveries = pd.read_sql("SELECT * FROM deliveries", engine)
    drivers = pd.read_sql("SELECT * FROM drivers", engine)
    vehicles = pd.read_sql("SELECT * FROM vehicles", engine)

    deliveries_clean = clean_deliveries(deliveries)
    delivery_clean = build_delivery_clean(deliveries_clean, drivers, vehicles)

    mart_delay_weather = build_mart_delay_weather(delivery_clean)
    mart_cost_distance = build_mart_cost_distance(delivery_clean)
    mart_driver_kpi = build_mart_driver_kpi(delivery_clean)
    mart_route_optimization = build_mart_route_optimization(delivery_clean)

    delivery_clean.to_sql(
        "delivery_clean",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_delay_weather.to_sql(
        "mart_delay_weather",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_cost_distance.to_sql(
        "mart_cost_distance",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_driver_kpi.to_sql(
        "mart_driver_kpi",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_route_optimization.to_sql(
        "mart_route_optimization",
        engine,
        if_exists="replace",
        index=False,
    )

    print("delivery_clean:", len(delivery_clean), "rows")
    print("mart_delay_weather:", len(mart_delay_weather), "rows")
    print("mart_cost_distance:", len(mart_cost_distance), "rows")
    print("mart_driver_kpi:", len(mart_driver_kpi), "rows")
    print("mart_route_optimization:", len(mart_route_optimization), "rows")
    print("Logistics analysis created successfully")


if __name__ == "__main__":
    main()