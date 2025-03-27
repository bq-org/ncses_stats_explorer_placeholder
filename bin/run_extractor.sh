#!/bin/bash
# Script to run the NCSES metadata extractor and setup the dashboard

# Default input and output directories
INPUT_DIR="/Users/shyamperi/workspace/bq-org/ncses_stats_explorer_placeholder/output"
DASHBOARD_DIR="/Users/shyamperi/workspace/bq-org/ncses_stats_explorer_placeholder/dashboard"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --input-dir)
      INPUT_DIR="$2"
      shift 2
      ;;
    --dashboard-dir)
      DASHBOARD_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--input-dir /path/to/input] [--dashboard-dir /path/to/dashboard]"
      exit 1
      ;;
  esac
done

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
  echo "Error: Input directory does not exist: $INPUT_DIR"
  exit 1
fi

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
  echo "Error: Dashboard directory does not exist: $DASHBOARD_DIR"
  exit 1
fi

# Create a temporary directory for extracted metadata
METADATA_DIR="$DASHBOARD_DIR/metadata"
mkdir -p "$METADATA_DIR"

echo "Running NCSES metadata extractor..."
echo "Input directory: $INPUT_DIR"
echo "Dashboard directory: $DASHBOARD_DIR"
echo "Metadata directory: $METADATA_DIR"

# Run the Python extractor
python /Users/shyamperi/workspace/bq-org/ncses_stats_explorer_placeholder/lib/ncses_metadata_extractor.py \
  --input-dir "$INPUT_DIR" \
  --output-dir "$METADATA_DIR"

# Check if the extractor succeeded
if [ $? -ne 0 ]; then
  echo "Error: Metadata extractor failed"
  exit 1
fi

# Copy the generated files to the dashboard directory
echo "Copying metadata files to dashboard directory..."
cp "$METADATA_DIR/dashboard_summary.json" "$DASHBOARD_DIR/"
cp "$METADATA_DIR/table_index.csv" "$DASHBOARD_DIR/"

echo "Dashboard setup complete. Open the following file in your web browser:"
echo "file://$DASHBOARD_DIR/index.html"

# Provide instructions for local web server if Python is available
if command -v python3 &>/dev/null; then
  echo ""
  echo "Alternatively, you can run a local web server with:"
  echo "cd $DASHBOARD_DIR && python3 -m http.server 8000"
  echo "Then open http://localhost:8000 in your web browser"
fi

echo ""
echo "Done!"
