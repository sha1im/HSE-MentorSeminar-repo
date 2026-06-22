import os

import pandas as pd
import s3fs
from sqlalchemy import create_engine


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "datalake")


TABLES = {
    "wells": None,
    "production": "date",
    "well_telemetry": "timestamp",
    "well_targets": "date",
    "pumps": None,
    "pump_sensors": "timestamp",
    "pump_failures": "failure_date",
    "drivers": None,
    "vehicles": None,
    "deliveries": "date",
}


def get_postgres_engine():
    db_url = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    return create_engine(db_url)


def get_s3_filesystem():
    return s3fs.S3FileSystem(
        key=MINIO_ROOT_USER,
        secret=MINIO_ROOT_PASSWORD,
        client_kwargs={
            "endpoint_url": MINIO_ENDPOINT,
        },
    )


def add_partition_column(df, date_column):
    df[date_column] = pd.to_datetime(df[date_column])
    df["partition_date"] = df[date_column].dt.date.astype(str)
    return df


def save_dataframe_to_minio(df, table_name, date_column, fs):
    base_path = f"{MINIO_BUCKET}/raw/{table_name}"

    if date_column is None:
        output_path = f"s3://{base_path}/data.parquet"
        df.to_parquet(output_path, engine="pyarrow", index=False, filesystem=fs)
        return

    df = add_partition_column(df, date_column)

    for partition_date, part_df in df.groupby("partition_date"):
        output_path = (
            f"s3://{base_path}/partition_date={partition_date}/data.parquet"
        )
        part_df = part_df.drop(columns=["partition_date"])
        part_df.to_parquet(output_path, engine="pyarrow", index=False, filesystem=fs)


def main():
    engine = get_postgres_engine()
    fs = get_s3_filesystem()

    for table_name, date_column in TABLES.items():
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        save_dataframe_to_minio(df, table_name, date_column, fs)

        if date_column is None:
            partition_info = "without partitions"
        else:
            partition_info = f"partitioned by {date_column}"

        print(f"{table_name}: {len(df)} rows, {partition_info}")

    print("ETL finished successfully")


if __name__ == "__main__":
    main()