"""
Complete Standalone Integrated Student Performance Prediction System - Phase 1
All components in one file - No external dependencies required
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import os
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manage SQLite database for student performance system"""
    
    def __init__(self, db_path='student_performance.db'):
        self.db_path = db_path
        self.conn = None
        self.create_database()
    
    def create_database(self):
        """Create database and all necessary tables"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Students Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT,
                enrollment_date DATE,
                graduation_date DATE,
                current_semester INTEGER,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student Performance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                semester INTEGER,
                previous_score REAL,
                attendance_percentage REAL,
                study_hours_per_week REAL,
                assignment_completion_rate REAL,
                previous_semester_cgpa REAL,
                library_visits_per_week INTEGER,
                online_resource_usage_hours REAL,
                internal_assessment_score REAL,
                predicted_score REAL,
                prediction_error REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Student Classification Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_classification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                semester INTEGER,
                classification TEXT CHECK(classification IN ('Fast Learner', 'Moderate Learner', 'Slow Learner')),
                classification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Interventions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                semester INTEGER,
                intervention_type TEXT,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_status TEXT DEFAULT 'Pending',
                completion_date TIMESTAMP,
                effectiveness_rating INTEGER,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        # Model Performance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semester INTEGER,
                model_type TEXT,
                rmse REAL,
                mae REAL,
                r2_score REAL,
                training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                training_samples INTEGER
            )
        ''')
        
        self.conn.commit()
        print(f"✓ Database created/connected: {self.db_path}")
    
    def insert_student(self, student_data):
        """Insert a new student"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO students 
            (student_id, name, enrollment_date, current_semester, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            student_data['student_id'],
            student_data.get('name', ''),
            student_data.get('enrollment_date', datetime.now().date()),
            student_data.get('current_semester', 1),
            student_data.get('email', ''),
            student_data.get('phone', '')
        ))
        self.conn.commit()
    
    def insert_performance_data(self, performance_df):
        """Insert performance data from DataFrame"""
        performance_df.to_sql('student_performance', self.conn, 
                             if_exists='append', index=False)
        self.conn.commit()
    
    def insert_classification(self, student_id, semester, classification):
        """Insert student classification"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO student_classification (student_id, semester, classification)
            VALUES (?, ?, ?)
        ''', (student_id, semester, classification))
        self.conn.commit()
    
    def insert_intervention(self, student_id, semester, intervention_type, notes=''):
        """Insert intervention assignment"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO interventions (student_id, semester, intervention_type, notes)
            VALUES (?, ?, ?, ?)
        ''', (student_id, semester, intervention_type, notes))
        self.conn.commit()
    
    def insert_model_performance(self, semester, model_type, metrics, training_samples):
        """Insert model performance metrics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO model_performance 
            (semester, model_type, rmse, mae, r2_score, training_samples)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            semester,
            model_type,
            metrics['rmse'],
            metrics['mae'],
            metrics['r2'],
            training_samples
        ))
        self.conn.commit()
    
    def get_student_history(self, student_id):
        """Get complete history of a student"""
        query = '''
            SELECT sp.*, sc.classification
            FROM student_performance sp
            LEFT JOIN student_classification sc 
                ON sp.student_id = sc.student_id AND sp.semester = sc.semester
            WHERE sp.student_id = ?
            ORDER BY sp.semester
        '''
        return pd.read_sql_query(query, self.conn, params=(student_id,))
    
    def get_semester_statistics(self, semester):
        """Get statistics for a specific semester"""
        query = '''
            SELECT 
                COUNT(DISTINCT student_id) as total_students,
                AVG(internal_assessment_score) as avg_score,
                AVG(attendance_percentage) as avg_attendance,
                AVG(study_hours_per_week) as avg_study_hours
            FROM student_performance
            WHERE semester = ?
        '''
        return pd.read_sql_query(query, self.conn, params=(semester,))
    
    def get_classification_distribution(self, semester):
        """Get classification distribution for a semester"""
        query = '''
            SELECT classification, COUNT(*) as count
            FROM student_classification
            WHERE semester = ?
            GROUP BY classification
        '''
        return pd.read_sql_query(query, self.conn, params=(semester,))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================================================
# STUDENT PERFORMANCE SYSTEM
# ============================================================================

class StudentPerformanceSystem:
    """Main system for predicting student performance"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.student_history = {}
        self.intervention_log = []
        self.model_performance_history = []
        
    def generate_student_data(self, n_students=100, semester=1):
        """Generate synthetic student data"""
        data = {
            'student_id': [f'STU{str(i).zfill(4)}' for i in range(1, n_students + 1)],
            'semester': [semester] * n_students,
            'previous_score': np.random.normal(65, 15, n_students).clip(0, 100),
            'attendance_percentage': np.random.normal(75, 15, n_students).clip(40, 100),
            'study_hours_per_week': np.random.normal(15, 5, n_students).clip(5, 35),
            'assignment_completion_rate': np.random.normal(75, 15, n_students).clip(30, 100),
            'previous_semester_cgpa': np.random.normal(7.0, 1.5, n_students).clip(4.0, 10.0),
            'library_visits_per_week': np.random.poisson(3, n_students),
            'online_resource_usage_hours': np.random.normal(8, 3, n_students).clip(0, 20),
        }
        
        df = pd.DataFrame(data)
        
        # Generate target variable
        df['internal_assessment_score'] = (
            0.4 * df['previous_score'] +
            0.2 * df['attendance_percentage'] +
            0.15 * df['study_hours_per_week'] * 2 +
            0.15 * df['assignment_completion_rate'] +
            0.1 * df['previous_semester_cgpa'] * 10 +
            np.random.normal(0, 5, n_students)
        ).clip(0, 100)
        
        return df
    
    def prepare_features(self, df):
        """Prepare features for model training"""
        feature_columns = [
            'previous_score', 'attendance_percentage', 'study_hours_per_week',
            'assignment_completion_rate', 'previous_semester_cgpa',
            'library_visits_per_week', 'online_resource_usage_hours'
        ]
        
        X = df[feature_columns]
        y = df['internal_assessment_score'] if 'internal_assessment_score' in df.columns else None
        
        return X, y, feature_columns
    
    def train_models(self, X_train, y_train, semester):
        """Train multiple models"""
        models = {
            'Linear Regression': LinearRegression(),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        self.scalers[semester] = scaler
        
        results = {}
        print(f"\nTraining Models for Semester {semester}:")
        print("-" * 50)
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            
            results[name] = {
                'model': model,
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std()
            }
            
            print(f"{name}: CV R² = {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        best_model_name = max(results, key=lambda x: results[x]['cv_r2_mean'])
        self.models[semester] = results[best_model_name]['model']
        
        print(f"\n✓ Best Model: {best_model_name}")
        return results, best_model_name
    
    def predict(self, X, semester):
        """Make predictions"""
        X_scaled = self.scalers[semester].transform(X)
        return self.models[semester].predict(X_scaled)
    
    def evaluate_predictions(self, y_true, y_pred):
        """Evaluate predictions"""
        return {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
    
    def classify_students(self, df, predictions, threshold=5):
        """Classify students"""
        df = df.copy()
        df['predicted_score'] = predictions
        df['score_difference'] = df['internal_assessment_score'] - df['predicted_score']
        
        conditions = [
            (df['score_difference'] >= threshold) | (df['internal_assessment_score'] >= 75),
            (df['score_difference'] <= -threshold) | (df['internal_assessment_score'] < 60),
        ]
        
        choices = ['Fast Learner', 'Slow Learner']
        df['classification'] = np.select(conditions, choices, default='Moderate Learner')
        
        return df
    
    def assign_interventions(self, df):
        """Assign interventions"""
        interventions = []
        
        for idx, row in df.iterrows():
            student_interventions = []
            
            if row['classification'] == 'Fast Learner':
                student_interventions.extend([
                    'Advanced Challenge Problems',
                    'Peer Mentoring Opportunity',
                    'Research Project Assignment'
                ])
            elif row['classification'] == 'Slow Learner':
                if row['attendance_percentage'] < 70:
                    student_interventions.append('Attendance Monitoring')
                if row['assignment_completion_rate'] < 70:
                    student_interventions.append('Assignment Support')
                student_interventions.extend(['Remedial Classes', 'One-on-One Tutoring'])
            else:
                student_interventions.append('Regular Check-ins')
            
            interventions.append(student_interventions)
            
            self.intervention_log.append({
                'student_id': row['student_id'],
                'semester': row['semester'],
                'classification': row['classification'],
                'interventions': student_interventions,
                'timestamp': datetime.now()
            })
        
        df['interventions'] = interventions
        return df
    
    def generate_report(self, df, metrics, semester):
        """Generate report"""
        print("\n" + "="*70)
        print(f"SEMESTER {semester} PERFORMANCE REPORT")
        print("="*70)
        
        print(f"\n1. MODEL PERFORMANCE METRICS")
        print(f"   RMSE: {metrics['rmse']:.2f}")
        print(f"   MAE:  {metrics['mae']:.2f}")
        print(f"   R²:   {metrics['r2']:.4f}")
        
        print(f"\n2. STUDENT CLASSIFICATION DISTRIBUTION")
        classification_counts = df['classification'].value_counts()
        for classification, count in classification_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {classification}: {count} ({percentage:.1f}%)")
        
        print(f"\n3. PERFORMANCE STATISTICS")
        print(f"   Average Score: {df['internal_assessment_score'].mean():.2f}")
        print(f"   Score Range: {df['internal_assessment_score'].min():.2f} - {df['internal_assessment_score'].max():.2f}")
        
        print("\n" + "="*70)
    
    def visualize_results(self, df, semester):
        """Create visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Predicted vs Actual
        colors = {'Fast Learner': 'green', 'Moderate Learner': 'orange', 'Slow Learner': 'red'}
        c = [colors[x] for x in df['classification']]
        axes[0, 0].scatter(df['predicted_score'], df['internal_assessment_score'], alpha=0.6, c=c)
        axes[0, 0].plot([0, 100], [0, 100], 'k--', lw=2)
        axes[0, 0].set_xlabel('Predicted Score')
        axes[0, 0].set_ylabel('Actual Score')
        axes[0, 0].set_title(f'Semester {semester}: Predicted vs Actual')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Classification Distribution
        classification_counts = df['classification'].value_counts()
        colors_bar = [colors[x] for x in classification_counts.index]
        axes[0, 1].bar(classification_counts.index, classification_counts.values, color=colors_bar)
        axes[0, 1].set_title(f'Semester {semester}: Classification')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Score Distribution
        for classification in colors.keys():
            if classification in df['classification'].values:
                subset = df[df['classification'] == classification]['internal_assessment_score']
                axes[1, 0].hist(subset, alpha=0.6, label=classification, bins=15)
        axes[1, 0].set_title('Score Distribution')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Prediction Error
        errors = df['internal_assessment_score'] - df['predicted_score']
        axes[1, 1].hist(errors, bins=20, color='steelblue', edgecolor='black')
        axes[1, 1].axvline(0, color='red', linestyle='--', linewidth=2)
        axes[1, 1].set_title('Prediction Error Distribution')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(f'semester_{semester}_analysis.png', dpi=300, bbox_inches='tight')
        print(f"\n✓ Visualization saved as 'semester_{semester}_analysis.png'")
        plt.close()


# ============================================================================
# INTEGRATED SYSTEM
# ============================================================================

class IntegratedSystem:
    """Complete integrated system"""
    
    def __init__(self, db_path='student_performance.db'):
        self.db = DatabaseManager(db_path)
        self.prediction_system = StudentPerformanceSystem()
        
        print("✓ Integrated System initialized successfully")
    
    def enroll_students(self, n_students, batch_name="2024"):
        """Enroll students"""
        print(f"\n{'='*70}")
        print(f"ENROLLING {n_students} STUDENTS - BATCH {batch_name}")
        print(f"{'='*70}\n")
        
        for i in range(1, n_students + 1):
            student = {
                'student_id': f'STU{batch_name}_{str(i).zfill(4)}',
                'name': f'Student {i}',
                'enrollment_date': datetime.now().date(),
                'current_semester': 1,
                'email': f'student{i}@university.edu',
                'phone': f'+91{9000000000 + i}'
            }
            self.db.insert_student(student)
        
        print(f"✓ {n_students} students enrolled successfully")
    
    def run_complete_semester(self, semester, n_students=100, batch_name="2024"):
        """Run complete semester"""
        print(f"\n{'='*70}")
        print(f"SEMESTER {semester} - COMPLETE WORKFLOW")
        print(f"{'='*70}\n")
        
        # Generate data
        print("Step 1: Generating student data...")
        df = self.prediction_system.generate_student_data(n_students, semester)
        df['student_id'] = [f'STU{batch_name}_{str(i).zfill(4)}' for i in range(1, n_students + 1)]
        
        # Prepare features
        print("Step 2: Preparing features...")
        X, y, _ = self.prediction_system.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, df.index, test_size=0.2, random_state=42
        )
        
        # Train model
        print("\nStep 3: Training model...")
        _, best_model = self.prediction_system.train_models(X_train, y_train, semester)
        
        # Predict
        print("\nStep 4: Making predictions...")
        predictions = self.prediction_system.predict(X_test, semester)
        
        # Evaluate
        metrics = self.prediction_system.evaluate_predictions(y_test, predictions)
        self.prediction_system.model_performance_history.append({'semester': semester, **metrics})
        
        # Store in database
        self.db.insert_model_performance(semester, best_model, metrics, len(X_train))
        
        # Classify and intervene
        test_df = df.loc[idx_test].copy()
        test_df = self.prediction_system.classify_students(test_df, predictions)
        test_df = self.prediction_system.assign_interventions(test_df)
        
        # Store results
        performance_cols = [
            'student_id', 'semester', 'previous_score', 'attendance_percentage',
            'study_hours_per_week', 'assignment_completion_rate', 
            'previous_semester_cgpa', 'library_visits_per_week',
            'online_resource_usage_hours', 'internal_assessment_score',
            'predicted_score', 'prediction_error'
        ]
        test_df['prediction_error'] = test_df['internal_assessment_score'] - test_df['predicted_score']
        
        self.db.insert_performance_data(test_df[performance_cols])
        
        for _, row in test_df.iterrows():
            self.db.insert_classification(row['student_id'], semester, row['classification'])
            for intervention in row['interventions']:
                self.db.insert_intervention(row['student_id'], semester, intervention)
        
        # Report
        self.prediction_system.generate_report(test_df, metrics, semester)
        self.prediction_system.visualize_results(test_df, semester)
        
        print(f"\n✓ Semester {semester} completed!")
        return test_df, metrics
    
    def simulate_full_cycle(self, n_students=100, n_semesters=5, batch_name="2024"):
        """Simulate complete cycle"""
        print("\n" + "="*70)
        print("FULL ACADEMIC CYCLE SIMULATION")
        print("="*70)
        
        self.enroll_students(n_students, batch_name)
        
        all_results = []
        for semester in range(1, n_semesters + 1):
            results_df, metrics = self.run_complete_semester(semester, n_students, batch_name)
            all_results.append((semester, results_df, metrics))
        
        # Overall report
        self.generate_overall_report()
        
        # Export
        self.export_data(all_results)
        
        return all_results
    
    def generate_overall_report(self):
        """Generate overall report"""
        print("\n" + "="*70)
        print("OVERALL PROGRESSION REPORT")
        print("="*70)
        
        performance_df = pd.DataFrame(self.prediction_system.model_performance_history)
        print("\nModel Performance Over Time:")
        print(performance_df.to_string(index=False))
    
    def export_data(self, all_results):
        """Export data"""
        all_data = [df for _, df, _ in all_results]
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_csv('phase1_complete_data.csv', index=False)
            print(f"\n✓ Data exported to 'phase1_complete_data.csv'")
    
    def close(self):
        """Close system"""
        self.db.close()
        print("\n✓ System closed successfully")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("INTEGRATED STUDENT PERFORMANCE PREDICTION SYSTEM")
    print("="*70)
    
    # Configuration
    N_STUDENTS = 100
    N_SEMESTERS = 5
    BATCH_NAME = "2024"
    
    try:
        # Initialize
        system = IntegratedSystem(db_path='student_performance.db')
        
        # Run simulation
        results = system.simulate_full_cycle(
            n_students=N_STUDENTS,
            n_semesters=N_SEMESTERS,
            batch_name=BATCH_NAME
        )
        
        # Close
        system.close()
        
        print("\n" + "="*70)
        print("✅ SIMULATION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n📁 Generated Files:")
        print("  • student_performance.db - SQLite database")
        print("  • semester_1_analysis.png to semester_N_analysis.png")
        print("  • phase1_complete_data.csv")
        print("\n🎯 Next Steps:")
        print("  1. Review visualizations")
        print("  2. Check database for detailed data")
        print("  3. Run Phase 2 for CTC prediction")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()