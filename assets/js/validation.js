/**
 * FORM VALIDATION
 * Client-side validation for prediction form
 * Updated to match actual dataset columns
 */

const Validator = {
    
    /**
     * Validation rules for each field
     */
    rules: {
        // Demographics
        age_group: {
            required: true,
            values: ['0 to 17', '18 to 29', '30 to 49', '50 to 69', '70 or Older']
        },
        gender: {
            required: true,
            values: ['M', 'F']
        },
        race: {
            required: true,
            values: [
                'Black/African American',
                'Multi-racial',
                'White',
                'Other Race'
            ]
        },
        ethnicity: {
            required: true,
            values: [
                'Multi-ethnic',
                'Spanish/Hispanic',
                'Not Span/Hispanic',
                'Unknown'
            ]
        },
        insurance_type: {
            required: true,  // Changed from false to true
            values: [
                'Medicare',
                'Medicaid',
                'Private Health Insurance',
                'Self-Pay',
                'Blue Cross/Blue Shield',
                'Department of Corrections',
                'Federal/State/Local/VA',
                'Managed Care, Unspecified',
                'Miscellaneous/Other',
                'Unknown'
            ]
        },
        
        // Clinical Information
        admission_type: {
            required: true,
            values: ['Emergency', 'Urgent', 'Elective', 'Newborn', 'Trauma', 'Not Available']
        },
        patient_disposition: {
            required: true,
            values: [
                'Admitted from Ambulatory Surgery',
                'Another Type Not Listed',
                'Cancer Center or Children\'s Hospital',
                'Court/Law Enforcement',
                'Critical Access Hospital',
                'Expired',
                'Facility w/ Custodial/Supportive Care',
                'Federal Health Care Facility',
                'Home or Self Care',
                'Home w/ Home Health Services',
                'Hosp Basd Medicare Approved Swing Bed',
                'Hospice - Home',
                'Hospice - Medical Facility',
                'Inpatient Rehabilitation Facility',
                'Left Against Medical Advice',
                'Medicaid Cert Nursing Facility',
                'Medicare Cert Long Term Care Hospital',
                'Psychiatric Hospital or Unit of Hosp',
                'Short-term Hospital',
                'Skilled Nursing Home'
            ]
        },
        diagnosis_group: {
            required: true,
            values: [
                'Pre-MDC or Ungroupable',
                'Human Immunodeficiency Virus Infections',
                'Diseases and Disorders of the Circulatory System',
                'Pregnancy, Childbirth and the Puerperium',
                'Newborns and Other Neonates with Conditions Originating in the Perinatal Period',
                'Diseases and Disorders of the Musculoskeletal System and Conn Tissue',
                'Diseases and Disorders of the Respiratory System',
                'Diseases and Disorders of the Digestive System',
                'Diseases and Disorders of the Nervous System',
                'Infectious and Parasitic Diseases, Systemic or Unspecified Sites',
                'Diseases and Disorders of the Kidney and Urinary Tract',
                'Mental Diseases and Disorders',
                'Endocrine, Nutritional and Metabolic Diseases and Disorders',
                'Alcohol/Drug Use and Alcohol/Drug Induced Organic Mental Disorders',
                'Diseases and Disorders of the Hepatobiliary System and Pancreas',
                'Diseases and Disorders of the Skin, Subcutaneous Tissue and Breast',
                'Diseases and Disorders of Blood, Blood Forming Organs and Immunological Disorders',
                'Ear, Nose, Mouth, Throat and Craniofacial Diseases and Disorders',
                'Rehabilitation, Aftercare, Other Factors Influencing Health Status and Other Health Service Contacts',
                'Poisonings, Toxic Effects, Other Injuries and Other Complications of Treatment',
                'Diseases and Disorders of the Female Reproductive System',
                'Lymphatic, Hematopoietic, Other Malignancies, Chemotherapy and Radiotherapy',
                'Diseases and Disorders of the Male Reproductive System',
                'Multiple Significant Trauma',
                'Diseases and Disorders of the Eye',
                'Burns'
            ]
        },
        'medical/surgical': {
            required: true,
            values: ['Medical', 'Surgical']
        },
        is_emergency: {
            required: true,
            values: ['Y', 'N']
        },
        severity: {
            required: true,
            values: ['1', '2', '3', '4']
        },
        
        // Optional fields
        comorbidity_count: {
            required: false,
            type: 'number',
            min: 0,
            max: 10
        },
        prior_admissions: {
            required: false,
            type: 'number',
            min: 0,
            max: 50
        }
    },
    
    /**
     * Validate single field
     * @param {string} fieldName - Field identifier
     * @param {any} value - Field value
     * @returns {Object} { valid: boolean, error: string }
     */
    validateField(fieldName, value) {
        const rule = this.rules[fieldName];
        
        if (!rule) {
            return { valid: true, error: null };
        }
        
        // Required check
        if (rule.required && (!value || value === '')) {
            return {
                valid: false,
                error: 'This field is required'
            };
        }
        
        // If not required and empty, skip other checks
        if (!rule.required && (!value || value === '')) {
            return { valid: true, error: null };
        }
        
        // Enum validation
        if (rule.values && !rule.values.includes(value)) {
            return {
                valid: false,
                error: `Invalid selection. Please choose from the dropdown.`
            };
        }
        
        // Number validation
        if (rule.type === 'number') {
            const num = parseFloat(value);
            
            if (isNaN(num)) {
                return {
                    valid: false,
                    error: 'Must be a valid number'
                };
            }
            
            if (rule.min !== undefined && num < rule.min) {
                return {
                    valid: false,
                    error: `Must be at least ${rule.min}`
                };
            }
            
            if (rule.max !== undefined && num > rule.max) {
                return {
                    valid: false,
                    error: `Must be at most ${rule.max}`
                };
            }
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate entire form
     * @param {Object} formData - Key-value pairs from form
     * @returns {Object} { valid: boolean, errors: Object }
     */
    validateForm(formData) {
        const errors = {};
        let isValid = true;
        
        // Validate each field that has a rule
        Object.keys(this.rules).forEach(fieldName => {
            const value = formData[fieldName];
            const result = this.validateField(fieldName, value);
            
            if (!result.valid) {
                errors[fieldName] = result.error;
                isValid = false;
            }
        });
        
        return { valid: isValid, errors };
    },
    
    /**
     * Show validation error on field
     * @param {string} fieldId - Input element ID
     * @param {string} errorMessage - Error text
     */
    showFieldError(fieldId, errorMessage) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        // Add error class
        field.classList.add('error');
        
        // Remove existing error message
        const existingError = field.parentElement.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = errorMessage;
        field.parentElement.appendChild(errorDiv);
    },
    
    /**
     * Clear validation error from field
     * @param {string} fieldId - Input element ID
     */
    clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        field.classList.remove('error');
        
        const errorDiv = field.parentElement.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    },
    
    /**
     * Clear all validation errors
     */
    clearAllErrors() {
        document.querySelectorAll('.error').forEach(el => {
            el.classList.remove('error');
        });
        
        document.querySelectorAll('.form-error').forEach(el => {
            el.remove();
        });
    },
    
    /**
     * Attach real-time validation to form
     * @param {string} formId - Form element ID
     */
    attachLiveValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        // Validate on blur
        form.querySelectorAll('input, select').forEach(field => {
            field.addEventListener('blur', (e) => {
                const fieldName = e.target.name || e.target.id;
                const value = e.target.value;
                
                const result = this.validateField(fieldName, value);
                
                if (!result.valid) {
                    this.showFieldError(e.target.id, result.error);
                } else {
                    this.clearFieldError(e.target.id);
                }
            });
            
            // Clear error on focus
            field.addEventListener('focus', (e) => {
                this.clearFieldError(e.target.id);
            });
        });
    },
    
    /**
     * Get form data as object
     * @param {string} formId - Form element ID
     * @returns {Object}
     */
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};
        
        const data = {};
        const formData = new FormData(form);
        
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    },
    
    /**
     * Map form field names to dataset column names
     */
    fieldToColumnMap: {
        'age_group': 'Age Group',
        'gender': 'Gender',
        'race': 'Race',
        'ethnicity': 'Ethnicity',
        'insurance_type': 'Payment Typology 1',
        'admission_type': 'Type of Admission',
        'patient_disposition': 'Patient Disposition',
        'diagnosis_group': 'APR MDC Description',  // Maps to MDC code
        'medical/surgical': 'APR Medical Surgical Description',
        'is_emergency': 'Emergency Department Indicator',
        'severity': 'APR Severity of Illness Code'
    },
    
    /**
     * Build prediction payload with hospital context
     * Maps form fields to actual dataset column names
     * @param {Object} formData - Raw form data
     * @param {Object} context - Additional context (hospital_id, etc.)
     * @returns {Object}
     */
    buildPredictionPayload(formData, context = {}) {
        return {
            // Hospital context (metadata, not for model)
            'hospital_id': context.hospital_id,
            'hospital_name': context.hospital_name,
            'county_name': context.county_name,
            
            // Dataset column names (for model input)
            'Hospital County': context.county_name,
            'Facility Name': context.hospital_name,
            'Age Group': formData.age_group,
            'Gender': formData.gender,
            'Race': formData.race,
            'Ethnicity': formData.ethnicity,
            'Type of Admission': formData.admission_type,
            'Patient Disposition': formData.patient_disposition,
            'APR MDC Description': formData.diagnosis_group,
            'APR Severity of Illness Code': parseInt(formData.severity),
            'APR Medical Surgical Description': formData['medical/surgical'],
            'Payment Typology 1': formData.insurance_type,
            'Emergency Department Indicator': formData.is_emergency,
            
            // Optional fields (if provided)
            'comorbidity_count': formData.comorbidity_count 
                ? parseInt(formData.comorbidity_count) 
                : null,
            'prior_admissions': formData.prior_admissions
                ? parseInt(formData.prior_admissions)
                : null,
            
            // Metadata
            'timestamp': new Date().toISOString()
        };
    },
    
    /**
     * Map APR MDC Description to MDC Code
     * Based on standard APR-DRG Major Diagnostic Categories
     */
    getMDCCode(description) {
        const mdcMap = {
            'Pre-MDC or Ungroupable': 0,
            'Diseases and Disorders of the Nervous System': 1,
            'Diseases and Disorders of the Eye': 2,
            'Ear, Nose, Mouth, Throat and Craniofacial Diseases and Disorders': 3,
            'Diseases and Disorders of the Respiratory System': 4,
            'Diseases and Disorders of the Circulatory System': 5,
            'Diseases and Disorders of the Digestive System': 6,
            'Diseases and Disorders of the Hepatobiliary System and Pancreas': 7,
            'Diseases and Disorders of the Musculoskeletal System and Conn Tissue': 8,
            'Diseases and Disorders of the Skin, Subcutaneous Tissue and Breast': 9,
            'Endocrine, Nutritional and Metabolic Diseases and Disorders': 10,
            'Diseases and Disorders of the Kidney and Urinary Tract': 11,
            'Diseases and Disorders of the Male Reproductive System': 12,
            'Diseases and Disorders of the Female Reproductive System': 13,
            'Pregnancy, Childbirth and the Puerperium': 14,
            'Newborns and Other Neonates with Conditions Originating in the Perinatal Period': 15,
            'Diseases and Disorders of Blood, Blood Forming Organs and Immunological Disorders': 16,
            'Lymphatic, Hematopoietic, Other Malignancies, Chemotherapy and Radiotherapy': 17,
            'Infectious and Parasitic Diseases, Systemic or Unspecified Sites': 18,
            'Mental Diseases and Disorders': 19,
            'Alcohol/Drug Use and Alcohol/Drug Induced Organic Mental Disorders': 20,
            'Poisonings, Toxic Effects, Other Injuries and Other Complications of Treatment': 21,
            'Burns': 22,
            'Rehabilitation, Aftercare, Other Factors Influencing Health Status and Other Health Service Contacts':23,
            'Human Immunodeficiency Virus Infections': 24,
            'Multiple Significant Trauma': 25
            
        };
        
        return mdcMap[description] || null;
    }
};

// Make globally available
window.Validator = Validator;