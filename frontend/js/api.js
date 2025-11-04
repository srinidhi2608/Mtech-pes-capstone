/**
 * API Connection Layer
 * Handles all communication with the backend API
 */

const API_BASE_URL = 'http://localhost:8000/api';

// Utility function to handle API responses
async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'An error occurred');
    }
    return response.json();
}

// Show loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// API Functions

// Dashboard Statistics
async function getDashboardStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        throw error;
    }
}

// Get all students
async function getStudents(limit = 100, offset = 0) {
    try {
        const response = await fetch(`${API_BASE_URL}/students?limit=${limit}&offset=${offset}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching students:', error);
        throw error;
    }
}

// Get single student
async function getStudent(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/students/${studentId}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching student:', error);
        throw error;
    }
}

// Get student history
async function getStudentHistory(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/students/${studentId}/history`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching student history:', error);
        throw error;
    }
}

// Create new student
async function createStudent(studentData) {
    try {
        const response = await fetch(`${API_BASE_URL}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(studentData)
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error creating student:', error);
        throw error;
    }
}

// Predict performance
async function predictPerformance(predictionData) {
    try {
        const response = await fetch(`${API_BASE_URL}/performance/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(predictionData)
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error predicting performance:', error);
        throw error;
    }
}

// Predict CTC
async function predictCTC(ctcData) {
    try {
        const response = await fetch(`${API_BASE_URL}/ctc/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(ctcData)
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error predicting CTC:', error);
        throw error;
    }
}

// Get performance trends
async function getPerformanceTrends() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/trends`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching trends:', error);
        throw error;
    }
}

// Get semester performance
async function getSemesterPerformance(semester) {
    try {
        const response = await fetch(`${API_BASE_URL}/performance/semester/${semester}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching semester performance:', error);
        throw error;
    }
}

// Get student interventions
async function getStudentInterventions(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/interventions/${studentId}`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching interventions:', error);
        throw error;
    }
}

// Create intervention
async function createIntervention(interventionData) {
    try {
        const response = await fetch(`${API_BASE_URL}/interventions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(interventionData)
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error creating intervention:', error);
        throw error;
    }
}

// Health check
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error checking health:', error);
        throw error;
    }
}