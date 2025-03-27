# NCSES Tables in ML-Ready Format

This directory contains NCSES statistical tables converted to machine-readable formats with ML Croissant metadata for machine learning applications.

## Directory Structure

- `tables/`: Contains one directory per table, each with:
  - `data.csv`: Table data in CSV format
  - `croissant_metadata.json`: ML Croissant metadata
  - `README.md`: Table documentation

- `catalog/`: Contains catalog files
  - `catalog.json`: Complete catalog in JSON format
  - `catalog.csv`: Simplified catalog in CSV format

## Table Types

- **ST**: Simple Tabular
- **RH**: Row Hierarchical
- **CH**: Column Hierarchical
- **MH**: Matrix Hierarchical
- **TS**: Time Series
- **SP**: Specialized

## Special Values

- *****: value between 0.00% and 0.05%
- **D**: suppressed to avoid disclosure of confidential information
- **i**: imputed value
- **r**: revised value

## Processing Summary

- Total tables processed: 6262
- Tables by type:
  - CH (Column Hierarchical): 97
  - MH (Matrix Hierarchical): 2300
  - RH (Row Hierarchical): 2728
  - ST (Simple Tabular): 348
  - TS (Time Series): 789
