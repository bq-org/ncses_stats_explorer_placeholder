// Table Type Examples Integration
// This script enhances the Table Types tab with real examples of each table type

console.log('Table Type Examples script loaded');

// Wait for dashboard data to be loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded, waiting for dashboard data...');
    
    // Wait for dashboard data to be available
    const checkDashboardData = setInterval(function() {
        console.log('Checking if dashboard data is loaded...');
        if (window.dashboardData) {
            console.log('Dashboard data found:', window.dashboardData);
            clearInterval(checkDashboardData);
            // Give some time for the dashboard to fully initialize
            setTimeout(initializeTableTypeExamples, 1000);
        }
    }, 500);
});

// Function to initialize the table type examples
async function initializeTableTypeExamples() {
    try {
        console.log('Initializing table type examples...');
        
        if (!window.dashboardData.table_type_examples) {
            console.log('No table_type_examples in dashboardData, fetching from dashboard_summary.json');
            // Load the table type examples directly from dashboard_summary.json
            const response = await fetch('dashboard_summary.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const summaryData = await response.json();
            console.log('Fetched dashboard_summary.json:', summaryData);
            
            // Check if the dashboard data has table_type_examples
            if (!summaryData.table_type_examples) {
                console.warn('No table type examples found in the dashboard data');
                return;
            }
            
            // Add to window.dashboardData so it's available elsewhere
            window.dashboardData.table_type_examples = summaryData.table_type_examples;
        }
        
        console.log('Table type examples data:', window.dashboardData.table_type_examples);
        
        // Get the legend items in the Table Types tab
        const legendItems = document.querySelectorAll('#tab-table-types .space-y-1 .flex');
        console.log('Found legend items:', legendItems.length);
        
        if (legendItems.length === 0) {
            console.error('Table Types legend items not found');
            // Let's try a different selector
            const alternativeLegendItems = document.querySelectorAll('#tab-table-types .flex');
            console.log('Alternative selector found items:', alternativeLegendItems.length);
            return;
        }
        
        // Create a container for the examples
        const exampleContainer = document.createElement('div');
        exampleContainer.id = 'table-type-example-container';
        exampleContainer.className = 'mt-4 p-3 border border-gray-200 rounded bg-gray-50 hidden';
        
        // Try different approaches to find where to insert the container
        const legendContainer = document.querySelector('#tab-table-types .space-y-1');
        if (legendContainer) {
            console.log('Found legend container, inserting example container');
            legendContainer.parentNode.insertBefore(exampleContainer, legendContainer.nextSibling);
        } else {
            // Alternative approach - add to the main tab content
            const tableTypesTab = document.getElementById('tab-table-types');
            if (tableTypesTab) {
                console.log('Using alternative approach - adding to main tab');
                tableTypesTab.appendChild(exampleContainer);
            } else {
                console.error('Could not find a place to insert example container');
                return;
            }
        }
        
        // Add examples data and make legend items clickable
        const examples = window.dashboardData.table_type_examples;
        
        // Define the table types and their codes
        const tableTypes = [
            { code: 'RH', name: 'Row Hierarchical' },
            { code: 'MH', name: 'Matrix Hierarchical' },
            { code: 'TS', name: 'Time Series' },
            { code: 'CH', name: 'Column Hierarchical' },
            { code: 'ST', name: 'Simple Tabular' }
        ];
        
        console.log('Attempting to make legend items clickable');
        
        // Try a more specific selector if the original one didn't work
        let targetItems = legendItems.length > 0 ? legendItems : 
                          document.querySelectorAll('#tab-table-types .text-sm .flex') || 
                          document.querySelectorAll('#tab-table-types div div .flex');
        
        console.log('Target items found:', targetItems.length);
        
        // If we still don't have items, create our own legend
        if (targetItems.length === 0) {
            console.log('Creating a new legend section');
            createNewLegendWithExamples(tableTypesTab, examples, tableTypes);
            return;
        }
            if (index < tableTypes.length) {
                const typeCode = tableTypes[index].code;
                const example = examples[typeCode];
                
                // Make the item clickable
                item.style.cursor = 'pointer';
                item.title = 'Click to see example';
                item.classList.add('hover:bg-gray-200', 'p-1', 'rounded');
                
                // Add a "View Example" button
                const viewButton = document.createElement('button');
                viewButton.className = 'ml-auto text-xs text-blue-600 hover:text-blue-800';
                viewButton.textContent = 'View Example';
                item.appendChild(viewButton);
                
                // Add click handler
                item.addEventListener('click', () => {
                    showExample(typeCode, example);
                });
            }
        });
        
    } catch (error) {
        console.error('Error loading table type examples:', error);
    }
}

// Function to show an example for a specific table type
function showExample(typeCode, example) {
    const container = document.getElementById('table-type-example-container');
    if (!container) return;
    
    // Show the container
    container.classList.remove('hidden');
    
    // Get the full name of the table type
    const typeName = getTableTypeFullName(typeCode);
    
    // Update the container content
    if (example) {
        container.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-md font-semibold">${typeName} Example</h3>
                <button class="close-example text-sm text-gray-500 hover:text-gray-700">×</button>
            </div>
            <p class="text-sm text-gray-600 mb-3">${getTableTypeDescription(typeCode)}</p>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="md:col-span-2">
                    <h4 class="font-medium text-sm">${example.title || 'Not Available'}</h4>
                    <div class="flex flex-wrap text-xs text-gray-500 mt-1">
                        <span class="mr-3">Modal ID: ${example.modal_id || 'N/A'}</span>
                        <span class="mr-3">Table Number: ${example.table_number || 'N/A'}</span>
                        <span class="mr-3">Row Hierarchy Depth: ${example.row_hierarchy_depth || '0'}</span>
                        <span>Column Hierarchy Depth: ${example.column_hierarchy_depth || '0'}</span>
                    </div>
                </div>
                <div>
                    <div class="bg-gray-100 p-2 rounded overflow-x-auto">
                        <h4 class="text-xs font-medium mb-1">Data Preview:</h4>
                        <pre class="text-xs">${example.data_preview || 'No data preview available'}</pre>
                    </div>
                </div>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-md font-semibold">${typeName} Example</h3>
                <button class="close-example text-sm text-gray-500 hover:text-gray-700">×</button>
            </div>
            <p class="text-sm text-gray-600 mb-2">${getTableTypeDescription(typeCode)}</p>
            <div class="p-4 bg-gray-100 text-gray-600 text-sm">
                <p>No example available for ${typeName} tables.</p>
            </div>
        `;
    }
    
    // Add click handler for the close button
    const closeButton = container.querySelector('.close-example');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            container.classList.add('hidden');
        });
    }
}

// Helper function to get the full name of a table type
function getTableTypeFullName(type) {
    const typeNames = {
        'RH': 'Row Hierarchical',
        'MH': 'Matrix Hierarchical',
        'CH': 'Column Hierarchical',
        'TS': 'Time Series',
        'ST': 'Simple Tabular'
    };
    
    return typeNames[type] || type;
}

// Helper function to get the description of a table type
function getTableTypeDescription(type) {
    const typeDescriptions = {
        'RH': 'Tables with hierarchical structure in row headers, often used for organizational hierarchies or categorical breakdowns.',
        'MH': 'Tables with hierarchies in both rows and columns, creating a multi-dimensional structure often used for cross-tabulations.',
        'CH': 'Tables with hierarchical structure in column headers, often used for grouped measurements or metrics.',
        'TS': 'Data tracked over multiple time periods (years, quarters, months), showing trends and patterns.',
        'ST': 'Simple tables with flat structure, no nested headers, used for straightforward data presentations.'
    };
    
    return typeDescriptions[type] || '';
}
