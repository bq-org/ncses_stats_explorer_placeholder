"""
NCSES Table Transformer

This script transforms NCSES tables from JSON Lines format into:
1. Machine-readable CSV files
2. ML Croissant metadata files

The transformation implements the strategy outlined in the
"Comprehensive Strategy for Transforming NCSES Datasets into ML-Ready Formats" document.
"""

"""
Generic Program Usage:
----------------------
To transform NCSES tables (in JSON Lines format) into machine-readable CSV and ML Croissant metadata files:

    python ncses_transformer.py input_file.jsonl --output-dir output_folder

Arguments:
    input_file.jsonl : Path to the input JSON Lines file.
    --output-dir      : (Optional) Output directory for generated files (default: output)

This script auto-detects table structure (simple, hierarchical, time series) and applies appropriate transformation.
"""

import argparse
import csv
import json
import os
import re
import logging
from typing import Dict, List, Any, Tuple, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ncses_transformer")

@dataclass
class TableClassification:
    """Classification information for a table."""
    table_id: str
    primary_type: str
    hierarchy_depth_rows: int
    hierarchy_depth_cols: int
    has_time_series: bool
    special_values: Set[str]
    numeric_types: Set[str]


class NCSESTableTransformer:
    """
    Transform NCSES tables from JSON Lines format to CSV and ML Croissant metadata.
    """
    
    # Define table type classifications
    TABLE_TYPES = {
        "ST": "Simple Tabular",
        "RH": "Row Hierarchical",
        "CH": "Column Hierarchical",
        "MH": "Matrix Hierarchical",
        "TS": "Time Series", 
        "SP": "Specialized"
    }
    
    # Special value mappings
    SPECIAL_VALUES = {
        "*": "value between 0.00% and 0.05%",
        "D": "suppressed to avoid disclosure of confidential information",
        "i": "imputed value",
        "r": "revised value"
    }
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create tables directory for table-centric organization
        self.tables_dir = self.output_dir / "tables"
        self.tables_dir.mkdir(exist_ok=True)
        
        # Create catalog directory
        self.catalog_dir = self.output_dir / "catalog"
        self.catalog_dir.mkdir(exist_ok=True)
        
        # Initialize catalog
        self.catalog = []
        
        # Create a root README file
        self.create_root_readme()
    
    def create_root_readme(self):
        """Create a README file at the root of the output directory."""
        readme_path = self.output_dir / "README.md"
        
        content = "# NCSES Tables in ML-Ready Format\n\n"
        content += "This directory contains NCSES statistical tables converted to machine-readable formats "
        content += "with ML Croissant metadata for machine learning applications.\n\n"
        
        content += "## Directory Structure\n\n"
        content += "- `tables/`: Contains one directory per table, each with:\n"
        content += "  - `data.csv`: Table data in CSV format\n"
        content += "  - `croissant_metadata.json`: ML Croissant metadata\n"
        content += "  - `README.md`: Table documentation\n\n"
        content += "- `catalog/`: Contains catalog files\n"
        content += "  - `catalog.json`: Complete catalog in JSON format\n"
        content += "  - `catalog.csv`: Simplified catalog in CSV format\n\n"
        
        content += "## Table Types\n\n"
        for code, desc in self.TABLE_TYPES.items():
            content += f"- **{code}**: {desc}\n"
        
        content += "\n## Special Values\n\n"
        for val, desc in self.SPECIAL_VALUES.items():
            content += f"- **{val}**: {desc}\n"
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
    def clean_text(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities."""
        if not isinstance(text, str):
            return str(text)
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = html.unescape(text)
        return text
    
    def standardize_value(self, value: str) -> Any:
        """Standardize cell values and handle special cases."""
        if not isinstance(value, str):
            return value
            
        value = self.clean_text(value)
        
        # Handle special values
        if value == "*":
            return 0.05  # Representing <0.05%
        elif value == "D":
            return None  # Suppressed value
        elif value.strip() == "":
            return None
            
        # Try to convert to numeric
        try:
            # Remove commas from numbers like "1,234.56"
            clean_value = value.replace(',', '')
            if "." in clean_value:
                return float(clean_value)
            else:
                return int(clean_value)
        except ValueError:
            return value
    
    def extract_hierarchy(self, row_label: str) -> Tuple[List[str], int]:
        """Extract hierarchy levels from a row label."""
        if " -> " in row_label:
            levels = row_label.split(" -> ")
            return levels, len(levels)
        return [row_label], 1
    
    def classify_table(self, table: Dict[str, Any]) -> TableClassification:
        """Determine the primary and secondary classifications for a table."""
        table_id = table.get("metadata", {}).get("modal_id", "unknown")
        
        # Analyze hierarchy in rows
        max_row_depth = 1
        for row in table.get("body", []):
            if row and isinstance(row[0], str):
                _, depth = self.extract_hierarchy(row[0])
                max_row_depth = max(max_row_depth, depth)
        
        # Analyze hierarchy in columns
        max_col_depth = 1
        header = table.get("header", [])
        col_hierarchy = any(" -> " in str(col) for col in header)
        if col_hierarchy:
            for col in header:
                if isinstance(col, str) and " -> " in col:
                    _, depth = self.extract_hierarchy(col)
                    max_col_depth = max(max_col_depth, depth)
        
        # Detect time series
        has_time_series = any(
            re.search(r'(19|20)\d\d', str(row[0])) for row in table.get("body", []) if row
        )
        
        # Check for special values
        special_values = set()
        for row in table.get("body", []):
            for cell in row:
                if isinstance(cell, str):
                    for special_val in self.SPECIAL_VALUES:
                        if special_val in cell:
                            special_values.add(special_val)
        
        # Detect numeric types
        numeric_types = set()
        for row in table.get("body", []):
            for cell in row[1:]:  # Skip the row header
                if isinstance(cell, (int, float)):
                    numeric_types.add(type(cell).__name__)
                elif isinstance(cell, str):
                    clean_cell = re.sub(r'[^\d.]', '', cell)
                    if clean_cell:
                        if "." in clean_cell:
                            numeric_types.add("float")
                        else:
                            numeric_types.add("int")
        
        # Determine primary classification
        primary_type = "ST"  # Default: Simple Tabular
        
        if has_time_series and max_col_depth > 1:
            primary_type = "TS"  # Time Series with hierarchical columns
        elif has_time_series:
            primary_type = "TS"  # Time Series
        elif max_row_depth > 1 and max_col_depth > 1:
            primary_type = "MH"  # Matrix Hierarchical
        elif max_row_depth > 1:
            primary_type = "RH"  # Row Hierarchical
        elif max_col_depth > 1:
            primary_type = "CH"  # Column Hierarchical
            
        return TableClassification(
            table_id=table_id,
            primary_type=primary_type,
            hierarchy_depth_rows=max_row_depth,
            hierarchy_depth_cols=max_col_depth,
            has_time_series=has_time_series,
            special_values=special_values,
            numeric_types=numeric_types
        )
    
    def transform_to_csv(self, table: Dict[str, Any], classification: TableClassification) -> str:
        """
        Transform table to CSV format based on its classification.
        Returns the path to the created CSV file.
        """
        table_id = classification.table_id
        
        # Create a directory for this specific table
        table_dir = self.tables_dir / table_id
        table_dir.mkdir(exist_ok=True)
        
        csv_filename = f"data.csv"
        csv_path = table_dir / csv_filename
        
        header = table.get("header", [])
        body = table.get("body", [])
        metadata = table.get("metadata", {})
        
        # Clean header values
        header_values = [self.clean_text(h) for h in header]
        
        # Prepare CSV rows based on table type
        if classification.primary_type in ["RH", "MH"]:
            # For hierarchical rows, we need to create level columns
            csv_rows = []
            
            # Create the header row with hierarchy level columns
            max_depth = classification.hierarchy_depth_rows
            # Use domain-specific names instead of generic ones for hierarchical fields
            # Determine the domain name based on the first column header
            domain_name = re.sub(r'[^a-zA-Z0-9_]', '_', header[0].lower()) if header else "characteristic"
            domain_name = re.sub(r'_+', '_', domain_name)
            if domain_name.endswith('_'):
                domain_name = domain_name[:-1]
                
            header_row = ["table_id", "row_id", f"{domain_name}_full_path"]
            for i in range(1, max_depth + 1):
                header_row.append(f"{domain_name}_level_{i}")
            header_row.append(f"{domain_name}_hierarchy_depth")
            
            # Add data columns from the original header
            for i, col in enumerate(header_values):
                if i > 0:  # Skip the first column which is usually a label for row headers
                    # Create a clean column name
                    col_name = re.sub(r'[^a-zA-Z0-9_]', '_', col.lower())
                    col_name = re.sub(r'_+', '_', col_name)
                    col_name = f"field_{col_name}"
                    header_row.append(col_name)
            
            csv_rows.append(header_row)
            
            # Process each row
            for i, row in enumerate(body):
                if not row:
                    continue
                    
                row_label = str(row[0])
                levels, depth = self.extract_hierarchy(row_label)
                
                # Create the row with hierarchy information
                csv_row = [
                    table_id,
                    f"r{str(i+1).zfill(3)}",
                    row_label
                ]
                
                # Add each hierarchy level, padding with empty strings if needed
                for level_idx in range(max_depth):
                    csv_row.append(levels[level_idx] if level_idx < len(levels) else "")
                
                csv_row.append(depth)
                
                # Add data values
                for j in range(1, len(row)):
                    csv_row.append(self.standardize_value(row[j]))
                
                csv_rows.append(csv_row)
                
        elif classification.primary_type in ["CH", "TS"]:
            # For column hierarchical or time series tables
            csv_rows = []
            
            # For column hierarchical tables, we need to transform the columns
            # to create a more normalized structure
            
            # First, process the hierarchical header columns
            col_headers = []
            col_levels = {}
            max_col_depth = classification.hierarchy_depth_cols
            
            for i, col in enumerate(header_values):
                if i == 0:  # Skip the first column which is usually a row label
                    col_headers.append(col)
                    continue
                
                # Extract hierarchy levels for this column
                if " -> " in col:
                    levels = col.split(" -> ")
                    col_headers.append(levels[-1])  # Add the leaf level as column name
                    
                    # Store the full hierarchy for this column
                    col_levels[i] = levels
                else:
                    col_headers.append(col)
                    col_levels[i] = [col]
            
            # Create header row for CSV
            header_row = ["table_id", "row_id", "time_period"]
            
            # If this is a time series with hierarchical columns, add hierarchy info with domain-specific naming
            if max_col_depth > 1:
                # Determine column domain name from the header context
                col_domain = "column"
                if len(header) > 1 and " -> " in header[1]:
                    col_domain_parts = header[1].split(" -> ")
                    if col_domain_parts:
                        col_domain = re.sub(r'[^a-zA-Z0-9_]', '_', col_domain_parts[0].lower())
                        col_domain = re.sub(r'_+', '_', col_domain)
                        if col_domain.endswith('_'):
                            col_domain = col_domain[:-1]
                
                for i in range(1, max_col_depth + 1):
                    header_row.append(f"{col_domain}_level_{i}")
                header_row.append(f"{col_domain}_hierarchy_depth")
            
            header_row.append("value")
            csv_rows.append(header_row)
            
            # For time series tables, we'll transform to a long format
            # with one row per time period and performer combination
            if classification.has_time_series:
                row_id_counter = 1
                
                # Process each row (time period)
                for i, row in enumerate(body):
                    if not row:
                        continue
                    
                    time_period = str(row[0])
                    
                    # For each column (performer), create a separate row
                    for j in range(1, len(row)):
                        value = self.standardize_value(row[j])
                        
                        # Skip if value is None or empty
                        if value is None or value == "":
                            continue
                        
                        # Create a CSV row in long format
                        csv_row = [
                            table_id,
                            f"r{str(row_id_counter).zfill(3)}",
                            time_period
                        ]
                        
                        # Add column hierarchy information if needed
                        if max_col_depth > 1:
                            # Use the same domain name as in the header row
                            col_domain = "column"
                            if len(header) > 1 and " -> " in header[1]:
                                col_domain_parts = header[1].split(" -> ")
                                if col_domain_parts:
                                    col_domain = re.sub(r'[^a-zA-Z0-9_]', '_', col_domain_parts[0].lower())
                                    col_domain = re.sub(r'_+', '_', col_domain)
                                    if col_domain.endswith('_'):
                                        col_domain = col_domain[:-1]
                            
                            levels = col_levels.get(j, [col_headers[j]])
                            for level_idx in range(max_col_depth):
                                csv_row.append(levels[level_idx] if level_idx < len(levels) else "")
                            csv_row.append(len(levels))
                        
                        # Add the value
                        csv_row.append(value)
                        
                        csv_rows.append(csv_row)
                        row_id_counter += 1
            else:
                # For non-time series tables with hierarchical columns
                # Process each row
                for i, row in enumerate(body):
                    if not row:
                        continue
                    
                    row_label = str(row[0])
                    
                    # For each column, create a separate row
                    for j in range(1, len(row)):
                        value = self.standardize_value(row[j])
                        
                        # Skip if value is None or empty
                        if value is None or value == "":
                            continue
                        
                        # Create a CSV row
                        csv_row = [
                            table_id,
                            f"r{str(i+1).zfill(3)}_{j}",
                            row_label
                        ]
                        
                        # Add column hierarchy information
                        if max_col_depth > 1:
                            # Use the same domain name as in the header row
                            col_domain = "column"
                            if len(header) > 1 and " -> " in header[1]:
                                col_domain_parts = header[1].split(" -> ")
                                if col_domain_parts:
                                    col_domain = re.sub(r'[^a-zA-Z0-9_]', '_', col_domain_parts[0].lower())
                                    col_domain = re.sub(r'_+', '_', col_domain)
                                    if col_domain.endswith('_'):
                                        col_domain = col_domain[:-1]
                            
                            levels = col_levels.get(j, [col_headers[j]])
                            for level_idx in range(max_col_depth):
                                csv_row.append(levels[level_idx] if level_idx < len(levels) else "")
                            csv_row.append(len(levels))
                        
                        # Add the value
                        csv_row.append(value)
                        
                        csv_rows.append(csv_row)
        else:
            # For simpler tables, use a more straightforward approach
            csv_rows = []
            
            # Header row
            header_row = ["table_id", "row_id"]
            for col in header_values:
                col_name = re.sub(r'[^a-zA-Z0-9_]', '_', col.lower())
                col_name = re.sub(r'_+', '_', col_name)
                header_row.append(col_name)
            
            csv_rows.append(header_row)
            
            # Data rows
            for i, row in enumerate(body):
                if not row:
                    continue
                    
                csv_row = [table_id, f"r{str(i+1).zfill(3)}"]
                for cell in row:
                    csv_row.append(self.standardize_value(cell))
                
                csv_rows.append(csv_row)
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in csv_rows:
                writer.writerow(row)
        
        return str(csv_path)
    
    def create_croissant_metadata(self, table: Dict[str, Any], classification: TableClassification, 
                                  csv_path: str) -> str:
        """
        Create ML Croissant metadata for the transformed table.
        Returns the path to the created metadata file.
        """
        table_id = classification.table_id
        
        # Get the table directory (parent of the CSV file)
        table_dir = Path(csv_path).parent
        metadata_filename = "croissant_metadata.json"
        metadata_path = table_dir / metadata_filename
        
        table_metadata = table.get("metadata", {})
        header = table.get("header", [])
        
        # Base metadata structure - ensuring ML Croissant schema compatibility
        croissant_metadata = {
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "dct:conformsTo": "http://mlcommons.org/croissant/1.0",
            "name": table_metadata.get("title", f"NCSES Table {table_id}"),
            "identifier": f"NCSES-{table_id}",
            "description": table_metadata.get("title", ""),
            "url": f"https://example.org/datasets/ncses/tables/{table_id}",
            "table_number": table_metadata.get("number", ""),
            "creator": {
                "@type": "Organization",
                "name": "National Center for Science and Engineering Statistics"
            },
            "schemaVersion": "https://w3id.org/croissant/schema/1.0",
            "distribution": {
                "@type": "DataDownload",
                "encodingFormat": "text/csv",
                "contentUrl": f"https://example.org/datasets/ncses/tables/{table_id}/data.csv"
            },
            "variableMeasured": [],
            "structuralType": "table",
            "transformationNotes": {
                "cleaningOperations": ["HTML tag removal", "Hierarchy normalization", "Special value handling"],
                "specialValues": {}
            }
        }
        
        # Add notes if available
        if "notes" in table_metadata and table_metadata["notes"]:
            croissant_metadata["notes"] = table_metadata["notes"]
            
        # Add sources if available
        if "sources" in table_metadata and table_metadata["sources"]:
            croissant_metadata["sources"] = table_metadata["sources"]
            
        # Add temporal coverage if available or detected
        if "year" in table_metadata:
            croissant_metadata["temporalCoverage"] = str(table_metadata["year"])
        elif classification.has_time_series:
            # For time series, try to extract years from the body's first column
            years = []
            for row in table.get("body", []):
                if row and row[0]:
                    matches = re.findall(r'(19|20)\d\d', str(row[0]))
                    years.extend(matches)
            if years:
                croissant_metadata["temporalCoverage"] = f"{min(years)}/{max(years)}"
        
        # Add special values information
        for special_val in classification.special_values:
            if special_val in self.SPECIAL_VALUES:
                croissant_metadata["transformationNotes"]["specialValues"][special_val] = self.SPECIAL_VALUES[special_val]
        
        # Add variable measured information based on table type
        if classification.primary_type in ["RH", "MH"]:
            # Hierarchical row structure - use additionalProperty array for ML Croissant compatibility
            # Determine domain name based on the first column header for consistency with CSV
            domain_name = re.sub(r'[^a-zA-Z0-9_]', '_', header[0].lower()) if header else "characteristic"
            domain_name = re.sub(r'_+', '_', domain_name)
            if domain_name.endswith('_'):
                domain_name = domain_name[:-1]
                
            # Create a more descriptive field name based on the actual content
            clean_description = self.clean_text(header[0]) if header else "Row characteristic or category"
            
            characteristic_variable = {
                "@type": "PropertyValue",
                "name": domain_name,
                "description": f"{clean_description} hierarchy",
                "valueType": "string",
                "additionalProperty": [
                    {
                        "name": "hierarchical",
                        "value": "true"
                    },
                    {
                        "name": "maxHierarchyDepth",
                        "value": str(classification.hierarchy_depth_rows)
                    },
                    {
                        "name": "levelColumns",
                        "value": ", ".join([f"{domain_name}_level_{i}" for i in range(1, classification.hierarchy_depth_rows + 1)])
                    },
                    {
                        "name": "fullPathColumn",
                        "value": f"{domain_name}_full_path"
                    }
                ]
            }
            croissant_metadata["variableMeasured"].append(characteristic_variable)
            
            # Extract field names from the first row of the CSV
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header_row = next(reader)
                
                # Find field columns (those starting with "field_")
                for col in header_row:
                    if col.startswith("field_"):
                        # Create individual variable entry with minimal assumptions
                        field_variable = {
                            "@type": "PropertyValue",
                            "name": col,
                            "description": col.replace('field_', '').replace('_', ' ').title(),
                            "valueType": "string"  # Default all to string
                        }
                        
                        # Add unit information generically if available, but skip obvious non-measurement fields
                        if "units_of_measurement" in table_metadata:
                            units = table_metadata.get("units_of_measurement", "")
                            # Only add unitText if it's not clearly a non-measurement field
                            if not any(term in col.lower() for term in ["code", "id", "identifier", "name"]):
                                field_variable["unitText"] = units.strip("()")
                        
                        croissant_metadata["variableMeasured"].append(field_variable)
            
        elif classification.primary_type in ["CH", "TS"]:
            # For column hierarchical or time series tables
            
            # Time period variable
            time_period_variable = {
                "@type": "PropertyValue",
                "name": "time_period",
                "description": "Time period of the measurement",
                "valueType": "string"
            }
            croissant_metadata["variableMeasured"].append(time_period_variable)
            
            # If there are hierarchical columns, add column hierarchy information
            if classification.hierarchy_depth_cols > 1:
                # Determine column domain name from the header context
                col_domain = "column"
                col_description = "Column category or characteristic"
                if len(header) > 1 and " -> " in header[1]:
                    col_domain_parts = header[1].split(" -> ")
                    if col_domain_parts:
                        col_domain = re.sub(r'[^a-zA-Z0-9_]', '_', col_domain_parts[0].lower())
                        col_domain = re.sub(r'_+', '_', col_domain)
                        if col_domain.endswith('_'):
                            col_domain = col_domain[:-1]
                        col_description = f"{self.clean_text(col_domain_parts[0])} hierarchy"
                
                column_hierarchy_variable = {
                    "@type": "PropertyValue",
                    "name": f"{col_domain}_characteristic",
                    "description": col_description,
                    "valueType": "string",
                    "additionalProperty": [
                        {
                            "name": "hierarchical",
                            "value": "true"
                        },
                        {
                            "name": "maxHierarchyDepth",
                            "value": str(classification.hierarchy_depth_cols)
                        },
                        {
                            "name": "levelColumns",
                            "value": ", ".join([f"{col_domain}_level_{i}" for i in range(1, classification.hierarchy_depth_cols + 1)])
                        }
                    ]
                }
                croissant_metadata["variableMeasured"].append(column_hierarchy_variable)
            
            # Value variable - simple definition without type assumptions
            value_variable = {
                "@type": "PropertyValue",
                "name": "value",
                "description": "Measurement value",
                "valueType": "string"  # Default to string for all values
            }
            
            # Only apply units to value fields
            if "units_of_measurement" in table_metadata:
                units = table_metadata.get("units_of_measurement", "")
                value_variable["unitText"] = units.strip("()")
                    
            croissant_metadata["variableMeasured"].append(value_variable)
            
        else:
            # Simple table structure
            # Extract column names from the first row of the CSV
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header_row = next(reader)
                # Skip table_id and row_id
                for col in header_row[2:]:
                    variable = {
                        "@type": "PropertyValue",
                        "name": col,
                        "description": col.replace('_', ' ').title(),
                        "valueType": "string"  # Default all to string
                    }
                    
                    # Add unit information generically if available, but skip obvious non-measurement fields
                    if "units_of_measurement" in table_metadata:
                        units = table_metadata.get("units_of_measurement", "")
                        # Only add unitText if it's not clearly a non-measurement field
                        if not any(term in col.lower() for term in ["code", "id", "identifier", "name"]):
                            variable["unitText"] = units.strip("()")
                    
                    croissant_metadata["variableMeasured"].append(variable)
        
        # Write metadata to file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(croissant_metadata, f, indent=2)
            
        return str(metadata_path)
    
    def add_to_catalog(self, table: Dict[str, Any], classification: TableClassification, 
                      csv_path: str, metadata_path: str):
        """Add the transformed table to the catalog."""
        table_id = classification.table_id
        table_metadata = table.get("metadata", {})
        
        catalog_entry = {
            "modal_id": table_id,
            "table_number": table_metadata.get("number", ""),
            "title": table_metadata.get("title", f"Table {table_id}"),
            "classification": {
                "primary_type": classification.primary_type,
                "hierarchy_depth_rows": classification.hierarchy_depth_rows,
                "hierarchy_depth_cols": classification.hierarchy_depth_cols,
                "has_time_series": classification.has_time_series
            },
            "csv_path": csv_path,
            "metadata_path": metadata_path
        }
        
        self.catalog.append(catalog_entry)
    
    def write_catalog(self):
        """Write the catalog to a JSON file."""
        catalog_path = self.catalog_dir / "catalog.json"
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.catalog, f, indent=2)
        
        # Also write a simplified CSV version
        csv_catalog_path = self.catalog_dir / "catalog.csv"
        with open(csv_catalog_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                "modal_id", "table_number", "title", "primary_type", "hierarchy_depth_rows", 
                "hierarchy_depth_cols", "has_time_series", "table_directory"
            ])
            # Write data
            for entry in self.catalog:
                table_dir = Path(entry["csv_path"]).parent
                writer.writerow([
                    entry["modal_id"],
                    entry["table_number"],
                    entry["title"],
                    entry["classification"]["primary_type"],
                    entry["classification"]["hierarchy_depth_rows"],
                    entry["classification"]["hierarchy_depth_cols"],
                    entry["classification"]["has_time_series"],
                    str(table_dir)
                ])
    
    def process_table(self, table: Dict[str, Any]):
        """Process a single table."""
        classification = self.classify_table(table)
        table_id = classification.table_id
        
        logger.info(f"Processing table {table_id} (Type: {classification.primary_type})")
        
        # Transform to CSV
        csv_path = self.transform_to_csv(table, classification)
        logger.info(f"Created CSV: {csv_path}")
        
        # Create metadata
        metadata_path = self.create_croissant_metadata(table, classification, csv_path)
        logger.info(f"Created metadata: {metadata_path}")
        
        # Create README
        readme_path = self.create_readme(table, classification, csv_path, metadata_path)
        logger.info(f"Created README: {readme_path}")
        
        # Add to catalog
        self.add_to_catalog(table, classification, csv_path, metadata_path)
    
    def process_jsonl_file(self, input_file: str):
        """Process all tables from a JSON Lines file."""
        num_tables = 0
        table_types = {}
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    table = json.loads(line.strip())
                    self.process_table(table)
                    num_tables += 1
                    
                    # Count table types for summary
                    classification = self.classify_table(table)
                    table_type = classification.primary_type
                    table_types[table_type] = table_types.get(table_type, 0) + 1
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON at line {line_num}")
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
        
        # Write catalog
        self.write_catalog()
        
        # Update root README with processing summary
        self.update_root_readme_with_summary(num_tables, table_types)
        
        logger.info(f"Processed tables: {len(self.catalog)}")
    
    def update_root_readme_with_summary(self, num_tables: int, table_types: Dict[str, int]):
        """Update the root README with a summary of the processed tables."""
        readme_path = self.output_dir / "README.md"
        
        # Read existing content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add processing summary
        summary = "\n## Processing Summary\n\n"
        summary += f"- Total tables processed: {num_tables}\n"
        summary += "- Tables by type:\n"
        for table_type, count in sorted(table_types.items()):
            type_desc = self.TABLE_TYPES.get(table_type, table_type)
            summary += f"  - {table_type} ({type_desc}): {count}\n"
        
        # Append to content and write back
        content += summary
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def create_readme(self, table: Dict[str, Any], classification: TableClassification,
                       csv_path: str, metadata_path: str) -> str:
        """
        Create a README file for the table with basic information.
        Returns the path to the created README file.
        """
        table_id = classification.table_id
        table_dir = Path(csv_path).parent
        readme_path = table_dir / "README.md"
        
        # Get table metadata
        table_metadata = table.get("metadata", {})
        title = table_metadata.get("title", f"NCSES Table {table_id}")
        notes = table_metadata.get("notes", "")
        sources = table_metadata.get("sources", "")
        units = table_metadata.get("units_of_measurement", "")
        
        # Create README content
        content = f"# {title}\n\n"
        content += f"**Modal ID:** {table_id}\n\n"
        if table_metadata.get("number"):
            content += f"**Table Number:** {table_metadata.get('number')}\n\n"
        content += f"**Type:** {classification.primary_type} ({self.TABLE_TYPES.get(classification.primary_type, '')})\n\n"
        
        if units:
            content += f"**Units:** {units}\n\n"
        
        if notes:
            content += f"## Notes\n\n{notes}\n\n"
            
        if sources:
            content += f"## Sources\n\n{sources}\n\n"
            
        content += "## Files\n\n"
        content += f"- `data.csv`: The table data in CSV format\n"
        content += f"- `croissant_metadata.json`: ML Croissant metadata for machine learning applications\n\n"
        
        content += "## Structure\n\n"
        content += f"- Row hierarchy depth: {classification.hierarchy_depth_rows}\n"
        content += f"- Column hierarchy depth: {classification.hierarchy_depth_cols}\n"
        content += f"- Time series: {'Yes' if classification.has_time_series else 'No'}\n"
        
        if classification.special_values:
            content += "\n## Special Values\n\n"
            for val in classification.special_values:
                if val in self.SPECIAL_VALUES:
                    content += f"- `{val}`: {self.SPECIAL_VALUES[val]}\n"
        
        # Write README file
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return str(readme_path)

def create_readme(self, table: Dict[str, Any], classification: TableClassification,
                    csv_path: str, metadata_path: str) -> str:
    """
    Create a README file for the table with basic information.
    Returns the path to the created README file.
    """
    table_id = classification.table_id
    table_dir = Path(csv_path).parent
    readme_path = table_dir / "README.md"
    
    # Get table metadata
    table_metadata = table.get("metadata", {})
    title = table_metadata.get("title", f"NCSES Table {table_id}")
    notes = table_metadata.get("notes", "")
    sources = table_metadata.get("sources", "")
    units = table_metadata.get("units_of_measurement", "")
    
    # Create README content
    content = f"# {title}\n\n"
    content += f"**Table ID:** {table_id}\n\n"
    content += f"**Type:** {classification.primary_type} ({self.TABLE_TYPES.get(classification.primary_type, '')})\n\n"
    
    if units:
        content += f"**Units:** {units}\n\n"
    
    if notes:
        content += f"## Notes\n\n{notes}\n\n"
        
    if sources:
        content += f"## Sources\n\n{sources}\n\n"
        
    content += "## Files\n\n"
    content += f"- `data.csv`: The table data in CSV format\n"
    content += f"- `croissant_metadata.json`: ML Croissant metadata for machine learning applications\n\n"
    
    content += "## Structure\n\n"
    content += f"- Row hierarchy depth: {classification.hierarchy_depth_rows}\n"
    content += f"- Column hierarchy depth: {classification.hierarchy_depth_cols}\n"
    content += f"- Time series: {'Yes' if classification.has_time_series else 'No'}\n"
    
    if classification.special_values:
        content += "\n## Special Values\n\n"
        for val in classification.special_values:
            if val in self.SPECIAL_VALUES:
                content += f"- `{val}`: {self.SPECIAL_VALUES[val]}\n"
    
    # Write README file
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return str(readme_path)#!/usr/bin/env python3


def main():
    parser = argparse.ArgumentParser(description="Transform NCSES tables to CSV and ML Croissant metadata.")
    parser.add_argument("input_file", help="Path to the input JSON Lines file")
    parser.add_argument("--output-dir", default="output", help="Directory for output files")
    args = parser.parse_args()

    logger.info("Starting NCSES transformation...")
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output directory: {args.output_dir}")

    transformer = NCSESTableTransformer(args.output_dir)
    transformer.process_jsonl_file(args.input_file)
    
    logger.info(f"Transformation complete. Files saved to {args.output_dir}")


if __name__ == "__main__":
    main()
