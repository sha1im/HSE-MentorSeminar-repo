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


def clean_production(production: pd.DataFrame) -> pd.DataFrame:
    df = production.copy()

    df["date"] = pd.to_datetime(df["date"])

    numeric_columns = [
        "oil_ton",
        "gas_m3",
        "water_m3",
        "energy_kwh",
        "downtime_hours",
        "temperature",
        "pressure",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df[df["oil_ton"] >= 0]
    df = df[df["gas_m3"] >= 0]
    df = df[df["water_m3"] >= 0]
    df = df[df["energy_kwh"] >= 0]
    df = df[(df["downtime_hours"] >= 0) & (df["downtime_hours"] <= 24)]

    for column in ["temperature", "pressure"]:
        df[column] = df[column].fillna(
            df.groupby("well_id")[column].transform("mean")
        )
        df[column] = df[column].fillna(df[column].mean())

    return df


def build_mart_production_daily(production: pd.DataFrame) -> pd.DataFrame:
    mart = (
        production
        .groupby("date", as_index=False)
        .agg(
            total_oil_ton=("oil_ton", "sum"),
            total_gas_m3=("gas_m3", "sum"),
            total_water_m3=("water_m3", "sum"),
            total_energy_kwh=("energy_kwh", "sum"),
            total_downtime_hours=("downtime_hours", "sum"),
            avg_temperature=("temperature", "mean"),
            avg_pressure=("pressure", "mean"),
            wells_count=("well_id", "nunique"),
        )
    )

    return mart


def build_mart_well_kpi(production: pd.DataFrame, wells: pd.DataFrame) -> pd.DataFrame:
    mart = (
        production
        .groupby("well_id", as_index=False)
        .agg(
            avg_oil_ton=("oil_ton", "mean"),
            total_oil_ton=("oil_ton", "sum"),
            avg_gas_m3=("gas_m3", "mean"),
            avg_water_m3=("water_m3", "mean"),
            avg_energy_kwh=("energy_kwh", "mean"),
            total_downtime_hours=("downtime_hours", "sum"),
            avg_temperature=("temperature", "mean"),
            avg_pressure=("pressure", "mean"),
            days_count=("date", "nunique"),
        )
    )

    mart["downtime_percent"] = (
        mart["total_downtime_hours"] / (mart["days_count"] * 24) * 100
    ).round(2)

    mart = mart.merge(
        wells[["well_id", "name", "field_name", "region", "operator", "status"]],
        on="well_id",
        how="left",
    )

    mart = mart[
        [
            "well_id",
            "name",
            "field_name",
            "region",
            "operator",
            "status",
            "avg_oil_ton",
            "total_oil_ton",
            "downtime_percent",
            "avg_temperature",
            "avg_pressure",
            "avg_gas_m3",
            "avg_water_m3",
            "avg_energy_kwh",
            "days_count",
        ]
    ]

    return mart

def build_mart_well_ranking(mart_well_kpi: pd.DataFrame) -> pd.DataFrame:
    mart = mart_well_kpi.copy()

    mart = mart.sort_values("total_oil_ton", ascending=False).reset_index(drop=True)

    mart["rank_by_total_oil"] = mart["total_oil_ton"].rank(
        ascending=False,
        method="dense",
    ).astype(int)

    mart["performance_group"] = "normal"

    best_rank = mart["rank_by_total_oil"].min()
    worst_rank = mart["rank_by_total_oil"].max()

    mart.loc[mart["rank_by_total_oil"] == best_rank, "performance_group"] = "best"
    mart.loc[mart["rank_by_total_oil"] == worst_rank, "performance_group"] = "worst"

    return mart[
        [
            "well_id",
            "name",
            "field_name",
            "region",
            "operator",
            "status",
            "avg_oil_ton",
            "total_oil_ton",
            "downtime_percent",
            "avg_pressure",
            "avg_temperature",
            "rank_by_total_oil",
            "performance_group",
        ]
    ]

def build_mart_pressure_debit(production: pd.DataFrame) -> pd.DataFrame:
    mart = production.copy()

    mart["pressure_bin"] = (mart["pressure"] / 5).round() * 5
    mart["temperature_bin"] = (mart["temperature"] / 5).round() * 5
    mart["oil_ton_bin"] = (mart["oil_ton"] / 10).round() * 10

    mart = (
        mart
        .groupby(["pressure_bin", "temperature_bin", "oil_ton_bin"], as_index=False)
        .agg(
            records_count=("well_id", "count"),
            avg_oil_ton=("oil_ton", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_temperature=("temperature", "mean"),
        )
    )

    return mart


def main():
    engine = get_postgres_engine()

    wells = pd.read_sql("SELECT * FROM wells", engine)
    production = pd.read_sql("SELECT * FROM production", engine)

    production_clean = clean_production(production)

    mart_production_daily = build_mart_production_daily(production_clean)
    mart_well_kpi = build_mart_well_kpi(production_clean, wells)
    mart_well_ranking = build_mart_well_ranking(mart_well_kpi)
    mart_pressure_debit = build_mart_pressure_debit(production_clean)

    production_clean.to_sql(
        "production_clean",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_production_daily.to_sql(
        "mart_production_daily",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_well_kpi.to_sql(
        "mart_well_kpi",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_well_ranking.to_sql(
        "mart_well_ranking",
        engine,
        if_exists="replace",
        index=False,
    )

    mart_pressure_debit.to_sql(
        "mart_pressure_debit",
        engine,
        if_exists="replace",
        index=False,
    )

    print("production_clean:", len(production_clean), "rows")
    print("mart_production_daily:", len(mart_production_daily), "rows")
    print("mart_well_kpi:", len(mart_well_kpi), "rows")
    print("mart_well_ranking:", len(mart_well_ranking), "rows")
    print("mart_pressure_debit:", len(mart_pressure_debit), "rows")
    print("Production marts created successfully")


if __name__ == "__main__":
    main()