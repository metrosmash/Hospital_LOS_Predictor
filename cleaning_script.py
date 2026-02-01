import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


drop_list = ["Hospital Service Area","Operating Certificate Number","Permanent Facility Id","Zip Code - 3 digits",
             "Discharge Year","CCS Diagnosis Code","CCS Diagnosis Description","CCS Procedure Code",
             "CCS Procedure Description","APR Severity of Illness Description","APR DRG Code","Payment Typology 2",
             "Payment Typology 3","Birth Weight","Length of Stay",
             "APR DRG Description","APR MDC Description","APR Risk of Mortality","Abortion Edit Indicator","Total Costs","Total Charges"]

cat_cols = ["Hospital County","Facility Name","Age Group","Gender","Race","Ethnicity","Type of Admission","Patient Disposition","Payment Typology 1"]
num_cols = ["APR MDC Code","APR Severity of Illness Code"]


## load pipeline 
class HospitalDataCleaner(BaseEstimator, TransformerMixin):
    """
    This class creates a pipeline that cleans and encodes the data for the
    hospital prediction app.
    Params: BaseEstimator, TransformerMixin
    """

    def __init__(self, drop_list=None, cat_cols=None, num_cols=None, 
                 return_dataframe=True):

        self.drop_list = drop_list
        self.cat_cols = cat_cols
        self.num_cols = num_cols
        self.return_dataframe = return_dataframe
        
        self.mdc_mapping = None
        self.severity_mapping = None
        self.encoder = None
        self.feature_names = None
    
    def fit(self, X, y=None):
        df = X.copy()
        
        # Convert LOS if present
        if "Length of Stay" in df.columns:
            df["Length of Stay"] = df["Length of Stay"].replace("120 +", 120).astype(int)
        

        # Remove unknown gender (only during training)
        df = df[df["Gender"] != "U"]
        
        # Target encoding mappings
        if "Length of Stay" in df.columns:
            self.mdc_mapping = df.groupby("APR MDC Code")["Length of Stay"].median()
            self.severity_mapping = df.groupby("APR Severity of Illness Code")["Length of Stay"].median()
        
        # Apply mappings
        df["LOS_per_MDC"] = df["APR MDC Code"].map(self.mdc_mapping)
        df["LOS_per_severity"] = df["APR Severity of Illness Code"].map(self.severity_mapping)
        
        # Drop irrelevant columns
        if self.drop_list:
            df = df.drop(columns=self.drop_list, errors="ignore")
        
        # Build ColumnTransformer
        self.encoder = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.cat_cols),
                ("num", "passthrough", self.num_cols)
            ]
        )
        
        # Fit encoder
        self.encoder.fit(df)
        
        # Store feature names for DataFrame output
        if self.return_dataframe:
            cat_features = self.encoder.named_transformers_['cat'].get_feature_names_out(self.cat_cols)
            self.feature_names = list(cat_features) + self.num_cols
        
        return self
    

    def transform(self, X):
        df = X.copy()
        
        # Convert LOS if present
        if "Length of Stay" in df.columns:
            df["Length of Stay"] = df["Length of Stay"].replace("120 +", 120).astype(int)
        
        # Apply mappings (handle unseen codes)
        df["LOS_per_MDC"] = df["APR MDC Code"].map(self.mdc_mapping).fillna(
            self.mdc_mapping.median() if self.mdc_mapping is not None else 0
        )
        df["LOS_per_severity"] = df["APR Severity of Illness Code"].map(self.severity_mapping).fillna(
            self.severity_mapping.median() if self.severity_mapping is not None else 0
        )
        

        # Drop irrelevant columns
        if self.drop_list:
            df = df.drop(columns=self.drop_list, errors="ignore")
        print(df.info())
        # Transform using trained encoder
        X_encoded = self.encoder.transform(df)
        
        # Return as DataFrame if requested
        if self.return_dataframe:
            return pd.DataFrame(X_encoded, columns=self.feature_names, index=df.index)
        
        return X_encoded



mdc_code_mapping = {
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
'Multiple Significant Trauma': 25 }