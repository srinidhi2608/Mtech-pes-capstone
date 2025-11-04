/**
 * Charts and Visualizations
 * Uses Chart.js for data visualization
 */

let performanceTrendChart = null;
let classificationChart = null;

// Create Performance Trend Chart
function createPerformanceTrendChart(data) {
    const ctx = document.getElementById('performanceTrendChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (performanceTrendChart) {
        performanceTrendChart.destroy();
    }
    
    // Prepare data
    const labels = data.map(d => `Sem ${d.semester}`);
    const scores = data.map(d => d.avg_score || 0);
    
    performanceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Score',
                data: scores,
                borderColor: '#4F46E5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#4F46E5',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    callbacks: {
                        label: function(context) {
                            return `Score: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Create Classification Distribution Chart
function createClassificationChart(stats) {
    const ctx = document.getElementById('classificationChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (classificationChart) {
        classificationChart.destroy();
    }
    
    const data = {
        labels: ['Fast Learners', 'Moderate Learners', 'At-Risk Students'],
        datasets: [{
            data: [
                stats.fast_learners || 0,
                stats.moderate_learners || 0,
                stats.slow_learners || 0
            ],
            backgroundColor: [
                '#10B981',
                '#F59E0B',
                '#EF4444'
            ],
            borderWidth: 0,
            hoverOffset: 15
        }]
    };
    
    classificationChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 13
                        },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Create CGPA Distribution Chart
function createCGPADistributionChart(data) {
    const ctx = document.getElementById('cgpaDistributionChart');
    if (!ctx) return;
    
    // Sample data structure
    const ranges = ['4.0-5.0', '5.0-6.0', '6.0-7.0', '7.0-8.0', '8.0-9.0', '9.0-10.0'];
    const counts = [5, 15, 25, 30, 20, 5]; // This should come from API
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ranges,
            datasets: [{
                label: 'Number of Students',
                data: counts,
                backgroundColor: '#4F46E5',
                borderRadius: 8,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Create Attendance vs Performance Scatter Chart
function createAttendancePerformanceChart(data) {
    const ctx = document.getElementById('attendancePerformanceChart');
    if (!ctx) return;
    
    // Transform data for scatter plot
    const scatterData = data.map(student => ({
        x: student.attendance_percentage,
        y: student.internal_assessment_score
    }));
    
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Students',
                data: scatterData,
                backgroundColor: 'rgba(79, 70, 229, 0.6)',
                borderColor: '#4F46E5',
                borderWidth: 1,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return [
                                `Attendance: ${context.parsed.x.toFixed(1)}%`,
                                `Score: ${context.parsed.y.toFixed(1)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Attendance %'
                    },
                    min: 0,
                    max: 100
                },
                y: {
                    title: {
                        display: true,
                        text: 'Performance Score'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

// Create CTC Distribution Chart
function createCTCDistributionChart(data) {
    const ctx = document.getElementById('ctcDistributionChart');
    if (!ctx) return;
    
    const companyTypes = ['Product Based', 'MNC', 'Startup', 'Service Based'];
    const avgCTC = [14.5, 12.8, 8.2, 6.5]; // This should come from API
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: companyTypes,
            datasets: [{
                label: 'Average CTC (LPA)',
                data: avgCTC,
                backgroundColor: [
                    '#10B981',
                    '#4F46E5',
                    '#F59E0B',
                    '#EF4444'
                ],
                borderRadius: 8,
                barThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `₹${context.parsed.x} LPA`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '₹' + value + ' LPA';
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Create Skills Radar Chart
function createSkillsRadarChart(skillsData) {
    const ctx = document.getElementById('skillsRadarChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [
                'Programming',
                'Data Analysis',
                'Communication',
                'Problem Solving',
                'Teamwork',
                'Web Development'
            ],
            datasets: [{
                label: 'Skill Level',
                data: [
                    skillsData.programming_skills || 0,
                    skillsData.data_analysis_skills || 0,
                    skillsData.communication || 0,
                    skillsData.problem_solving || 0,
                    skillsData.teamwork || 0,
                    skillsData.web_development || 0
                ],
                backgroundColor: 'rgba(79, 70, 229, 0.2)',
                borderColor: '#4F46E5',
                borderWidth: 2,
                pointBackgroundColor: '#4F46E5',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#4F46E5'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}