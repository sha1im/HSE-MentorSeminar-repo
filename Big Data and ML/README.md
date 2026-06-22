# Big Data and ML Homework

Учебный проект: data pipeline для нефтяной отрасли.

Реализовано:

* PostgreSQL с исходными данными;
* MinIO как S3/data lake;
* JupyterHub для Python-обработки;
* Superset для BI-дашбордов;
* ETL PostgreSQL → MinIO;
* очистка данных и витрины;
* ML-прогноз дебита;
* анализ отказов оборудования;
* анализ логистики.

## Структура проекта

```text
.
├── notebooks/
│   └── 00_connection_check.ipynb          # проверка подключений PostgreSQL и MinIO
│
├── screenshots/
│   └── superset/                          # скриншоты готовых Superset dashboards
│       ├── production-analytics.jpg
│       ├── debit-forecast-ml.jpg
│       ├── equipment-failure-analysis.jpg
│       └── logistics-analytics.jpg
│
├── scripts/
│   ├── etl_postgres_to_minio.py           # выгрузка таблиц PostgreSQL в MinIO parquet
│   ├── build_production_marts.py          # очистка production и витрины добычи
│   ├── build_debit_forecast.py            # ML-прогноз суточного дебита
│   ├── build_failure_analysis.py          # аномалии и риск отказа насосов
│   └── build_logistics_analysis.py        # витрины логистики и маршрутов
│
├── sql/
│   └── init/                              # SQL-инициализация PostgreSQL
│       ├── 01_task1_ddl.sql
│       ├── 02_task1_data.sql
│       ├── 03_task2_ddl.sql
│       ├── 04_task2_data.sql
│       ├── 05_task3_ddl.sql
│       ├── 06_task3_data.sql
│       ├── 07_task4_ddl.sql
│       └── 08_task4_data.sql
│
├── superset/
│   └── Dockerfile                         # Superset image с PostgreSQL-драйвером
│
├── .env.example                           # пример переменных окружения
├── .gitignore
└── docker-compose.yml                     # инфраструктура проекта
```

## Запуск

Создать `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Запустить сервисы:

```bash
docker compose up -d --build
```

Проверить контейнеры:

```bash
docker compose ps
```

Сервисы:

```text
PostgreSQL  localhost:5432
MinIO       http://localhost:9001
JupyterHub  http://localhost:8000
Superset    http://localhost:8088
```

## Выполнение pipeline

Скрипты запускаются внутри контейнера `jupyterhub`:

```bash
docker exec -it jupyterhub python /home/student/scripts/etl_postgres_to_minio.py
docker exec -it jupyterhub python /home/student/scripts/build_production_marts.py
docker exec -it jupyterhub python /home/student/scripts/build_debit_forecast.py
docker exec -it jupyterhub python /home/student/scripts/build_failure_analysis.py
docker exec -it jupyterhub python /home/student/scripts/build_logistics_analysis.py
```

## Результаты

### 1. Добыча

Созданы витрины:

```text
production_clean
mart_production_daily
mart_well_kpi
mart_pressure_debit
mart_well_ranking
```

Superset dashboard:

```text
Production Analytics
```

Графики:

* добыча по времени;
* топ скважин;
* давление vs дебит.

### 2. ML-прогноз дебита

Созданы таблицы:

```text
telemetry_daily
ml_debit_dataset
mart_debit_predictions
mart_debit_model_metrics
```

Модель:

```text
RandomForestRegressor
```

Метрики:

```text
MAE  = 0.2624
RMSE = 0.3558
```

Superset dashboard:

```text
Debit Forecast ML
```

### 3. Отказы оборудования

Созданы таблицы:

```text
pump_sensor_clean
mart_pump_anomalies
mart_vibration_before_failure
mart_pump_risk_score
mart_failure_model_metrics
```

Модель:

```text
RandomForestClassifier
```

Superset dashboard:

```text
Equipment Failure Analysis
```

### 4. Логистика

Созданы таблицы:

```text
delivery_clean
mart_delay_weather
mart_cost_distance
mart_driver_kpi
mart_route_optimization
```

Superset dashboard:

```text
Logistics Analytics
```

## Примечания

Superset dashboards созданы вручную через UI. Скриншоты сохранены в `screenshots/superset/`.
