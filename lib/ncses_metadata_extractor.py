"""
NCSES Metadata Extractor

This script extracts metadata from the transformed NCSES tables to create
a comprehensive index for the dashboard.

Usage:
    python ncses_metadata_extractor.py --input-dir /path/to/input --output-dir /path/to/output
"""

import argparse
import json
import os
import csv
import re
from pathlib import Path
from collections import Counter, defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ncses_extractor")

class NCSESMetadataExtractor:
    """Extract metadata from transformed NCSES tables."""
    
    def __init__(self, input_dir, output_dir):
        """Initialize with the directory containing transformed data."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.tables_dir = self.input_dir / "tables"
        self.catalog_file = self.input_dir / "catalog" / "catalog.json"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            "table_count": 0,
            "table_types": Counter(),
            "temporal_coverage": set(),
            "row_hierarchy_depths": Counter(),
            "column_hierarchy_depths": Counter(),
            "time_series_count": 0,
            "special_values": Counter(),
            "units": Counter(),
            "topics": Counter(),
            "field_counts": Counter(),
            "missing_metadata": [],
            "tables": []
        }
    
    def run(self):
        """Execute the extraction process."""
        logger.info(f"Starting extraction from {self.input_dir}")
        
        # Load catalog if it exists
        catalog_data = self._load_catalog()
        
        # Process individual table directories
        self._process_table_directories(catalog_data)
        
        # Analyze and summarize the extracted data
        self._analyze_results()
        
        return self.results
    
    def _load_catalog(self):
        """Load the catalog file if it exists."""
        if self.catalog_file.exists():
            logger.info(f"Loading catalog from {self.catalog_file}")
            try:
                with open(self.catalog_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading catalog: {e}")
                return []
        else:
            logger.warning(f"Catalog file not found at {self.catalog_file}")
            return []
    
    def _process_table_directories(self, catalog_data):
        """Process each table directory to extract metadata."""
        table_dirs = [d for d in self.tables_dir.iterdir() if d.is_dir()]
        self.results["table_count"] = len(table_dirs)
        
        logger.info(f"Processing {len(table_dirs)} table directories")
        
        # Create a catalog lookup for efficiency
        catalog_lookup = {item.get('modal_id'): item for item in catalog_data}
        
        for table_dir in table_dirs:
            modal_id = table_dir.name
            logger.debug(f"Processing table {modal_id}")
            
            table_info = self._extract_table_info(table_dir, modal_id, catalog_lookup.get(modal_id, {}))
            if table_info:
                self.results["tables"].append(table_info)
    
    def _extract_table_info(self, table_dir, modal_id, catalog_item):
        """Extract information for a single table."""
        metadata_file = table_dir / "croissant_metadata.json"
        data_file = table_dir / "data.csv"
        readme_file = table_dir / "README.md"
        
        table_info = {
            "table_id": modal_id,  # We use modal_id as the unique identifier
            "modal_id": modal_id,
            "table_number": "",
            "title": "",
            "description": "",
            "table_type": "",
            "row_hierarchy_depth": 0,
            "column_hierarchy_depth": 0,
            "has_time_series": False,
            "special_values": [],
            "units": "",
            "field_count": 0,
            "row_count": 0,
            "temporal_coverage": "",
            "topics": [],
            "keywords": []
        }
        
        # Extract from metadata file
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                table_info["title"] = metadata.get("name", "")
                table_info["description"] = metadata.get("description", "")
                
                # Extract units
                if "variableMeasured" in metadata:
                    for var in metadata["variableMeasured"]:
                        if "unitText" in var:
                            unit = var["unitText"]
                            table_info["units"] = unit
                            self.results["units"][unit] += 1
                
                # Count fields
                field_count = len(metadata.get("variableMeasured", []))
                table_info["field_count"] = field_count
                self.results["field_counts"][field_count] += 1
                
                # Extract temporal coverage
                if "temporalCoverage" in metadata:
                    temporal = metadata["temporalCoverage"]
                    table_info["temporal_coverage"] = temporal
                    self.results["temporal_coverage"].add(temporal)
                
                # Extract special values
                if "transformationNotes" in metadata and "specialValues" in metadata["transformationNotes"]:
                    special_values = list(metadata["transformationNotes"]["specialValues"].keys())
                    table_info["special_values"] = special_values
                    for val in special_values:
                        self.results["special_values"][val] += 1
                
                # Extract structure type
                structure_type = metadata.get("structuralType", "")
                if structure_type:
                    table_info["structure_type"] = structure_type
            
            except Exception as e:
                logger.error(f"Error processing metadata for table {table_id}: {e}")
                self.results["missing_metadata"].append(table_id)
        else:
            logger.warning(f"Metadata file not found for table {table_id}")
            self.results["missing_metadata"].append(table_id)
        
        # Extract from README file to get table type information
        if readme_file.exists():
            try:
                with open(readme_file, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    
                    # Extract table type
                    type_match = re.search(r'\*\*Type:\*\* ([A-Z]{2,3})', readme_content)
                    if type_match:
                        table_type = type_match.group(1)
                        table_info["table_type"] = table_type
                        self.results["table_types"][table_type] += 1
                    
                    # Extract table number
                    table_number_match = re.search(r'\*\*Table Number:\*\* ([^\n]+)', readme_content)
                    if table_number_match:
                        table_number = table_number_match.group(1).strip()
                        table_info["table_number"] = table_number
                    
                    # Extract hierarchy depths
                    row_depth_match = re.search(r'Row hierarchy depth: (\d+)', readme_content)
                    if row_depth_match:
                        row_depth = int(row_depth_match.group(1))
                        table_info["row_hierarchy_depth"] = row_depth
                        self.results["row_hierarchy_depths"][row_depth] += 1
                    
                    col_depth_match = re.search(r'Column hierarchy depth: (\d+)', readme_content)
                    if col_depth_match:
                        col_depth = int(col_depth_match.group(1))
                        table_info["column_hierarchy_depth"] = col_depth
                        self.results["column_hierarchy_depths"][col_depth] += 1
                    
                    # Check for time series
                    time_series_match = re.search(r'Time series: (Yes|No)', readme_content)
                    if time_series_match:
                        has_time_series = time_series_match.group(1) == 'Yes'
                        table_info["has_time_series"] = has_time_series
                        if has_time_series:
                            self.results["time_series_count"] += 1
                    
                    # Extract units
                    units_match = re.search(r'\*\*Units:\*\* \((.*?)\)', readme_content)
                    if units_match:
                        units = units_match.group(1)
                        if not table_info["units"]:  # Only set if not already set from metadata
                            table_info["units"] = units
                            self.results["units"][units] += 1
                    
                    # Extract topics from title
                    title = table_info["title"] or ""
                    if title:
                        # Extract keywords from title
                        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
                        stop_words = {'and', 'the', 'for', 'with', 'from', 'etc', 'other'}
                        topics = [w for w in words if w not in stop_words]
                        table_info["topics"] = topics
                        for topic in topics:
                            self.results["topics"][topic] += 1
            
            except Exception as e:
                logger.error(f"Error processing README for table {table_id}: {e}")
        
        # Count rows from CSV file
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    row_count = sum(1 for _ in reader) - 1  # Subtract header row
                    table_info["row_count"] = row_count
            except Exception as e:
                logger.error(f"Error counting rows for table {table_id}: {e}")
        
        # Add catalog information if available
        if catalog_item:
            if "classification" in catalog_item:
                if not table_info["table_type"]:
                    table_info["table_type"] = catalog_item["classification"].get("primary_type", "")
                    if table_info["table_type"]:
                        self.results["table_types"][table_info["table_type"]] += 1
                
                if not table_info["row_hierarchy_depth"]:
                    table_info["row_hierarchy_depth"] = catalog_item["classification"].get("hierarchy_depth_rows", 0)
                    if table_info["row_hierarchy_depth"]:
                        self.results["row_hierarchy_depths"][table_info["row_hierarchy_depth"]] += 1
                
                if not table_info["column_hierarchy_depth"]:
                    table_info["column_hierarchy_depth"] = catalog_item["classification"].get("hierarchy_depth_cols", 0)
                    if table_info["column_hierarchy_depth"]:
                        self.results["column_hierarchy_depths"][table_info["column_hierarchy_depth"]] += 1
                
                if not table_info["has_time_series"]:
                    table_info["has_time_series"] = catalog_item["classification"].get("has_time_series", False)
                    if table_info["has_time_series"]:
                        self.results["time_series_count"] += 1
        
        return table_info
    
    def _analyze_results(self):
        """Analyze and summarize the extracted data."""
        logger.info("Analyzing extracted data")
        
        # Get examples for each table type
        table_type_examples = self._find_table_type_examples()
        self.results["table_type_examples"] = table_type_examples
        
        # Convert counters to regular dictionaries for JSON serialization
        for key, value in self.results.items():
            if isinstance(value, Counter):
                self.results[key] = dict(value)
            elif isinstance(value, set):
                self.results[key] = list(value)
        
        # Add summary statistics
        self.results["summary"] = {
            "total_tables": self.results["table_count"],
            "tables_with_time_series": self.results["time_series_count"],
            "tables_missing_metadata": len(self.results["missing_metadata"]),
            "max_row_hierarchy_depth": max(self.results["row_hierarchy_depths"].keys()) if self.results["row_hierarchy_depths"] else 0,
            "max_column_hierarchy_depth": max(self.results["column_hierarchy_depths"].keys()) if self.results["column_hierarchy_depths"] else 0,
            "most_common_table_type": max(self.results["table_types"].items(), key=lambda x: x[1])[0] if self.results["table_types"] else "",
            "most_common_unit": max(self.results["units"].items(), key=lambda x: x[1])[0] if self.results["units"] else "",
            "top_topics": [topic for topic, _ in sorted(self.results["topics"].items(), key=lambda x: x[1], reverse=True)[:10]] if self.results["topics"] else []
        }
    
    def save_results(self):
        """Save the results to files in the output directory."""
        # Save the full detailed JSON
        detail_path = self.output_dir / "dashboard_full_data.json"
        logger.info(f"Saving detailed results to {detail_path}")
        with open(detail_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        # Save a summary JSON with just the essential dashboard data
        summary_path = self.output_dir / "dashboard_summary.json"
        logger.info(f"Saving summary results to {summary_path}")
        
        summary_data = {
            "table_count": self.results["table_count"],
            "table_types": self.results["table_types"],
            "time_series_count": self.results["time_series_count"],
            "row_hierarchy_depths": self.results["row_hierarchy_depths"],
            "column_hierarchy_depths": self.results["column_hierarchy_depths"],
            "special_values": self.results["special_values"],
            "units": self.results["units"],
            "topics": self.results["topics"],
            "summary": self.results["summary"],
            "table_type_examples": self.results["table_type_examples"]
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        # Create a simple CSV listing all tables with key properties for easy filtering
        csv_path = self.output_dir / "table_index.csv"
        logger.info(f"Saving table index to {csv_path}")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['table_id', 'modal_id', 'table_number', 'title', 'table_type', 'row_hierarchy_depth', 'column_hierarchy_depth', 
                        'has_time_series', 'row_count', 'field_count', 'units']
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, quotechar='"')
            
            writer.writeheader()
            for table in self.results["tables"]:
                writer.writerow({
                    'table_id': table.get('table_id', ''),
                    'modal_id': table.get('modal_id', ''),
                    'table_number': table.get('table_number', ''),
                    'title': table.get('title', ''),
                    'table_type': table.get('table_type', ''),
                    'row_hierarchy_depth': table.get('row_hierarchy_depth', 0),
                    'column_hierarchy_depth': table.get('column_hierarchy_depth', 0),
                    'has_time_series': 'Yes' if table.get('has_time_series', False) else 'No',
                    'row_count': table.get('row_count', 0),
                    'field_count': table.get('field_count', 0),
                    'units': table.get('units', '')
                })
        
        logger.info("Extraction complete")

    def _find_table_type_examples(self):
        """Find examples for each table type to display in the dashboard."""
        table_type_examples = {
            "RH": None,  # Row Hierarchical
            "MH": None,  # Matrix Hierarchical
            "CH": None,  # Column Hierarchical
            "TS": None,  # Time Series
            "ST": None   # Simple Tabular
        }
        
        # Read the catalog.csv file to get table types and modal_ids
        catalog_csv_path = self.input_dir / "catalog" / "catalog.csv"
        if not catalog_csv_path.exists():
            logger.warning(f"Catalog CSV file not found at {catalog_csv_path}")
            return self._create_placeholder_examples(table_type_examples)
            
        # Create a map of modal_id -> primary_type from the CSV
        table_types_by_modal_id = {}
        try:
            with open(catalog_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    modal_id = row.get('modal_id', '')
                    primary_type = row.get('primary_type', '')
                    if modal_id and primary_type:
                        table_types_by_modal_id[modal_id] = primary_type
        except Exception as e:
            logger.error(f"Error reading catalog CSV: {e}")
            return self._create_placeholder_examples(table_type_examples)
        
        # Sort tables by modal_id to ensure consistent examples
        # Combine catalog data with the tables we've already processed
        tables_with_types = []
        for table in self.results["tables"]:
            table_id = table.get("table_id", "")
            if not table_id:
                continue
                
            # If we don't have a table_type from our processing, check the catalog
            table_type = table.get("table_type", "")
            if not table_type and table_id in table_types_by_modal_id:
                table_type = table_types_by_modal_id[table_id]
                table["table_type"] = table_type
                
            if table_type in table_type_examples.keys():
                tables_with_types.append(table)
        
        # Sort by modal_id
        sorted_tables = sorted(tables_with_types, key=lambda t: t.get("table_id", ""))
        
        # First pass: find clean examples with good titles
        for table in sorted_tables:
            table_type = table.get("table_type", "")
            if not table_type or table_type not in table_type_examples.keys():
                continue
            
            # Skip if we already have an example for this type
            if table_type_examples[table_type] is not None:
                continue
            
            # Get a snippet of data for the example
            # Use modal_id as the directory name
            modal_id = table.get("table_id", "")
            table_dir = self.tables_dir / modal_id
            if not table_dir.exists() or not table_dir.is_dir():
                continue
                
            data_file = table_dir / "data.csv"
            if not data_file.exists():
                continue
                
            # Get the first few rows as an example
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    # Read up to 10 lines for the example
                    data_rows = []
                    for i, line in enumerate(f):
                        if i >= 10:  # Limit to 10 rows
                            break
                        data_rows.append(line.strip())
                    
                    if len(data_rows) >= 2:  # Need at least header + one data row
                        example = {
                            "modal_id": modal_id,
                            "table_number": table.get("table_number", ""),  # Include original table number
                            "title": table.get("title", ""),
                            "description": table.get("description", ""),
                            "units": table.get("units", ""),
                            "row_hierarchy_depth": table.get("row_hierarchy_depth", 0),
                            "column_hierarchy_depth": table.get("column_hierarchy_depth", 0),
                            "data_preview": "\n".join(data_rows),
                            "has_time_series": table.get("has_time_series", False),
                        }
                        table_type_examples[table_type] = example
            except Exception as e:
                logger.error(f"Error reading data file for table {modal_id}: {e}")
                continue
        
        # Check if we have examples for all types, if not create placeholders
        for table_type, example in table_type_examples.items():
            if example is None:
                table_type_examples[table_type] = self._create_placeholder_example(table_type)
        
        return table_type_examples
        
    def _create_placeholder_examples(self, table_type_examples):
        """Create placeholder examples when no real examples are available."""
        for table_type in table_type_examples.keys():
            table_type_examples[table_type] = self._create_placeholder_example(table_type)
        return table_type_examples
        
    def _create_placeholder_example(self, table_type):
        """Create a single placeholder example for a specific table type."""
        return {
            "modal_id": "example",
            "table_number": f"Example-{table_type}",
            "title": f"Example {table_type} Table",
            "description": f"This is a placeholder for a {table_type} table.",
            "units": "(Number)",
            "row_hierarchy_depth": 1,
            "column_hierarchy_depth": 1,
            "data_preview": "No example data available.",
            "has_time_series": table_type == "TS",
        }


def main():
    parser = argparse.ArgumentParser(description="Extract metadata from transformed NCSES tables")
    parser.add_argument("--input-dir", required=True, help="Directory containing transformed tables")
    parser.add_argument("--output-dir", required=True, help="Directory to save extracted metadata")
    args = parser.parse_args()
    
    extractor = NCSESMetadataExtractor(args.input_dir, args.output_dir)
    results = extractor.run()
    extractor.save_results()
    
    print(f"Extraction complete. Processed {results['table_count']} tables.")
    print(f"Results saved to {args.output_dir}")


if __name__ == "__main__":
    main()
