"""
Student Performance Prediction System - REST API
FastAPI Backend for Production Deployment
"""

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os


from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import json

# Initialize FastAPI app
app = FastAPI(
    title="Student Performance Prediction API",
    description="REST API for academic performance and CTC prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("frontend"):
    print("WARNING: frontend directory not found!")
else:
    print("✓ Frontend directory found")
    
    # Mount CSS
    if os.path.exists("frontend/css"):
        app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
        print("✓ Mounted /css")
    
    # Mount JS
    if os.path.exists("frontend/js"):
        app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
        print("✓ Mounted /js")
    
    # Mount pages
    if os.path.exists("frontend/pages"):
        app.mount("/pages", StaticFiles(directory="frontend/pages", html=True), name="pages")
        print("✓ Mounted /pages")
    
    # Mount everything under /static
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    print("✓ Mounted /static")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.mount("/static/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/static/js", StaticFiles(directory="frontend/js"), name="js")

# Serve main page
@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/pages/{page_name}", include_in_schema=False)
async def serve_page(page_name: str):
    return FileResponse(f"frontend/pages/{page_name}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class StudentBase(BaseModel):
    student_id: str
    name: str
    email: str
    phone: Optional[str] = None
    batch: str

class StudentCreate(StudentBase):
    enrollment_date: Optional[str] = None

class Student(StudentBase):
    current_semester: int
    created_at: str
    
    class Config:
        from_attributes = True

class PerformanceData(BaseModel):
    student_id: str
    semester: int
    previous_score: float = Field(ge=0, le=100)
    attendance_percentage: float = Field(ge=0, le=100)
    study_hours_per_week: float = Field(ge=0, le=168)
    assignment_completion_rate: float = Field(ge=0, le=100)
    previous_semester_cgpa: float = Field(ge=0, le=10)
    library_visits_per_week: int = Field(ge=0)
    online_resource_usage_hours: float = Field(ge=0)

class PerformancePredictionRequest(BaseModel):
    student_id: str
    semester: int
    performance_data: PerformanceData

class PerformancePredictionResponse(BaseModel):
    student_id: str
    semester: int
    predicted_score: float
    classification: str
    recommended_interventions: List[str]
    confidence: float

class SkillsData(BaseModel):
    student_id: str
    programming_skills: int = Field(ge=0, le=100)
    data_analysis_skills: int = Field(ge=0, le=100)
    web_development: int = Field(ge=0, le=100)
    communication: int = Field(ge=0, le=100)
    teamwork: int = Field(ge=0, le=100)
    problem_solving: int = Field(ge=0, le=100)
    num_internships: int = Field(ge=0)
    num_projects: int = Field(ge=0)
    num_certifications: int = Field(ge=0)

class CTCPredictionRequest(BaseModel):
    student_id: str
    skills_data: SkillsData

class CTCPredictionResponse(BaseModel):
    student_id: str
    predicted_ctc_min: float
    predicted_ctc_avg: float
    predicted_ctc_max: float
    recommended_companies: List[Dict[str, Any]]
    improvement_suggestions: List[str]

class InterventionData(BaseModel):
    student_id: str
    semester: int
    intervention_type: str
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    total_students: int
    fast_learners: int
    moderate_learners: int
    slow_learners: int
    average_cgpa: float
    average_attendance: float
    placement_rate: float

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class Database:
    def __init__(self, db_path='student_performance.db'):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        conn.close()
    
    def fetch_query(self, query, params=None):
        conn = self.get_connection()
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df

db = Database()

# ============================================================================
# MODEL MANAGER
# ============================================================================

class ModelManager:
    def __init__(self):
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        self.performance_models = {}
        self.ctc_model = None
        self.scalers = {}
    
    def save_model(self, model, model_name):
        filepath = os.path.join(self.models_dir, f'{model_name}.pkl')
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        print(f"✓ Model saved: {filepath}")
    
    def load_model(self, model_name):
        filepath = os.path.join(self.models_dir, f'{model_name}.pkl')
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return None
    
    def get_performance_model(self, semester):
        if semester not in self.performance_models:
         model_package = self.load_model(f'performance_sem_{semester}')
        if model_package:
            self.performance_models[semester] = model_package
        return self.performance_models.get(semester)
    
    def get_ctc_model(self):
        if not self.ctc_model:
            self.ctc_model = self.load_model('ctc_prediction')
        return self.ctc_model

model_manager = ModelManager()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "Student Performance Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "students": "/api/students",
            "performance": "/api/performance",
            "ctc": "/api/ctc",
            "dashboard": "/api/dashboard",
            "docs": "/docs"
        }
    }

# ============================================================================
# STUDENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/students", response_model=Dict[str, Any])
async def create_student(student: StudentCreate):
    """Create a new student"""
    try:
        query = """
            INSERT INTO students (student_id, name, email, phone, enrollment_date, current_semester)
            VALUES (?, ?, ?, ?, ?, 1)
        """
        enrollment_date = student.enrollment_date or datetime.now().strftime('%Y-%m-%d')
        
        db.execute_query(query, (
            student.student_id,
            student.name,
            student.email,
            student.phone,
            enrollment_date
        ))
        
        return {
            "status": "success",
            "message": f"Student {student.student_id} created successfully",
            "student_id": student.student_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/students", response_model=List[Dict[str, Any]])
async def get_all_students(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all students with pagination"""
    query = f"""
        SELECT student_id, name, email, phone, current_semester, enrollment_date, created_at
        FROM students
        LIMIT {limit} OFFSET {offset}
    """
    df = db.fetch_query(query)
    return df.to_dict('records')

@app.get("/api/students/{student_id}", response_model=Dict[str, Any])
async def get_student(student_id: str):
    """Get student details"""
    query = "SELECT * FROM students WHERE student_id = ?"
    df = db.fetch_query(query, (student_id,))
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return df.iloc[0].to_dict()

@app.get("/api/students/{student_id}/history", response_model=List[Dict[str, Any]])
async def get_student_history(student_id: str):
    """Get complete academic history for a student"""
    query = """
        SELECT 
            sp.*,
            sc.classification
        FROM student_performance sp
        LEFT JOIN student_classification sc 
            ON sp.student_id = sc.student_id AND sp.semester = sc.semester
        WHERE sp.student_id = ?
        ORDER BY sp.semester
    """
    df = db.fetch_query(query, (student_id,))
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No history found for student")
    
    return df.to_dict('records')

# ============================================================================
# PERFORMANCE PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/performance/predict", response_model=PerformancePredictionResponse)
async def predict_performance(request: PerformancePredictionRequest):
    """Predict student performance for a semester"""
    try:
        # Get model for the semester
        model_package = model_manager.get_performance_model(request.semester)
        
        if not model_package:
            raise HTTPException(...)
        features = pd.DataFrame([{...}])
        X_scaled = model_package['scaler'].transform(features)
        prediction = float(model_package['model'].predict(X_scaled)[0])
        
        # Prepare features
        features = pd.DataFrame([{
            'previous_score': request.performance_data.previous_score,
            'attendance_percentage': request.performance_data.attendance_percentage,
            'study_hours_per_week': request.performance_data.study_hours_per_week,
            'assignment_completion_rate': request.performance_data.assignment_completion_rate,
            'previous_semester_cgpa': request.performance_data.previous_semester_cgpa,
            'library_visits_per_week': request.performance_data.library_visits_per_week,
            'online_resource_usage_hours': request.performance_data.online_resource_usage_hours
        }])
        
        # Make prediction
        prediction = float(model.predict(features)[0])
        
        # Classify student
        if prediction >= 75:
            classification = "Fast Learner"
            interventions = ["Advanced Challenge Problems", "Peer Mentoring", "Research Projects"]
        elif prediction < 60:
            classification = "Slow Learner"
            interventions = ["Remedial Classes", "One-on-One Tutoring", "Study Skills Workshop"]
        else:
            classification = "Moderate Learner"
            interventions = ["Regular Check-ins", "Study Groups"]
        
        # Add specific interventions based on features
        if request.performance_data.attendance_percentage < 75:
            interventions.append("Attendance Monitoring")
        if request.performance_data.study_hours_per_week < 15:
            interventions.append("Time Management Training")
        
        # Calculate confidence (simplified)
        confidence = 0.85  # In production, use model's prediction intervals
        
        return PerformancePredictionResponse(
            student_id=request.student_id,
            semester=request.semester,
            predicted_score=round(prediction, 2),
            classification=classification,
            recommended_interventions=interventions,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/submit")
async def submit_performance(data: PerformanceData):
    """Submit actual performance data"""
    try:
        query = """
            INSERT INTO student_performance (
                student_id, semester, previous_score, attendance_percentage,
                study_hours_per_week, assignment_completion_rate, 
                previous_semester_cgpa, library_visits_per_week,
                online_resource_usage_hours, internal_assessment_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # For now, use predicted score as actual (in production, get actual score)
        internal_score = data.previous_score  # Placeholder
        
        db.execute_query(query, (
            data.student_id,
            data.semester,
            data.previous_score,
            data.attendance_percentage,
            data.study_hours_per_week,
            data.assignment_completion_rate,
            data.previous_semester_cgpa,
            data.library_visits_per_week,
            data.online_resource_usage_hours,
            internal_score
        ))
        
        return {
            "status": "success",
            "message": "Performance data submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/performance/semester/{semester}")
async def get_semester_performance(semester: int):
    """Get performance statistics for a semester"""
    query = """
        SELECT 
            COUNT(*) as total_students,
            AVG(internal_assessment_score) as avg_score,
            MIN(internal_assessment_score) as min_score,
            MAX(internal_assessment_score) as max_score,
            AVG(attendance_percentage) as avg_attendance
        FROM student_performance
        WHERE semester = ?
    """
    df = db.fetch_query(query, (semester,))
    
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for this semester")
    
    return df.iloc[0].to_dict()

# ============================================================================
# CTC PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/ctc/predict", response_model=CTCPredictionResponse)
async def predict_ctc(request: CTCPredictionRequest):
    """Predict CTC for a student"""
    try:
        # Get student's academic performance
        query = """
            SELECT 
                AVG(internal_assessment_score) as avg_score,
                AVG(attendance_percentage) as avg_attendance
            FROM student_performance
            WHERE student_id = ?
        """
        perf_df = db.fetch_query(query, (request.student_id,))
        
        if perf_df.empty:
            raise HTTPException(status_code=404, detail="No performance data found")
        
        # Calculate CGPA
        final_cgpa = (perf_df['avg_score'].iloc[0] / 10)
        
        # Simple CTC prediction logic (in production, use trained model)
        base_ctc = final_cgpa * 1.5  # Simplified formula
        
        # Adjust based on skills
        skill_bonus = (
            request.skills_data.programming_skills * 0.03 +
            request.skills_data.communication * 0.02 +
            request.skills_data.num_internships * 0.5 +
            request.skills_data.num_projects * 0.3
        ) / 100
        
        predicted_ctc_avg = base_ctc + skill_bonus
        predicted_ctc_min = predicted_ctc_avg * 0.85
        predicted_ctc_max = predicted_ctc_avg * 1.15
        
        # Recommend companies
        recommended_companies = [
            {
                "name": "Tech Corp",
                "type": "Product Based",
                "ctc": round(predicted_ctc_max, 2),
                "match_score": 92
            },
            {
                "name": "IT Services Ltd",
                "type": "Service Based",
                "ctc": round(predicted_ctc_avg, 2),
                "match_score": 85
            },
            {
                "name": "Innovation Inc",
                "type": "Startup",
                "ctc": round(predicted_ctc_min, 2),
                "match_score": 78
            }
        ]
        
        # Generate improvement suggestions
        improvements = []
        if request.skills_data.programming_skills < 80:
            improvements.append("Improve programming skills through coding practice")
        if request.skills_data.num_internships < 2:
            improvements.append("Gain more internship experience")
        if request.skills_data.num_projects < 3:
            improvements.append("Build more projects")
        if request.skills_data.communication < 75:
            improvements.append("Enhance communication skills")
        
        if not improvements:
            improvements.append("Excellent profile! Focus on interview preparation")
        
        return CTCPredictionResponse(
            student_id=request.student_id,
            predicted_ctc_min=round(predicted_ctc_min, 2),
            predicted_ctc_avg=round(predicted_ctc_avg, 2),
            predicted_ctc_max=round(predicted_ctc_max, 2),
            recommended_companies=recommended_companies,
            improvement_suggestions=improvements
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INTERVENTION ENDPOINTS
# ============================================================================

@app.post("/api/interventions")
async def create_intervention(intervention: InterventionData):
    """Assign an intervention to a student"""
    try:
        query = """
            INSERT INTO interventions (student_id, semester, intervention_type, notes)
            VALUES (?, ?, ?, ?)
        """
        db.execute_query(query, (
            intervention.student_id,
            intervention.semester,
            intervention.intervention_type,
            intervention.notes
        ))
        
        return {
            "status": "success",
            "message": "Intervention assigned successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/interventions/{student_id}")
async def get_student_interventions(student_id: str):
    """Get all interventions for a student"""
    query = """
        SELECT * FROM interventions
        WHERE student_id = ?
        ORDER BY assigned_date DESC
    """
    df = db.fetch_query(query, (student_id,))
    return df.to_dict('records')

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        # Get classification distribution - FIXED query
        class_query = """
            SELECT 
                classification,
                COUNT(*) as count
            FROM student_classification
            WHERE classification IS NOT NULL
            GROUP BY classification
        """
        
        try:
            class_df = db.fetch_query(class_query)
        except:
            # If table doesn't exist or is empty, return zeros
            class_df = pd.DataFrame({'classification': [], 'count': []})
        
        # Get performance stats
        perf_query = """
            SELECT 
                COUNT(DISTINCT student_id) as total_students,
                AVG(internal_assessment_score) / 10 as avg_cgpa,
                AVG(attendance_percentage) as avg_attendance
            FROM student_performance
        """
        
        try:
            perf_df = db.fetch_query(perf_query)
        except:
            # If table doesn't exist, return zeros
            perf_df = pd.DataFrame({
                'total_students': [0],
                'avg_cgpa': [0.0],
                'avg_attendance': [0.0]
            })
        
        # Parse classification counts safely
        class_counts = {}
        if len(class_df) > 0:
            class_counts = dict(zip(class_df['classification'], class_df['count']))
        
        # Return with safe defaults
        total = int(perf_df['total_students'].iloc[0]) if len(perf_df) > 0 and not pd.isna(perf_df['total_students'].iloc[0]) else 0
        avg_cgpa = float(perf_df['avg_cgpa'].iloc[0]) if len(perf_df) > 0 and not pd.isna(perf_df['avg_cgpa'].iloc[0]) else 0.0
        avg_att = float(perf_df['avg_attendance'].iloc[0]) if len(perf_df) > 0 and not pd.isna(perf_df['avg_attendance'].iloc[0]) else 0.0
        
        return DashboardStats(
            total_students=total,
            fast_learners=int(class_counts.get('Fast Learner', 0)),
            moderate_learners=int(class_counts.get('Moderate Learner', 0)),
            slow_learners=int(class_counts.get('Slow Learner', 0)),
            average_cgpa=round(avg_cgpa, 2),
            average_attendance=round(avg_att, 2),
            placement_rate=85.5  # Placeholder
        )
        
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        # Return default values on error
        return DashboardStats(
            total_students=0,
            fast_learners=0,
            moderate_learners=0,
            slow_learners=0,
            average_cgpa=0.0,
            average_attendance=0.0,
            placement_rate=0.0
        )

@app.get("/api/dashboard/trends")
async def get_performance_trends():
    """Get performance trends over semesters"""
    query = """
        SELECT 
            semester,
            AVG(internal_assessment_score) as avg_score,
            AVG(attendance_percentage) as avg_attendance,
            COUNT(*) as student_count
        FROM student_performance
        GROUP BY semester
        ORDER BY semester
    """
    df = db.fetch_query(query)
    return df.to_dict('records')

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if os.path.exists(db.db_path) else "disconnected"
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 STARTING STUDENT PERFORMANCE API SERVER")
    print("="*70)
    print("\n📍 API will be available at:")
    print("   • Local:   http://localhost:8000")
    print("   • Docs:    http://localhost:8000/docs")
    print("   • ReDoc:   http://localhost:8000/redoc")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)