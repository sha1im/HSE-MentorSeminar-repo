# Домашнее задание 1 — Yandex Cloud / PySpark

## Описание

В рамках задания была собрана витрина mart_city_top_products на основе трех исходных таблиц:

- users
- orders
- products

Работа выполнялась в Yandex Data Processing через Apache Zeppelin с использованием %spark.pyspark.

## Что было сделано

1. Созданы исходные DataFrame прямо в Zeppelin.
2. Посчитана производная метрика revenue = qty * price.
3. Выполнено объединение orders с users и products.
4. Посчитаны метрики по (city, product_id, product_name):
   - orders_cnt
   - qty_sum
   - revenue_sum
5. С помощью оконной функции Window выбран Top-2 товаров по revenue_sum для каждого города.
6. Результат сохранен в формате Parquet:
   - в HDFS: hdfs:///tmp/sandbox_zeppelin/mart_city_top_products/
   - в Yandex Object Storage: s3a://hse-seminar-backet/mart_city_top_products/
7. Данные были повторно прочитаны из HDFS и Object Storage для проверки.

## Используемые инструменты

- Yandex Cloud
- Yandex Data Processing
- Apache Zeppelin
- Apache Spark / PySpark
- HDFS
- Yandex Object Storage

## Результат

Итоговая витрина содержит Топ-2 товара по выручке для каждого города. Её содержание можно увидеть на скриншотах в папке 'screenshots'.