// This script fixes the Special Values chart
// Store a reference to the chart instance
let specialValuesChartInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    // Wait for dashboard to be fully loaded and data to be available
    const checkInterval = setInterval(function() {
        if (typeof dashboardData !== 'undefined' && dashboardData.special_values) {
            clearInterval(checkInterval);
            console.log('Dashboard data loaded, fixing special values chart...');
            
            // Patch the original createSpecialValuesChart function to prevent conflicts
            patchOriginalChartFunction();
            
            // Create the special values chart directly
            createFixedSpecialValuesChart();
            
            // Click the special values tab to show it
            const specialValuesTab = document.querySelector('.tab-button[data-tab="special-values"]');
            if (specialValuesTab) {
                console.log('Showing Special Values tab...');
                specialValuesTab.click();
            }
        }
    }, 500); // Check every 500ms
});

// Patch the original createSpecialValuesChart function to use our version
function patchOriginalChartFunction() {
    if (typeof window.originalCreateSpecialValuesChart === 'undefined') {
        // Save the original function
        window.originalCreateSpecialValuesChart = window.createSpecialValuesChart;
        
        // Replace with our function that handles cleanup first
        window.createSpecialValuesChart = function() {
            console.log('Using patched createSpecialValuesChart function');
            
            // Clean up existing chart if it exists
            if (specialValuesChartInstance) {
                specialValuesChartInstance.destroy();
                specialValuesChartInstance = null;
            }
            
            // Create a new chart using our fixed function
            createFixedSpecialValuesChart();
        };
        
        console.log('Successfully patched createSpecialValuesChart function');
    }
}

function createFixedSpecialValuesChart() {
    // Get the canvas element
    const canvas = document.getElementById('special-values-chart');
    if (!canvas) {
        console.error('Could not find special values chart canvas element');
        return;
    }
    
    console.log('Found special values chart canvas');
    
    // Destroy existing chart if it exists
    if (specialValuesChartInstance) {
        specialValuesChartInstance.destroy();
        specialValuesChartInstance = null;
    }
    
    // Get the context
    const ctx = canvas.getContext('2d');
    
    // Get special values data
    const specialValues = dashboardData.special_values;
    console.log('Special values data:', specialValues);
    
    // Define the colors
    const SPECIAL_VALUE_COLORS = {
        'D': '#ef4444', // red
        '*': '#3b82f6', // blue
        'r': '#10b981', // green
        'i': '#f59e0b'  // yellow
    };
    
    // Extract labels and values
    const labels = Object.keys(specialValues);
    const values = Object.values(specialValues);
    
    // Set up colors
    const colors = labels.map(value => SPECIAL_VALUE_COLORS[value] || '#6366f1');
    
    // Create the chart
    specialValuesChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Tables',
                data: values,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Tables'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Special Value Type'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Tables: ${context.raw}`;
                        }
                    }
                }
            }
        }
    });
    
    console.log('Fixed Special Values chart created successfully');
}
