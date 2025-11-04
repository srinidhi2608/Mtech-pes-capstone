"""
Phase 2: CTC (Salary) Prediction System - FIXED STANDALONE VERSION
Predicts student placement salary based on academic performance and skills
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

class CTCPredictionSystem:
    """Main system for predicting CTC based on student performance and skills"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.ctc_history = []
        self.skill_importance = {}
        
    def load_phase1_data(self, filepath='phase1_complete_data.csv'):
        """Load Phase 1 output data"""
        try:
            df = pd.read_csv(filepath)
            print(f"✓ Loaded Phase 1 data: {len(df)} records")
            return df
        except FileNotFoundError:
            print(f"✗ File not found: {filepath}")
            print("  Generating sample Phase 1 data...")
            return self.generate_sample_phase1_data()
    
    def generate_sample_phase1_data(self, n_students=100):
        """Generate sample Phase 1 data if file doesn't exist"""
        students = []
        for i in range(1, n_students + 1):
            student_id = f'STU{str(i).zfill(4)}'
            
            # Simulate 8 semesters of data
            for semester in range(1, 9):
                students.append({
                    'student_id': student_id,
                    'semester': semester,
                    'internal_assessment_score': float(np.random.normal(70, 15)),
                    'attendance_percentage': float(np.random.normal(80, 12)),
                    'study_hours_per_week': float(np.random.normal(18, 5)),
                    'assignment_completion_rate': float(np.random.normal(80, 15)),
                    'classification': np.random.choice(['Fast Learner', 'Moderate Learner', 'Slow Learner'], 
                                                      p=[0.35, 0.45, 0.20])
                })
        
        df = pd.DataFrame(students)
        # Clip values to realistic ranges
        df['internal_assessment_score'] = df['internal_assessment_score'].clip(40, 100)
        df['attendance_percentage'] = df['attendance_percentage'].clip(50, 100)
        df['study_hours_per_week'] = df['study_hours_per_week'].clip(8, 35)
        df['assignment_completion_rate'] = df['assignment_completion_rate'].clip(40, 100)
        
        print(f"✓ Generated sample Phase 1 data: {len(df)} records")
        return df
    
    def aggregate_student_performance(self, phase1_df):
        """Aggregate student performance across all semesters"""
        print("\nAggregating student performance data...")
        
        # Get final semester data for each student
        final_semester = phase1_df.groupby('student_id')['semester'].max().reset_index()
        final_semester.columns = ['student_id', 'max_semester']
        
        # Merge to get final semester scores
        phase1_df = phase1_df.merge(final_semester, on='student_id')
        final_data = phase1_df[phase1_df['semester'] == phase1_df['max_semester']].copy()
        
        # Calculate aggregate metrics
        agg_metrics = phase1_df.groupby('student_id').agg({
            'internal_assessment_score': ['mean', 'std', 'min', 'max'],
            'attendance_percentage': 'mean',
            'study_hours_per_week': 'mean',
            'assignment_completion_rate': 'mean'
        }).reset_index()
        
        # Flatten column names
        agg_metrics.columns = ['student_id', 'avg_score', 'score_std', 'min_score', 'max_score',
                               'avg_attendance', 'avg_study_hours', 'avg_assignment_completion']
        
        # Calculate CGPA (assuming 10-point scale)
        agg_metrics['final_cgpa'] = (agg_metrics['avg_score'] / 10).clip(4.0, 10.0)
        
        # Calculate improvement trend
        first_semester = phase1_df[phase1_df['semester'] == 1][['student_id', 'internal_assessment_score']]
        first_semester.columns = ['student_id', 'first_semester_score']
        
        agg_metrics = agg_metrics.merge(first_semester, on='student_id', how='left')
        agg_metrics['score_improvement'] = agg_metrics['avg_score'] - agg_metrics['first_semester_score']
        
        # Get final classification
        final_classification = final_data[['student_id', 'classification']]
        agg_metrics = agg_metrics.merge(final_classification, on='student_id', how='left')
        
        # Calculate learner progression score
        classification_score = {
            'Slow Learner': 1,
            'Moderate Learner': 2,
            'Fast Learner': 3
        }
        agg_metrics['learner_score'] = agg_metrics['classification'].map(classification_score)
        
        print(f"✓ Aggregated data for {len(agg_metrics)} students")
        return agg_metrics
    
    def generate_student_skills_data(self, student_performance_df):
        """Generate student skills profile data"""
        print("\nGenerating student skills profiles...")
        
        skills_data = []
        
        for idx, row in student_performance_df.iterrows():
            # Skills correlate with academic performance
            base_skill_level = float((row['final_cgpa'] / 10) * 100)
            
            # Generate random values first, then clip
            prog_raw = float(np.random.normal(base_skill_level, 10))
            data_raw = float(np.random.normal(base_skill_level, 12))
            web_raw = float(np.random.normal(base_skill_level - 5, 15))
            db_raw = float(np.random.normal(base_skill_level - 3, 12))
            comm_raw = float(np.random.normal(base_skill_level + 5, 10))
            team_raw = float(np.random.normal(base_skill_level + 3, 10))
            prob_raw = float(np.random.normal(base_skill_level + 7, 8))
            
            # Clip values
            programming_skills = int(max(30, min(100, prog_raw)))
            data_analysis_skills = int(max(25, min(100, data_raw)))
            web_development = int(max(20, min(100, web_raw)))
            database_skills = int(max(25, min(100, db_raw)))
            communication = int(max(40, min(100, comm_raw)))
            teamwork = int(max(40, min(100, team_raw)))
            problem_solving = int(max(40, min(100, prob_raw)))
            
            # Experience
            num_internships = int(np.random.choice([0, 1, 2, 3], p=[0.2, 0.4, 0.3, 0.1]))
            num_projects = int(np.random.choice([1, 2, 3, 4, 5, 6], p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]))
            num_certifications = int(np.random.choice([0, 1, 2, 3, 4], p=[0.3, 0.35, 0.2, 0.1, 0.05]))
            
            # Domain knowledge
            domain = str(np.random.choice(['Software Development', 'Data Science', 'Web Development', 
                                          'Cloud Computing', 'Mobile Development', 'AI/ML']))
            
            skills_data.append({
                'student_id': row['student_id'],
                'programming_skills': programming_skills,
                'data_analysis_skills': data_analysis_skills,
                'web_development': web_development,
                'database_skills': database_skills,
                'communication': communication,
                'teamwork': teamwork,
                'problem_solving': problem_solving,
                'num_internships': num_internships,
                'num_projects': num_projects,
                'num_certifications': num_certifications,
                'preferred_domain': domain,
                'years_coding_experience': float(np.random.uniform(1, 4))
            })
        
        skills_df = pd.DataFrame(skills_data)
        print(f"✓ Generated skills data for {len(skills_df)} students")
        return skills_df
    
    def generate_employer_data(self, n_companies=50):
        """Generate employer requirements and CTC data"""
        print(f"\nGenerating employer data for {n_companies} companies...")
        
        companies = []
        
        company_types = ['Product Based', 'Service Based', 'Startup', 'MNC']
        sectors = ['IT Services', 'Software Product', 'Consulting', 'E-commerce', 
                  'Fintech', 'Healthcare Tech', 'EdTech']
        
        for i in range(1, n_companies + 1):
            company_type = str(np.random.choice(company_types, p=[0.3, 0.3, 0.2, 0.2]))
            sector = str(np.random.choice(sectors))
            
            # CTC varies by company type
            if company_type == 'Product Based':
                base_ctc = float(np.random.uniform(8, 20))
            elif company_type == 'MNC':
                base_ctc = float(np.random.uniform(7, 18))
            elif company_type == 'Startup':
                base_ctc = float(np.random.uniform(4, 12))
            else:  # Service Based
                base_ctc = float(np.random.uniform(3.5, 10))
            
            # Skill requirements
            min_cgpa = float(np.random.uniform(6.0, 8.0))
            programming_req = int(np.random.randint(60, 95))
            data_analysis_req = int(np.random.randint(40, 85))
            communication_req = int(np.random.randint(50, 90))
            
            # Experience requirements
            internship_preferred = int(np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2]))
            projects_required = int(np.random.randint(2, 6))
            
            companies.append({
                'company_id': f'COMP{str(i).zfill(3)}',
                'company_name': f'Company {i}',
                'company_type': company_type,
                'sector': sector,
                'ctc_lpa': round(base_ctc, 2),
                'min_cgpa_required': round(min_cgpa, 1),
                'programming_skill_required': programming_req,
                'data_analysis_required': data_analysis_req,
                'communication_required': communication_req,
                'min_internships': internship_preferred,
                'min_projects': projects_required,
                'hiring_volume': int(np.random.randint(5, 50))
            })
        
        employer_df = pd.DataFrame(companies)
        print(f"✓ Generated employer data for {len(employer_df)} companies")
        return employer_df
    
    def calculate_skill_match_score(self, student_skills, employer_req):
        """Calculate how well student skills match employer requirements"""
        # Programming match
        prog_match = min(float(student_skills['programming_skills']) / float(employer_req['programming_skill_required']), 1.0)
        
        # Data analysis match
        data_match = min(float(student_skills['data_analysis_skills']) / float(employer_req['data_analysis_required']), 1.0)
        
        # Communication match
        comm_match = min(float(student_skills['communication']) / float(employer_req['communication_required']), 1.0)
        
        # Experience match
        intern_match = 1.0 if int(student_skills['num_internships']) >= int(employer_req['min_internships']) else 0.5
        project_match = min(float(student_skills['num_projects']) / float(employer_req['min_projects']), 1.0)
        
        # Overall skill match score (0-100)
        skill_match_score = (
            prog_match * 0.3 +
            data_match * 0.2 +
            comm_match * 0.15 +
            intern_match * 0.15 +
            project_match * 0.2
        ) * 100
        
        return float(skill_match_score)
    
    def create_placement_dataset(self, student_performance_df, student_skills_df, employer_df):
        """Create comprehensive dataset for CTC prediction"""
        print("\nCreating placement dataset...")
        
        placement_data = []
        
        # For each student, match with potential employers
        for idx, student_perf in student_performance_df.iterrows():
            student_id = student_perf['student_id']
            
            # Get student skills
            student_skill = student_skills_df[student_skills_df['student_id'] == student_id].iloc[0]
            
            # Check CGPA eligibility
            eligible_companies = employer_df[employer_df['min_cgpa_required'] <= student_perf['final_cgpa']]
            
            if len(eligible_companies) == 0:
                continue
            
            # Select a company based on skill match
            skill_matches = []
            for _, company in eligible_companies.iterrows():
                match_score = self.calculate_skill_match_score(student_skill, company)
                skill_matches.append(match_score)
            
            # Higher skill match = higher probability
            skill_matches_array = np.array(skill_matches)
            probabilities = skill_matches_array / skill_matches_array.sum()
            selected_idx = np.random.choice(len(eligible_companies), p=probabilities)
            selected_company = eligible_companies.iloc[selected_idx]
            
            # Calculate skill match score
            skill_match_score = self.calculate_skill_match_score(student_skill, selected_company)
            
            # Combine all features
            placement_record = {
                'student_id': student_id,
                'final_cgpa': float(student_perf['final_cgpa']),
                'avg_score': float(student_perf['avg_score']),
                'score_improvement': float(student_perf['score_improvement']),
                'avg_attendance': float(student_perf['avg_attendance']),
                'avg_study_hours': float(student_perf['avg_study_hours']),
                'learner_score': int(student_perf['learner_score']),
                'programming_skills': int(student_skill['programming_skills']),
                'data_analysis_skills': int(student_skill['data_analysis_skills']),
                'web_development': int(student_skill['web_development']),
                'database_skills': int(student_skill['database_skills']),
                'communication': int(student_skill['communication']),
                'teamwork': int(student_skill['teamwork']),
                'problem_solving': int(student_skill['problem_solving']),
                'num_internships': int(student_skill['num_internships']),
                'num_projects': int(student_skill['num_projects']),
                'num_certifications': int(student_skill['num_certifications']),
                'years_coding_experience': float(student_skill['years_coding_experience']),
                'skill_match_score': float(skill_match_score),
                'company_type': str(selected_company['company_type']),
                'sector': str(selected_company['sector']),
                'ctc_lpa': float(selected_company['ctc_lpa'])
            }
            
            placement_data.append(placement_record)
        
        placement_df = pd.DataFrame(placement_data)
        
        # Add realistic CTC variation
        performance_multiplier = (
            0.3 * (placement_df['final_cgpa'] / 10) +
            0.2 * (placement_df['skill_match_score'] / 100) +
            0.2 * (placement_df['communication'] / 100) +
            0.15 * (placement_df['num_internships'] / 3) +
            0.15 * (placement_df['problem_solving'] / 100)
        )
        
        # Add negotiation variance
        negotiation_factor = np.random.normal(1.0, 0.1, len(placement_df))
        negotiation_factor = np.clip(negotiation_factor, 0.85, 1.15)
        
        placement_df['ctc_lpa'] = placement_df['ctc_lpa'] * performance_multiplier * negotiation_factor
        placement_df['ctc_lpa'] = placement_df['ctc_lpa'].round(2)
        
        print(f"✓ Created placement dataset with {len(placement_df)} records")
        print(f"  CTC Range: ₹{placement_df['ctc_lpa'].min():.2f} - ₹{placement_df['ctc_lpa'].max():.2f} LPA")
        print(f"  Average CTC: ₹{placement_df['ctc_lpa'].mean():.2f} LPA")
        
        return placement_df
    
    def prepare_features_for_ctc_prediction(self, placement_df):
        """Prepare features for CTC prediction model"""
        print("\nPreparing features for CTC prediction...")
        
        df = placement_df.copy()
        
        # Encode categorical variables
        for col in ['company_type', 'sector']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Select features for prediction
        feature_columns = [
            'final_cgpa', 'avg_score', 'score_improvement', 'avg_attendance',
            'learner_score', 'programming_skills', 'data_analysis_skills',
            'communication', 'teamwork', 'problem_solving',
            'num_internships', 'num_projects', 'num_certifications',
            'years_coding_experience', 'skill_match_score',
            'company_type_encoded', 'sector_encoded'
        ]
        
        X = df[feature_columns]
        y = df['ctc_lpa']
        
        print(f"✓ Features prepared: {len(feature_columns)} features")
        return X, y, feature_columns, df
    
    def train_ctc_models(self, X_train, y_train):
        """Train multiple CTC prediction models"""
        print("\nTraining CTC prediction models...")
        print("-" * 50)
        
        models = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0),
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
        }
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        self.scalers['ctc'] = scaler
        
        results = {}
        
        for name, model in models.items():
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            
            # Training predictions
            train_pred = model.predict(X_train_scaled)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
            train_mae = mean_absolute_error(y_train, train_pred)
            
            results[name] = {
                'model': model,
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std(),
                'train_rmse': train_rmse,
                'train_mae': train_mae
            }
            
            print(f"{name}:")
            print(f"  CV R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            print(f"  Train RMSE: ₹{train_rmse:.2f} LPA")
            print(f"  Train MAE: ₹{train_mae:.2f} LPA")
        
        # Select best model
        best_model_name = max(results, key=lambda x: results[x]['cv_r2_mean'])
        self.models['ctc'] = results[best_model_name]['model']
        
        print(f"\n✓ Best Model Selected: {best_model_name}")
        
        # Feature importance
        if best_model_name in ['Random Forest', 'Gradient Boosting']:
            feature_importance = results[best_model_name]['model'].feature_importances_
            self.skill_importance = dict(zip(X_train.columns, feature_importance))
        
        return results, best_model_name
    
    def predict_ctc(self, X):
        """Predict CTC for given features"""
        X_scaled = self.scalers['ctc'].transform(X)
        predictions = self.models['ctc'].predict(X_scaled)
        return predictions
    
    def evaluate_ctc_predictions(self, y_true, y_pred):
        """Evaluate CTC prediction performance"""
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # Calculate percentage error
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        metrics = {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape
        }
        
        return metrics
    
    def generate_ctc_report(self, y_true, y_pred, test_df):
        """Generate comprehensive CTC prediction report"""
        print("\n" + "="*70)
        print("CTC PREDICTION REPORT")
        print("="*70)
        
        metrics = self.evaluate_ctc_predictions(y_true, y_pred)
        
        print(f"\n1. MODEL PERFORMANCE METRICS")
        print(f"   RMSE: ₹{metrics['rmse']:.2f} LPA")
        print(f"   MAE:  ₹{metrics['mae']:.2f} LPA")
        print(f"   R²:   {metrics['r2']:.4f}")
        print(f"   MAPE: {metrics['mape']:.2f}%")
        
        print(f"\n2. CTC STATISTICS")
        print(f"   Actual CTC Range: ₹{y_true.min():.2f} - ₹{y_true.max():.2f} LPA")
        print(f"   Predicted CTC Range: ₹{y_pred.min():.2f} - ₹{y_pred.max():.2f} LPA")
        print(f"   Average Actual CTC: ₹{y_true.mean():.2f} LPA")
        print(f"   Average Predicted CTC: ₹{y_pred.mean():.2f} LPA")
        
        # CTC by company type
        print(f"\n3. CTC BY COMPANY TYPE")
        for company_type in test_df['company_type'].unique():
            mask = test_df['company_type'] == company_type
            avg_ctc = test_df.loc[mask, 'ctc_lpa'].mean()
            count = mask.sum()
            print(f"   {company_type}: ₹{avg_ctc:.2f} LPA (n={count})")
        
        # Feature importance
        if self.skill_importance:
            print(f"\n4. TOP 10 IMPORTANT FEATURES")
            sorted_importance = sorted(self.skill_importance.items(), 
                                      key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in sorted_importance:
                print(f"   {feature}: {importance:.4f}")
        
        print("\n" + "="*70)
        
        return metrics
    
    def visualize_ctc_results(self, y_true, y_pred, test_df, feature_columns):
        """Create comprehensive visualizations for CTC predictions"""
        fig = plt.figure(figsize=(20, 12))
        
        # Convert to numpy arrays
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        
        # 1. Predicted vs Actual CTC
        ax1 = plt.subplot(2, 3, 1)
        ax1.scatter(y_pred_arr, y_true_arr, alpha=0.6, c='steelblue', edgecolors='black', linewidth=0.5)
        ax1.plot([y_true_arr.min(), y_true_arr.max()], [y_true_arr.min(), y_true_arr.max()], 
                'r--', lw=2, label='Perfect Prediction')
        ax1.set_xlabel('Predicted CTC (LPA)', fontsize=11)
        ax1.set_ylabel('Actual CTC (LPA)', fontsize=11)
        ax1.set_title('Predicted vs Actual CTC', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Prediction Error Distribution
        ax2 = plt.subplot(2, 3, 2)
        errors = y_true_arr - y_pred_arr
        ax2.hist(errors, bins=30, color='coral', edgecolor='black', alpha=0.7)
        ax2.axvline(0, color='red', linestyle='--', linewidth=2)
        ax2.set_xlabel('Prediction Error (LPA)', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title('Prediction Error Distribution', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. CTC by Company Type
        ax3 = plt.subplot(2, 3, 3)
        company_ctc = test_df.groupby('company_type')['ctc_lpa'].mean().sort_values(ascending=False)
        colors = plt.cm.Set3(range(len(company_ctc)))
        ax3.barh(company_ctc.index, company_ctc.values, color=colors, edgecolor='black')
        ax3.set_xlabel('Average CTC (LPA)', fontsize=11)
        ax3.set_title('Average CTC by Company Type', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # 4. CGPA vs CTC
        ax4 = plt.subplot(2, 3, 4)
        scatter = ax4.scatter(test_df['final_cgpa'], y_true_arr, 
                            c=y_pred_arr, cmap='viridis', alpha=0.6, 
                            edgecolors='black', linewidth=0.5)
        plt.colorbar(scatter, ax=ax4, label='Predicted CTC (LPA)')
        ax4.set_xlabel('Final CGPA', fontsize=11)
        ax4.set_ylabel('Actual CTC (LPA)', fontsize=11)
        ax4.set_title('CGPA vs CTC', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # 5. Skill Match Score vs CTC
        ax5 = plt.subplot(2, 3, 5)
        scatter = ax5.scatter(test_df['skill_match_score'], y_true_arr,
                            c=y_pred_arr, cmap='plasma', alpha=0.6,
                            edgecolors='black', linewidth=0.5)
        plt.colorbar(scatter, ax=ax5, label='Predicted CTC (LPA)')
        ax5.set_xlabel('Skill Match Score', fontsize=11)
        ax5.set_ylabel('Actual CTC (LPA)', fontsize=11)
        ax5.set_title('Skill Match vs CTC', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        
        # 6. Feature Importance
        ax6 = plt.subplot(2, 3, 6)
        if self.skill_importance:
            sorted_importance = sorted(self.skill_importance.items(), 
                                      key=lambda x: x[1], reverse=True)[:10]
            features, importances = zip(*sorted_importance)
            colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(features)))
            ax6.barh(range(len(features)), importances, color=colors, edgecolor='black')
            ax6.set_yticks(range(len(features)))
            ax6.set_yticklabels(features, fontsize=9)
            ax6.set_xlabel('Importance', fontsize=11)
            ax6.set_title('Top 10 Feature Importance', fontsize=12, fontweight='bold')
            ax6.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig('ctc_prediction_analysis.png', dpi=300, bbox_inches='tight')
        print(f"\n✓ CTC visualization saved as 'ctc_prediction_analysis.png'")
        plt.close()
    
    def export_results(self, placement_df, predictions_df, filename='phase2_ctc_predictions.csv'):
        """Export CTC predictions and analysis"""
        print(f"\n{'='*70}")
        print("EXPORTING PHASE 2 RESULTS")
        print(f"{'='*70}\n")
        
        # Combine results
        results_df = placement_df.copy()
        results_df['predicted_ctc_lpa'] = predictions_df
        results_df['prediction_error'] = results_df['ctc_lpa'] - results_df['predicted_ctc_lpa']
        results_df['prediction_error_percentage'] = (results_df['prediction_error'] / results_df['ctc_lpa']) * 100
        
        # Export to CSV
        results_df.to_csv(filename, index=False)
        
        print(f"✓ Results exported to '{filename}'")
        print(f"  Total records: {len(results_df)}")
        print(f"  Average actual CTC: ₹{results_df['ctc_lpa'].mean():.2f} LPA")
        print(f"  Average predicted CTC: ₹{results_df['predicted_ctc_lpa'].mean():.2f} LPA")
        print(f"  Average prediction error: ₹{abs(results_df['prediction_error']).mean():.2f} LPA")
        
        return results_df


def run_phase2_complete_pipeline():
    """Run complete Phase 2 pipeline"""
    print("\n" + "="*70)
    print("PHASE 2: CTC (SALARY) PREDICTION SYSTEM")
    print("Predicting Student Placement Outcomes")
    print("="*70)
    
    # Initialize system
    ctc_system = CTCPredictionSystem()
    
    # Step 1: Load Phase 1 data
    print("\n" + "="*70)
    print("STEP 1: LOADING PHASE 1 DATA")
    print("="*70)
    phase1_df = ctc_system.load_phase1_data()
    
    # Step 2: Aggregate student performance
    print("\n" + "="*70)
    print("STEP 2: AGGREGATING STUDENT PERFORMANCE")
    print("="*70)
    student_performance_df = ctc_system.aggregate_student_performance(phase1_df)
    
    # Step 3: Generate student skills data
    print("\n" + "="*70)
    print("STEP 3: GENERATING STUDENT SKILLS DATA")
    print("="*70)
    student_skills_df = ctc_system.generate_student_skills_data(student_performance_df)
    
    # Step 4: Generate employer data
    print("\n" + "="*70)
    print("STEP 4: GENERATING EMPLOYER DATA")
    print("="*70)
    employer_df = ctc_system.generate_employer_data(n_companies=50)
    
    # Export employer data
    employer_df.to_csv('employer_requirements.csv', index=False)
    print("✓ Employer data exported to 'employer_requirements.csv'")
    
    # Step 5: Create placement dataset
    print("\n" + "="*70)
    print("STEP 5: CREATING PLACEMENT DATASET")
    print("="*70)
    placement_df = ctc_system.create_placement_dataset(
        student_performance_df, student_skills_df, employer_df
    )
    
    # Step 6: Prepare features
    print("\n" + "="*70)
    print("STEP 6: PREPARING FEATURES FOR CTC PREDICTION")
    print("="*70)
    X, y, feature_columns, placement_df_full = ctc_system.prepare_features_for_ctc_prediction(placement_df)
    
    # Step 7: Split data
    print("\n" + "="*70)
    print("STEP 7: SPLITTING DATA FOR TRAINING AND TESTING")
    print("="*70)
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, placement_df_full.index, test_size=0.2, random_state=42
    )
    print(f"✓ Training samples: {len(X_train)}")
    print(f"✓ Test samples: {len(X_test)}")
    
    # Step 8: Train models
    print("\n" + "="*70)
    print("STEP 8: TRAINING CTC PREDICTION MODELS")
    print("="*70)
    model_results, best_model = ctc_system.train_ctc_models(X_train, y_train)
    
    # Step 9: Make predictions
    print("\n" + "="*70)
    print("STEP 9: MAKING CTC PREDICTIONS")
    print("="*70)
    predictions = ctc_system.predict_ctc(X_test)
    print(f"✓ Predictions made for {len(predictions)} students")
    
    # Step 10: Evaluate and report
    print("\n" + "="*70)
    print("STEP 10: EVALUATING PREDICTIONS")
    print("="*70)
    test_df = placement_df_full.loc[idx_test]
    metrics = ctc_system.generate_ctc_report(y_test, predictions, test_df)
    
    # Step 11: Visualize results
    print("\n" + "="*70)
    print("STEP 11: CREATING VISUALIZATIONS")
    print("="*70)
    ctc_system.visualize_ctc_results(y_test, predictions, test_df, feature_columns)
    
    # Step 12: Export results
    print("\n" + "="*70)
    print("STEP 12: EXPORTING RESULTS")
    print("="*70)
    
    # Create full predictions for all data
    all_predictions = ctc_system.predict_ctc(X)
    results_df = ctc_system.export_results(placement_df_full, all_predictions)
    
    # Export additional datasets
    student_performance_df.to_csv('student_final_performance.csv', index=False)
    print("✓ Student performance exported to 'student_final_performance.csv'")
    
    student_skills_df.to_csv('student_skills_profile.csv', index=False)
    print("✓ Student skills exported to 'student_skills_profile.csv'")
    
    # Generate correlation analysis
    print("\n" + "="*70)
    print("CORRELATION ANALYSIS: KEY FACTORS AFFECTING CTC")
    print("="*70)
    
    correlation_features = [
        'final_cgpa', 'programming_skills', 'data_analysis_skills',
        'communication', 'num_internships', 'num_projects', 
        'num_certifications', 'skill_match_score'
    ]
    
    correlations = []
    for feature in correlation_features:
        if feature in placement_df_full.columns:
            corr = placement_df_full[feature].corr(placement_df_full['ctc_lpa'])
            correlations.append({'Feature': feature, 'Correlation': corr})
    
    corr_df = pd.DataFrame(correlations).sort_values('Correlation', ascending=False)
    print("\nFeature Correlations with CTC:")
    for _, row in corr_df.iterrows():
        print(f"  {row['Feature']}: {row['Correlation']:.4f}")
    
    print("\n" + "="*70)
    print("✅ PHASE 2 COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📁 Generated Files:")
    print("  1. ctc_prediction_analysis.png - Comprehensive visualizations")
    print("  2. phase2_ctc_predictions.csv - All CTC predictions")
    print("  3. employer_requirements.csv - Employer data")
    print("  4. student_final_performance.csv - Aggregated performance")
    print("  5. student_skills_profile.csv - Student skills data")
    print("\n🎯 Key Insights:")
    print(f"  • Model R² Score: {metrics['r2']:.4f}")
    print(f"  • Average Prediction Error: ₹{metrics['mae']:.2f} LPA")
    print(f"  • CTC Range: ₹{placement_df_full['ctc_lpa'].min():.2f} - ₹{placement_df_full['ctc_lpa'].max():.2f} LPA")
    print(f"  • Students Analyzed: {len(placement_df_full)}")
    print("\n" + "="*70 + "\n")
    
    return ctc_system, results_df, metrics


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        # Run complete Phase 2 pipeline
        ctc_system, results_df, metrics = run_phase2_complete_pipeline()
        
        print("\n" + "="*70)
        print("🎓 PHASE 2 EXECUTION COMPLETED!")
        print("="*70)
        print("\n📊 Summary:")
        print(f"  ✓ CTC predictions generated for all students")
        print(f"  ✓ Model accuracy: R² = {metrics['r2']:.4f}")
        print(f"  ✓ Average prediction error: ₹{metrics['mae']:.2f} LPA")
        print(f"  ✓ All visualizations and reports generated")
        print(f"  ✓ Data exported for further analysis")
        print("\n🎯 Next Steps:")
        print("  1. Review ctc_prediction_analysis.png")
        print("  2. Analyze phase2_ctc_predictions.csv")
        print("  3. Use insights for placement strategy")
        print("  4. Provide feedback to students")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("  1. Make sure Phase 1 has run successfully")
        print("  2. Check if phase1_complete_data.csv exists")
        print("  3. Verify all required libraries are installed")
        print("  4. If issue persists, the system will use sample data")