"""
Train and save models for the API to use
Run this once after Phase 1 completes
"""

import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Create models directory
os.makedirs('models', exist_ok=True)

print("Loading Phase 1 data...")
# Load data from Phase 1
try:
    df = pd.read_csv('phase1_complete_data.csv')
    print(f"✓ Loaded {len(df)} records")
except FileNotFoundError:
    print("✗ phase1_complete_data.csv not found!")
    print("  Please run Phase 1 first: python integrated_system_standalone.py")
    exit(1)

# Get unique semesters
semesters = df['semester'].unique()
print(f"\nTraining models for {len(semesters)} semesters...")

for semester in sorted(semesters):
    print(f"\nSemester {semester}:")
    
    # Get data for this semester
    sem_data = df[df['semester'] == semester].copy()
    
    # Prepare features
    feature_columns = [
        'previous_score', 'attendance_percentage', 'study_hours_per_week',
        'assignment_completion_rate', 'previous_semester_cgpa',
        'library_visits_per_week', 'online_resource_usage_hours'
    ]
    
    # Check if we have all columns
    missing_cols = [col for col in feature_columns if col not in sem_data.columns]
    if missing_cols:
        print(f"  ⚠ Missing columns: {missing_cols}, skipping...")
        continue
    
    X = sem_data[feature_columns]
    y = sem_data['internal_assessment_score']
    
    # Skip if too few samples
    if len(X) < 10:
        print(f"  ⚠ Only {len(X)} samples, skipping...")
        continue
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Save model and scaler as a package
    model_package = {
        'model': model,
        'scaler': scaler,
        'features': feature_columns
    }
    
    # Save to file
    filename = f'models/performance_sem_{semester}.pkl'
    with open(filename, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"  ✓ Model saved: {filename}")
    print(f"  Training samples: {len(X_train)}")

print("\n✓ All models saved successfully!")
print("\nYou can now use the API with trained models.")
print("Restart the API server: python api.py")