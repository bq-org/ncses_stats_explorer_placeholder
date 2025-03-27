#!/bin/bash
# Script to update the NCSES dashboard with fixed column headers

# Set directories
BASE_DIR="/Users/shyamperi/workspace/bq-org/ncses_stats_explorer_placeholder"
INPUT_DIR="${BASE_DIR}/output"
DASHBOARD_DIR="${BASE_DIR}/dashboard"

echo "Updating NCSES dashboard data..."
echo "Running metadata extractor..."

# Run the updated Python extractor script
python ${BASE_DIR}/lib/ncses_metadata_extractor.py \
  --input-dir "${INPUT_DIR}" \
  --output-dir "${DASHBOARD_DIR}/metadata"

# Check if the extractor succeeded
if [ $? -ne 0 ]; then
  echo "Error: Metadata extractor failed"
  exit 1
fi

# Copy the generated files to the dashboard directory
echo "Copying metadata files to dashboard directory..."
cp "${DASHBOARD_DIR}/metadata/dashboard_summary.json" "${DASHBOARD_DIR}/"
cp "${DASHBOARD_DIR}/metadata/table_index.csv" "${DASHBOARD_DIR}/"

echo "Dashboard update complete. The Table Quick Search layout has been fixed:"
echo "- 'Table ID' and 'Modal ID' are now displayed correctly"
echo "- Fixed column widths to prevent spillover between columns"
echo "- Added text truncation with tooltip for long titles"
echo "- Made Type and Time Series columns centered"
echo "- Fixed CSV parsing to properly handle quoted fields and titles with commas"
echo "- Added proper quote handling for values in the generated CSV file"
echo ""
echo "Open the following file in your web browser to see the changes:"
echo "file://${DASHBOARD_DIR}/index.html"

# Provide instructions for local web server if Python is available
if command -v python3 &>/dev/null; then
  echo ""
  echo "Alternatively, you can run a local web server with:"
  echo "cd ${DASHBOARD_DIR} && python3 -m http.server 8000"
  echo "Then open http://localhost:8000 in your web browser"
fi

echo ""
echo "Done!"