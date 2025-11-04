/**
 * Main Application Logic
 * Handles UI interactions and data flow
 */

// Load Dashboard Data
async function loadDashboardData() {
    showLoading();
    
    try {
        // Fetch dashboard statistics
        const stats = await getDashboardStats();
        
        // Update stat cards
        document.getElementById('totalStudents').textContent = stats.total_students || 0;
        document.getElementById('fastLearners').textContent = stats.fast_learners || 0;
        document.getElementById('moderateLearners').textContent = stats.moderate_learners || 0;
        document.getElementById('slowLearners').textContent = stats.slow_learners || 0;
        
        // Create classification chart
        createClassificationChart(stats);
        
        // Fetch and display trends
        const trends = await getPerformanceTrends();
        createPerformanceTrendChart(trends);
        
        // Load recent students
        await loadRecentStudents();
        
        hideLoading();
        showToast('Dashboard loaded successfully', 'success');
    } catch (error) {
        hideLoading();
        showToast('Error loading dashboard: ' + error.message, 'error');
        console.error('Dashboard load error:', error);
    }
}

// Load Recent Students Table
async function loadRecentStudents() {
    try {
        const students = await getStudents(5, 0); // Get first 5 students
        const tbody = document.getElementById('studentsTableBody');
        
        if (!students || students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No students found</td></tr>';
            return;
        }
        
        tbody.innerHTML = students.map(student => `
            <tr>
                <td><strong>${student.student_id}</strong></td>
                <td>${student.name || 'N/A'}</td>
                <td>${student.current_semester || 1}</td>
                <td>7.5</td>
                <td><span class="badge badge-success">Fast Learner</span></td>
                <td>
                    <button class="btn-sm" onclick="viewStudent('${student.student_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading recent students:', error);
        document.getElementById('studentsTableBody').innerHTML = 
            '<tr><td colspan="6" class="text-center">Error loading students</td></tr>';
    }
}

// Show Add Student Modal
function showAddStudentModal() {
    document.getElementById('addStudentModal').classList.add('active');
}

// Close Modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Add Student
async function addStudent(event) {
    event.preventDefault();
    showLoading();
    
    const studentData = {
        student_id: document.getElementById('studentId').value,
        name: document.getElementById('studentName').value,
        email: document.getElementById('studentEmail').value,
        phone: document.getElementById('studentPhone').value,
        batch: document.getElementById('studentBatch').value
    };
    
    try {
        const result = await createStudent(studentData);
        hideLoading();
        closeModal('addStudentModal');
        showToast('Student added successfully!', 'success');
        
        // Reset form
        document.getElementById('addStudentForm').reset();
        
        // Reload dashboard
        loadDashboardData();
    } catch (error) {
        hideLoading();
        showToast('Error adding student: ' + error.message, 'error');
    }
}

// View Student Details
function viewStudent(studentId) {
    window.location.href = `pages/students.html?id=${studentId}`;
}

// Load Trend Data by Semester
async function loadTrendData() {
    const semester = document.getElementById('trendSemester').value;
    
    if (semester === 'all') {
        const trends = await getPerformanceTrends();
        createPerformanceTrendChart(trends);
    } else {
        // Load specific semester data
        const semData = await getSemesterPerformance(semester);
        // Create chart with semester specific data
    }
}

// Export Report
function exportReport() {
    showToast('Generating report...', 'success');
    
    // In a real application, this would generate and download a PDF/CSV
    setTimeout(() => {
        showToast('Report downloaded!', 'success');
    }, 2000);
}

// Initialize page based on URL
function initializePage() {
    const path = window.location.pathname;
    
    if (path.includes('students.html')) {
        loadStudentsPage();
    } else if (path.includes('predictions.html')) {
        loadPredictionsPage();
    } else if (path.includes('ctc.html')) {
        loadCTCPage();
    } else if (path.includes('analytics.html')) {
        loadAnalyticsPage();
    }
}

// Students Page Functions
async function loadStudentsPage() {
    showLoading();
    
    try {
        const students = await getStudents(100, 0);
        displayStudentsTable(students);
        hideLoading();
    } catch (error) {
        hideLoading();
        showToast('Error loading students', 'error');
    }
}

function displayStudentsTable(students) {
    const tbody = document.getElementById('allStudentsTableBody');
    
    if (!tbody) return;
    
    tbody.innerHTML = students.map(student => `
        <tr>
            <td><strong>${student.student_id}</strong></td>
            <td>${student.name || 'N/A'}</td>
            <td>${student.email || 'N/A'}</td>
            <td>${student.phone || 'N/A'}</td>
            <td>${student.current_semester || 1}</td>
            <td>
                <button class="btn-sm btn-primary" onclick="viewStudentDetails('${student.student_id}')">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn-sm btn-success" onclick="predictForStudent('${student.student_id}')">
                    <i class="fas fa-magic"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Predictions Page Functions
async function loadPredictionsPage() {
    // Initialize prediction form
    const form = document.getElementById('predictionForm');
    if (form) {
        form.addEventListener('submit', handlePrediction);
    }
}

async function handlePrediction(event) {
    event.preventDefault();
    showLoading();
    
    const formData = {
        student_id: document.getElementById('pred_studentId').value,
        semester: parseInt(document.getElementById('pred_semester').value),
        performance_data: {
            student_id: document.getElementById('pred_studentId').value,
            semester: parseInt(document.getElementById('pred_semester').value),
            previous_score: parseFloat(document.getElementById('pred_previousScore').value),
            attendance_percentage: parseFloat(document.getElementById('pred_attendance').value),
            study_hours_per_week: parseFloat(document.getElementById('pred_studyHours').value),
            assignment_completion_rate: parseFloat(document.getElementById('pred_assignmentRate').value),
            previous_semester_cgpa: parseFloat(document.getElementById('pred_cgpa').value),
            library_visits_per_week: parseInt(document.getElementById('pred_libraryVisits').value),
            online_resource_usage_hours: parseFloat(document.getElementById('pred_onlineHours').value)
        }
    };
    
    try {
        const result = await predictPerformance(formData);
        hideLoading();
        displayPredictionResult(result);
    } catch (error) {
        hideLoading();
        showToast('Error making prediction: ' + error.message, 'error');
    }
}

function displayPredictionResult(result) {
    const resultDiv = document.getElementById('predictionResult');
    
    if (!resultDiv) return;
    
    const classColors = {
        'Fast Learner': 'success',
        'Moderate Learner': 'warning',
        'Slow Learner': 'danger'
    };
    
    const badgeClass = classColors[result.classification] || 'secondary';
    
    resultDiv.innerHTML = `
        <div class="result-card ${badgeClass}">
            <h3><i class="fas fa-chart-line"></i> Prediction Results</h3>
            <div class="result-grid">
                <div class="result-item">
                    <label>Student ID</label>
                    <p><strong>${result.student_id}</strong></p>
                </div>
                <div class="result-item">
                    <label>Semester</label>
                    <p><strong>${result.semester}</strong></p>
                </div>
                <div class="result-item">
                    <label>Predicted Score</label>
                    <p class="score-large">${result.predicted_score.toFixed(2)}</p>
                </div>
                <div class="result-item">
                    <label>Classification</label>
                    <p><span class="badge badge-${badgeClass}">${result.classification}</span></p>
                </div>
                <div class="result-item">
                    <label>Confidence</label>
                    <p><strong>${(result.confidence * 100).toFixed(1)}%</strong></p>
                </div>
            </div>
            <div class="interventions">
                <h4><i class="fas fa-lightbulb"></i> Recommended Interventions</h4>
                <ul>
                    ${result.recommended_interventions.map(int => `<li>${int}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
}

// CTC Page Functions
async function loadCTCPage() {
    const form = document.getElementById('ctcPredictionForm');
    if (form) {
        form.addEventListener('submit', handleCTCPrediction);
    }
}

async function handleCTCPrediction(event) {
    event.preventDefault();
    showLoading();
    
    const formData = {
        student_id: document.getElementById('ctc_studentId').value,
        skills_data: {
            student_id: document.getElementById('ctc_studentId').value,
            programming_skills: parseInt(document.getElementById('ctc_programming').value),
            data_analysis_skills: parseInt(document.getElementById('ctc_dataAnalysis').value),
            web_development: parseInt(document.getElementById('ctc_webDev').value),
            communication: parseInt(document.getElementById('ctc_communication').value),
            teamwork: parseInt(document.getElementById('ctc_teamwork').value),
            problem_solving: parseInt(document.getElementById('ctc_problemSolving').value),
            num_internships: parseInt(document.getElementById('ctc_internships').value),
            num_projects: parseInt(document.getElementById('ctc_projects').value),
            num_certifications: parseInt(document.getElementById('ctc_certifications').value)
        }
    };
    
    try {
        const result = await predictCTC(formData);
        hideLoading();
        displayCTCResult(result);
    } catch (error) {
        hideLoading();
        showToast('Error predicting CTC: ' + error.message, 'error');
    }
}

function displayCTCResult(result) {
    const resultDiv = document.getElementById('ctcResult');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
        <div class="result-card success">
            <h3><i class="fas fa-money-bill-wave"></i> CTC Prediction Results</h3>
            <div class="ctc-range">
                <div class="ctc-item">
                    <label>Minimum</label>
                    <p class="ctc-amount">₹${result.predicted_ctc_min.toFixed(2)} LPA</p>
                </div>
                <div class="ctc-item highlight">
                    <label>Expected</label>
                    <p class="ctc-amount">₹${result.predicted_ctc_avg.toFixed(2)} LPA</p>
                </div>
                <div class="ctc-item">
                    <label>Maximum</label>
                    <p class="ctc-amount">₹${result.predicted_ctc_max.toFixed(2)} LPA</p>
                </div>
            </div>
            
            <div class="companies-section">
                <h4><i class="fas fa-building"></i> Recommended Companies</h4>
                <div class="companies-list">
                    ${result.recommended_companies.map(company => `
                        <div class="company-card">
                            <h5>${company.name}</h5>
                            <p class="company-type">${company.type}</p>
                            <p class="company-ctc">₹${company.ctc.toFixed(2)} LPA</p>
                            <div class="match-score">
                                <div class="match-bar" style="width: ${company.match_score}%"></div>
                                <span>${company.match_score}% Match</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="improvements-section">
                <h4><i class="fas fa-chart-line"></i> Improvement Suggestions</h4>
                <ul>
                    ${result.improvement_suggestions.map(sugg => `<li>${sugg}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    resultDiv.style.display = 'block';
}

// Analytics Page Functions
async function loadAnalyticsPage() {
    showLoading();
    
    try {
        // Load various analytics
        const stats = await getDashboardStats();
        const trends = await getPerformanceTrends();
        
        // Create multiple charts
        createClassificationChart(stats);
        createPerformanceTrendChart(trends);
        // Add more charts as needed
        
        hideLoading();
    } catch (error) {
        hideLoading();
        showToast('Error loading analytics', 'error');
    }
}

// Utility Functions
function predictForStudent(studentId) {
    window.location.href = `predictions.html?student_id=${studentId}`;
}

function viewStudentDetails(studentId) {
    // Create a modal or redirect to detailed view
    showStudentDetailsModal(studentId);
}

async function showStudentDetailsModal(studentId) {
    showLoading();
    
    try {
        const student = await getStudent(studentId);
        const history = await getStudentHistory(studentId);
        
        // Create modal HTML
        const modalHTML = `
            <div class="modal active" id="studentDetailsModal">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h3><i class="fas fa-user"></i> Student Details - ${student.student_id}</h3>
                        <button class="modal-close" onclick="closeModal('studentDetailsModal')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="student-info">
                            <div class="info-item">
                                <label>Name</label>
                                <p>${student.name}</p>
                            </div>
                            <div class="info-item">
                                <label>Email</label>
                                <p>${student.email}</p>
                            </div>
                            <div class="info-item">
                                <label>Phone</label>
                                <p>${student.phone || 'N/A'}</p>
                            </div>
                            <div class="info-item">
                                <label>Current Semester</label>
                                <p>${student.current_semester}</p>
                            </div>
                        </div>
                        
                        <h4>Academic History</h4>
                        <table class="history-table">
                            <thead>
                                <tr>
                                    <th>Semester</th>
                                    <th>Score</th>
                                    <th>Attendance</th>
                                    <th>Classification</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${history.map(h => `
                                    <tr>
                                        <td>${h.semester}</td>
                                        <td>${h.internal_assessment_score?.toFixed(2) || 'N/A'}</td>
                                        <td>${h.attendance_percentage?.toFixed(1) || 'N/A'}%</td>
                                        <td><span class="badge badge-success">${h.classification || 'N/A'}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        // Append to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        hideLoading();
    } catch (error) {
        hideLoading();
        showToast('Error loading student details', 'error');
    }
}

// Search functionality
function setupSearch() {
    const searchInput = document.querySelector('.search-box input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
}

function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupSearch();
    initializePage();
});