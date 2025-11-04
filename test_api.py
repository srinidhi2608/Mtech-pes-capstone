import requests

# Make a prediction
response = requests.post(
    "http://localhost:8000/api/performance/predict",
    json={
        "student_id": "STU0001",
        "semester": 1,
        "performance_data": {
            "student_id": "STU0001",
            "semester": 1,
            "previous_score": 75,
            "attendance_percentage": 85,
            "study_hours_per_week": 20,
            "assignment_completion_ rate": 90,
            "previous_semester_cgpa": 7.5,
            "library_visits_per_week": 3,
            "online_resource_usage_hours": 10
        }
    }
)

print(response.json())