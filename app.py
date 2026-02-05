"""
Hospital LOS Prediction Flask API
Handles feature engineering from 13 input columns to 312 encoded features
"""

from flask import Flask, request, jsonify
from flask import render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import logging
from datetime import datetime
import traceback
import xgboost 
import os 

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from cleaning_script import HospitalDataCleaner ,mdc_code_mapping


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



# ============================================
# LOAD MODEL AND PREPROCESSORS
# ============================================

try:
    # Load your trained model
    model = joblib.load('assets/pkl_files/xgb_modelv1.pkl')
    logger.info("✓ Model loaded successfully")

    xgb_hospital_pipeline = joblib.load('assets/pkl_files/xgb_hospital_full_pipeline.pkl')
    logger.info("✓ Model-cleaner pipeline loaded successfully")
    
    # Load column names and order
    column_names = joblib.load('assets/pkl_files/feature_names.pkl')
    logger.info(f"✓ Column names loaded: {len(column_names)} columns expected")
    
    # Load mapping files
    mdc_mapping = joblib.load('assets/pkl_files/mdc_mapping.pkl')
    logger.info(f"✓ MDC mapping loaded: {len(mdc_mapping)} mappings")
    
    severity_mapping = joblib.load('assets/pkl_files/severity_mapping.pkl')
    logger.info(f"✓ Severity mapping loaded: {len(severity_mapping)} mappings")

    mdc_conversion_mapping = joblib.load('assets/pkl_files/mdc_conversion_mapping.pkl')
    logger.info(f"✓ mdc conversion mapping  loaded: {len(mdc_conversion_mapping)} mappings")

    cleaning_pipeline = joblib.load('assets/pkl_files/hospital_data_cleanerv1.pkl')
    logger.info(f"✓ Cleaning pipeline  loaded ")
    
    MODEL_LOADED = True
    
except FileNotFoundError as e:
    logger.error(f"✗ Failed to load model files: {e}")
    logger.error("Make sure these files are in the assets/pkl_files:")
    logger.error("  - xgb_hospital_predict.pkl")
    logger.error("  - feature_names.pkl")
    logger.error("  - mdc_mapping.pkl")
    logger.error("  - severity_mapping.pkl")
    MODEL_LOADED = False
    model = None
    column_names = None
    mdc_mapping = None
    severity_mapping = None

# ============================================
# FEATURE ENGINEERING FUNCTIONS
# ============================================



def prepare_input_dataframe(data):
    """
    Convert frontend payload to initial DataFrame with 13 columns
    
    Args:
        data: Dict from frontend with dataset column names
    
    Returns:
        pandas DataFrame with 13 input columns
    """
    # using dictionary to map the MDC Description to Code
    ## Loading the user selected MDC Description
    mdc_key = data.get('APR MDC Description', '')
    ## using the MDC Description as the key to get the MDC Code
    mdc_value = mdc_code_mapping[mdc_key]
    logger.info(f"This is the APR MDC Code: {mdc_value} while this is the APR MDC Description: {mdc_key}")
    # Extract the 13 input features in correct order
    input_data = {
        'Hospital County': data.get('Hospital County', ''),
        'Facility Name': data.get('Facility Name', ''),
        'Age Group': data.get('Age Group', ''),
        'Gender': data.get('Gender', ''),
        'Race': data.get('Race', ''),
        'Ethnicity': data.get('Ethnicity', ''),
        'Type of Admission': data.get('Type of Admission', ''),
        'Patient Disposition': data.get('Patient Disposition', ''),
        'APR MDC Code': mdc_value,
        'APR MDC Description': data.get('APR MDC Description', ''),
        'APR Severity of Illness Code': data.get('APR Severity of Illness Code', 0),
        'APR Medical Surgical Description': data.get('APR Medical Surgical Description', ''),
        'Payment Typology 1': data.get('Payment Typology 1', ''),
        'Emergency Department Indicator': data.get('Emergency Department Indicator', '')
    }
    
    # Create DataFrame
    df = pd.DataFrame([input_data])
    
    logger.info(f"Created input DataFrame with shape: {df.shape}")
    logger.info(f"Input columns: {df.columns.tolist()}")
    
    return df

def encode_features(df):
    """
    Transform 13 input columns into 312 encoded features
    
    This function should match your training preprocessing exactly:
    - One-hot encoding for categorical variables
    - Any feature engineering you did during training
    
    Args:
        df: DataFrame with 13 input columns
    
    Returns:
        DataFrame with 312 encoded columns matching column_names.pkl
    """
    
    logger.info("Starting feature encoding...")
    logger.info(f"{df.columns}")
    
    # Apply MDC mapping if needed
    # if 'APR MDC Code' in df.columns and mdc_conversion_mapping:
    if 'APR MDC Code' in df.columns and mdc_conversion_mapping is not None:
        mdc_conversion_mapping1 = mdc_conversion_mapping.set_index("APR MDC Description")["APR MDC Code"].to_dict()
        df['APR MDC Code'] = df['APR MDC Description'].map(mdc_conversion_mapping1)
        logger.info(f"Mapped MDC Description to Code: {df['APR MDC Code'].iloc[0]}")

    if 'APR MDC Code' in df.columns and mdc_conversion_mapping is not None:
        df["LOS_per_MDC"] = df["APR MDC Code"].map(mdc_mapping)
        logger.info(f"Mapped feature Engineering LOS_per_MDC")
    
    # Apply severity mapping if needed
    if 'APR Severity of Illness Code' in df.columns and severity_mapping is not None:
        # If your severity_mapping transforms the codes
        df["LOS_per_severity"] = df["APR Severity of Illness Code"].map(severity_mapping)
        logger.info(f"Mapped feature Engineering LOS_per_severity")

        logger.info(f" After feature engineering: {df.columns }")
    
    # Get categorical columns (exclude numeric ones)
    categorical_columns = [
        'Hospital County',
        'Facility Name',
        'Age Group',
        'Gender',
        'Race',
        'Ethnicity',
        'Type of Admission',
        'Patient Disposition',
        'APR MDC Description',
        'APR Medical Surgical Description',
        'Payment Typology 1',
        'Emergency Department Indicator'
    ]
    

    logger.info(f"{'+'*5} Dropping irrelevant columns (with respect to my prediction app)  {'+' * 5} ")
    # please modify the drop_list as much as needed 

    df_drop_irrelevant = df.drop(columns = ['APR MDC Description']).copy()

    # One-hot encode categorical variables
    # This should match your training preprocessing

    df_encoded = pd.get_dummies(df_drop_irrelevant).copy()
    
    logger.info(f"After encoding: {df_encoded.shape[1]} columns")
    logger.info(f"feature names after encoding :{df_encoded.columns}")
    
    # Align with training columns (312 columns)
    # Add missing columns with 0s
    missing_cols = set(column_names) - set(df_encoded.columns)
    for col in missing_cols:
        df_encoded[col] = 0
    
    # Remove extra columns not in training
    extra_cols = set(df_encoded.columns) - set(column_names)
    df_encoded = df_encoded.drop(columns=extra_cols)
    
    # Reorder columns to match training order
    df_encoded = df_encoded[column_names]
    
    logger.info(f"Final encoded shape: {df_encoded.shape}")
    logger.info(f"Matches expected columns: {df_encoded.shape[1] == len(column_names)}")
    
    return df_encoded


# ============================================
# RISK FACTOR IDENTIFICATION
# ============================================

def identify_risk_factors(input_data, predicted_los):
    """
    Identify clinical factors contributing to predicted LOS
    Based on domain knowledge and input features
    """
    
    factors = []
    
    # Severity-based factors
    severity = input_data.get('APR Severity of Illness Code', 0)
    if severity >= 3:
        factors.append({
            'factor': 'High Clinical Severity',
            'description': f'Severity level {severity} indicates complex medical needs',
            'impact': 'high',
            'impact_days': '+2-4 days'
        })
    
    # Age-based factors
    age_group = input_data.get('Age Group', '')
    if age_group == '70+':
        factors.append({
            'factor': 'Advanced Age',
            'description': 'Patients 70+ typically require longer recovery periods',
            'impact': 'medium',
            'impact_days': '+1-2 days'
        })
    elif age_group == '50-69':
        factors.append({
            'factor': 'Older Adult',
            'description': 'Age may contribute to extended recovery time',
            'impact': 'low',
            'impact_days': '+0.5-1 day'
        })
    
    # Admission type factors
    admission_type = input_data.get('Type of Admission', '')
    if admission_type == 'Emergency':
        factors.append({
            'factor': 'Emergency Admission',
            'description': 'Unplanned admissions often involve more complex conditions',
            'impact': 'medium',
            'impact_days': '+1-3 days'
        })
    elif admission_type == 'Trauma':
        factors.append({
            'factor': 'Trauma Case',
            'description': 'Traumatic injuries typically require intensive care',
            'impact': 'high',
            'impact_days': '+3-5 days'
        })
    
    # Surgical vs Medical
    med_surg = input_data.get('APR Medical Surgical Description', '')
    if med_surg == 'Surgical':
        factors.append({
            'factor': 'Surgical Procedure',
            'description': 'Post-operative care and recovery time needed',
            'impact': 'medium',
            'impact_days': '+2-3 days'
        })
    
    # Emergency Department indicator
    if input_data.get('Emergency Department Indicator') == 'Y':
        factors.append({
            'factor': 'Emergency Department Admission',
            'description': 'Initial ED evaluation may indicate urgent condition',
            'impact': 'low',
            'impact_days': '+0.5-1 day'
        })
    
    # Diagnosis-specific factors
    diagnosis = input_data.get('APR MDC Description', '')
    high_los_diagnoses = {
        'Multiple Significant Trauma': ('high', '+4-7 days'),
        'Burns': ('high', '+5-10 days'),
        'Mental Diseases and Disorders': ('medium', '+2-4 days'),
        'Newborns and Other Neonates with Conditions Originating in the Perinatal Period': ('medium', '+3-5 days'),
        'Diseases and Disorders of the Circulatory System': ('medium', '+1-3 days'),
        'Diseases and Disorders of the Respiratory System': ('medium', '+1-2 days')
    }
    
    if diagnosis in high_los_diagnoses:
        impact, days = high_los_diagnoses[diagnosis]
        factors.append({
            'factor': 'Complex Diagnosis',
            'description': f'{diagnosis.split(" and ")[0]} typically requires extended care',
            'impact': impact,
            'impact_days': days
        })
    
    # Insurance/Payment factors (social determinant)
    payment = input_data.get('Payment Typology 1', '')
    if payment in ['Self-Pay', 'Unknown']:
        factors.append({
            'factor': 'Insurance Coverage',
            'description': 'Insurance status may affect discharge planning',
            'impact': 'low',
            'impact_days': '+0.5-1 day'
        })
    elif payment == 'Medicaid':
        factors.append({
            'factor': 'Medicaid Coverage',
            'description': 'May require additional discharge planning resources',
            'impact': 'low',
            'impact_days': '+0.5 day'
        })
    
    # Patient disposition planning
    disposition = input_data.get('Patient Disposition', '')
    if disposition in ['Skilled Nursing Home', 'Inpatient Rehabilitation Facility']:
        factors.append({
            'factor': 'Post-Acute Care Planning',
            'description': f'Discharge to {disposition} requires coordination',
            'impact': 'medium',
            'impact_days': '+1-2 days'
        })
    
    # If no specific risk factors, note routine case
    if len(factors) == 0:
        factors.append({
            'factor': 'Routine Admission',
            'description': 'No major clinical complexity indicators identified',
            'impact': 'none',
            'impact_days': 'Standard LOS expected'
        })
    
    return factors

# ============================================
# PREDICTION ENDPOINT
# ============================================

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    
    Expected input: 13 feature columns from frontend
    Output: Predicted LOS with confidence interval and risk factors
    """
    
    if not MODEL_LOADED:
        return jsonify({
            'error': 'Model not loaded',
            'message': 'Server configuration error. Please contact administrator.'
        }), 500
    
    try:
        # Get input data
        data = request.json
        logger.info(f"Received prediction request: {data.get('hospital_name', 'Unknown')}")
        
        # Validate required fields
        required_fields = [
            'Hospital County','Facility Name','Age Group', 'Gender', 'Race', 'Ethnicity',
            'Type of Admission', 'Patient Disposition',
            'APR MDC Description', 'APR Severity of Illness Code',
            'APR Medical Surgical Description', 'Payment Typology 1',
            'Emergency Department Indicator'
        ]
        
        missing = [f for f in required_fields if f not in data or data[f] == '']
        if missing:
            logger.warning(f"Missing required fields: {missing}")
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing
            }), 400
        
        # Step 1: Create initial DataFrame (13 columns)
        df_input = prepare_input_dataframe(data)
        
        # Step 2: Make prediction
        #predicted_los = model.predict(df_encoded)[0]
        predicted_los = xgb_hospital_pipeline.predict(df_input)
        predicted_los_ = predicted_los[0].astype(float)
        
        logger.info(f"Prediction: {predicted_los_.round(2)} days")
        
        # Step 4: Calculate confidence interval
        # If your model supports prediction intervals (e.g., Quantile Regression)
        # use that. Otherwise, use a simple approach:
        std_error = predicted_los_ * 0.15  # 15% standard error (adjust based on your model's performance)
        confidence_low = max(1.0, predicted_los_ - 1.96 * std_error)  # 95% CI
        confidence_high = predicted_los_ + 1.96 * std_error
        
        # Step 5: Identify risk factors
        risk_factors = identify_risk_factors(data, predicted_los_)
        
        # Step 6: Prepare response
        response = {
            'predicted_los': predicted_los_.round(2),
            'confidence_interval': [
                confidence_low.round(1).astype(float),
                confidence_high.round(1).astype(float)
            ],
            'risk_factors': risk_factors,
            'metadata': {
                'model_version': '1.0.0',
                'prediction_timestamp': datetime.now().isoformat(),
                'hospital_id': data.get('hospital_id'),
                'hospital_name': data.get('hospital_name'),
                'input_features': 13,
                #'encoded_features': df_encoded.shape[1]
            }
        }
        
        # Log prediction for monitoring
        log_prediction(data, predicted_los)
        logger.info(f"predicted value right now")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e),
            'details': traceback.format_exc() if app.debug else None
        }), 500

@app.route('/debug', methods=['GET'])
def debug():
    try:
        # If using separate model
        expected_features = model.get_booster().feature_names
        
        
        return jsonify({
            'expected_features': expected_features,
            'num_features': len(expected_features),
            
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# ============================================
# HELPER ENDPOINTS
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API and model are ready"""
    
    return jsonify({
        'status': 'healthy' if MODEL_LOADED else 'degraded',
        'model_loaded': MODEL_LOADED,
        'expected_features': len(column_names) if column_names else None,
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Return information about the model"""
    
    if not MODEL_LOADED:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'input_features': 13,
        'encoded_features': len(column_names),
        'model_type': type(model).__name__,
        'feature_columns': column_names[:15] + ['...'] if len(column_names) > 15 else column_names,
        #'mdc_mappings': len(mdc_mapping) if mdc_mapping else 0,
        #'severity_mappings': len(severity_mapping) if severity_mapping else 0
    })

@app.route('/api/feature-info', methods=['POST'])
def feature_info():
    """
    Debug endpoint: Show how input features are encoded
    Useful for validating preprocessing pipeline
    """
    
    try:
        data = request.json
        
        # Create input DataFrame
        df_input = prepare_input_dataframe(data)
        
        # Encode features
        df_encoded = encode_features(df_input)
        
        # Get non-zero features (more interpretable)
        non_zero_features = df_encoded.loc[0, df_encoded.loc[0] != 0].to_dict()
        
        return jsonify({
            'input_shape': df_input.shape,
            'encoded_shape': df_encoded.shape,
            'non_zero_features': len(non_zero_features),
            'sample_features': dict(list(non_zero_features.items())[:20]),  # First 20
            'all_features_present': df_encoded.shape[1] == len(column_names)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# LOGGING AND MONITORING
# ============================================

def log_prediction(input_data, prediction):
    """
    Log predictions for monitoring and model improvement
    In production, save to database
    """
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'hospital_id': input_data.get('hospital_id'),
        'hospital_name': input_data.get('hospital_name'),
        'county': input_data.get('Hospital County'),
        'predicted_los': prediction.round(2),
        'severity': input_data.get('APR Severity of Illness Code'),
        'age_group': input_data.get('Age Group'),
        'diagnosis': input_data.get('APR MDC Description'),
        'admission_type': input_data.get('Type of Admission')
    }
    
    logger.info(f"PREDICTION_LOG: {log_entry}")
    
    # TODO: In production, save to database
    # db.predictions.insert_one(log_entry)



# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# SERVE FRONTEND PAGES
# ============================================


@app.route('/')
def home():
    """Serve the main county selection page"""
    return render_template("index.html")

@app.route('/page/<page_name>')
def page(page_name):
    """Serve other HTML pages dynamically"""
    # Security: whitelist allowed pages
    allowed_pages = ['county_map', 'prediction_form', 'prediction_result']
    
    if page_name in allowed_pages:
        return render_template(f"{page_name}.html")
    else:
        return "Page not found", 404

# # Serve static assets (GeoJSON, CSS, JS)
# @app.route('/assets/<path:filename>')
# def serve_assets(filename):
#     """Serve files from assets directory"""
#     return send_from_directory('assets', filename)

# ============================================
# SERVE STATIC ASSETS (CSS, JS, DATA)
# ============================================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from assets directory"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    return send_from_directory(assets_dir, filename)




# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Hospital LOS Prediction API Starting...")
    logger.info("=" * 50)
    
    if MODEL_LOADED:
        logger.info("✓ All models and mappings loaded successfully")
        logger.info(f"✓ Ready to predict with {len(column_names)} features")
    else:
        logger.warning("✗ Model loading failed - API will return errors")
    
    # Development server
    # app.run(
    #     debug=True,
    #     host='0.0.0.0',
    #     port=5000
    # )
    
    # Production: Use gunicorn
    gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

    