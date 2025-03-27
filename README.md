# NCSES Statistics Explorer

A comprehensive tool for transforming National Center for Science and Engineering Statistics (NCSES) data tables into machine-readable formats and visualizing the results through an interactive dashboard.

## Overview

The NCSES Statistics Explorer consists of three main components:

1. **NCSES Transformer**: Converts raw NCSES data tables from JSON Lines format into structured CSV files with ML Croissant metadata.
2. **NCSES Metadata Extractor**: Analyzes the transformed tables and extracts summary metadata.
3. **Interactive Dashboard**: Visualizes the metadata and provides examples of different table structures.

## Table Types

The system classifies NCSES tables into five structural types:

- **RH - Row Hierarchical**: Tables with hierarchies in row headers (e.g., organizational structures)
- **MH - Matrix Hierarchical**: Tables with hierarchies in both rows and columns
- **TS - Time Series**: Data tracked over multiple time periods
- **CH - Column Hierarchical**: Tables with hierarchies in column headers
- **ST - Simple Tabular**: Flat data without hierarchies

For detailed examples of each table type and their transformed formats, see [Table Type Examples](docs/table_type_examples.md).

## Project Structure

```
ncses_stats_explorer/
├── bin/                    # Executable scripts
│   ├── run_transformer.sh  # Script to run the transformer
│   └── run_extractor.sh    # Script to run the metadata extractor
├── lib/                    # Core library code
│   ├── ncses_transformer.py      # Transforms tables to CSV and ML Croissant
│   └── ncses_metadata_extractor.py  # Extracts metadata from transformed tables
├── dashboard/             # Interactive dashboard
│   ├── index.html         # Dashboard HTML
│   ├── dashboard.js       # Dashboard JavaScript
│   ├── table_type_examples.js  # Table type examples
│   └── fix_special_values_chart.js  # Fix for special values chart
├── data/                   # Input data
│   └── table_results.jsonl  # Raw NCSES tables in JSON Lines format
├── output/                 # Output directory (created by transformer)
│   ├── tables/             # Transformed tables (one directory per table)
│   └── catalog/            # Catalog files (JSON and CSV)
├── README.md               # This file
└── .gitignore              # Git ignore file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ncses_stats_explorer.git
   cd ncses_stats_explorer
   ```

2. Set up a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Transforming NCSES Tables

To transform NCSES tables from JSON Lines format to CSV and ML Croissant metadata:

```bash
python -m lib.ncses_transformer data/table_results.jsonl --output-dir output
```

Or use the provided shell script:

```bash
bin/run_transformer.sh
```

### Extracting Metadata

To extract metadata from the transformed tables:

```bash
python -m lib.ncses_metadata_extractor --input-dir output --output-dir dashboard/metadata
```

Or use the provided shell script:

```bash
bin/run_extractor.sh
```

### Running the Dashboard

The dashboard is a static HTML/JS application and can be viewed by opening the `dashboard/index.html` file in a web browser.

For a better experience, you can serve it using a local web server:

```bash
cd dashboard
python -m http.server 8000
```

Then open http://localhost:8000 in your web browser.

## Key Features

- **Modal ID Support**: Tables are organized by unique modal IDs while preserving original table numbers.
- **Hierarchical Data Normalization**: Preserves nested hierarchies in row and column headers.
- **Table Type Classification**: Automatically detects and classifies table structures.
- **Rich Metadata Generation**: Creates ML Croissant compliant metadata for each table.
- **Interactive Dashboard**: Visualizes metadata and provides examples of different table types.
- **Table Type Examples**: Interactive examples showing the structure of each table type.

## Implementation Details

### Transformer

The NCSES Transformer performs the following operations:

1. Parses and analyzes the structure of each table
2. Classifies tables based on their structural characteristics
3. Transforms tables into normalized CSV format
4. Generates ML Croissant metadata for each table
5. Creates a catalog of all transformed tables

### Metadata Extractor

The Metadata Extractor:

1. Reads the transformed tables and metadata
2. Analyzes the distribution of table types, hierarchy depths, etc.
3. Extracts examples of each table type
4. Creates summary statistics for the dashboard
5. Generates a searchable table index

### Dashboard

The dashboard provides:

1. Summary statistics on table types, hierarchy depths, etc.
2. Interactive examples of each table type
3. A searchable table browser
4. Visualizations of metadata distributions

## License

This project is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/deed.en).

You are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

## Acknowledgments

- National Center for Science and Engineering Statistics (NCSES) for the data
- ML Commons for the Croissant metadata format specification
