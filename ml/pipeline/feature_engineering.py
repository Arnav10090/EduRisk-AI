"""
Feature Engineering Pipeline for EduRisk AI

This module transforms raw student data into model-ready feature vectors.
All transformations are consistent between training and inference.

Feature: edurisk-ai-placement-intelligence
Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 28
"""

from typing import Dict, List, Optional
import numpy as np
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Transforms raw student data into feature vectors for ML models.
    
    Implements feature engineering pipeline including:
    - CGPA normalization
    - Internship score calculation
    - Employer type encoding
    - Skill gap score derivation
    - EMI stress ratio calculation
    - Placement momentum calculation
    - One-hot encoding for institute tier
    - Label encoding for course type
    
    Configuration is loaded from ml/pipeline/config.json (Requirement 28).
    """
    
    # Default config path
    DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"
    
    def __init__(self, feature_config: Optional[Dict] = None, config_path: Optional[Path] = None):
        """
        Initialize FeatureEngineer with configuration from JSON file.
        
        Args:
            feature_config: Optional dictionary with runtime overrides
            config_path: Optional path to config.json file (defaults to ml/pipeline/config.json)
        
        Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6
        """
        # Load configuration from file (Requirement 28.1)
        config_file = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config(config_file)
        
        # Apply runtime overrides if provided
        if feature_config:
            self.config.update(feature_config)
        
        # Extract internship score weights (Requirement 28.2)
        internship_weights = self.config.get('internship_score_weights', {})
        self.internship_count_weight = internship_weights.get('count_weight', 0.4)
        self.internship_months_weight = internship_weights.get('months_weight', 0.3)
        self.internship_employer_weight = internship_weights.get('employer_weight', 0.3)
        self.internship_months_denominator = internship_weights.get('months_denominator', 24.0)
        
        # Extract skill gap weights (Requirement 28.2)
        skill_gap_weights = self.config.get('skill_gap_weights', {})
        self.skill_gap_cgpa_multiplier = skill_gap_weights.get('cgpa_multiplier', 5.0)
        self.skill_gap_internship_multiplier = skill_gap_weights.get('internship_multiplier', 5.0)
        
        # Extract certification cap (Requirement 28.2)
        cert_config = self.config.get('certification_cap', {})
        self.max_certifications = cert_config.get('max_certifications', 5)
        
        # Extract historical defaults (Requirement 28.2)
        historical = self.config.get('historical_defaults', {})
        self.placement_rate_3m = historical.get('placement_rate_3m', 0.45)
        self.placement_rate_6m = historical.get('placement_rate_6m', 0.65)
        self.placement_rate_12m = historical.get('placement_rate_12m', 0.80)
        self.salary_benchmark = historical.get('salary_benchmark', 5.0)
        self.job_demand_score = historical.get('job_demand_score', 5.0)
        self.region_job_density = historical.get('region_job_density', 0.5)
        self.macro_hiring_index = historical.get('macro_hiring_index', 0.6)
        
        # Extract employer type scores (Requirement 28.2)
        self.EMPLOYER_TYPE_SCORES = self.config.get('employer_type_scores', {
            'MNC': 4, 'Startup': 3, 'PSU': 2, 'NGO': 1, 'None': 0, None: 0
        })
        
        # Extract course type encoding (Requirement 28.2)
        self.COURSE_TYPE_ENCODING = self.config.get('course_type_encoding', {
            'Engineering': 0, 'MBA': 1, 'MCA': 2, 'MSc': 3, 'Other': 4
        })
        
        # Log loaded configuration (Requirement 28.6)
        logger.info(f"FeatureEngineer initialized with config from: {config_file}")
        logger.info(f"Internship weights: count={self.internship_count_weight}, "
                   f"months={self.internship_months_weight}, employer={self.internship_employer_weight}")
        logger.info(f"Skill gap multipliers: cgpa={self.skill_gap_cgpa_multiplier}, "
                   f"internship={self.skill_gap_internship_multiplier}")
        logger.info(f"Historical defaults: placement_3m={self.placement_rate_3m}, "
                   f"placement_6m={self.placement_rate_6m}, salary={self.salary_benchmark}")
    
    def _load_config(self, config_path: Path) -> Dict:
        """
        Load configuration from JSON file with fallback to defaults.
        
        Args:
            config_path: Path to config.json file
            
        Returns:
            Configuration dictionary
            
        Requirements: 28.1, 28.4, 28.5
        """
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"✅ Loaded feature engineering config from {config_path}")
                return config
            else:
                # Config file missing, use defaults (Requirement 28.4)
                logger.warning(f"⚠️ Config file not found at {config_path}, using default weights")
                return self._get_default_config()
        except json.JSONDecodeError as e:
            # Invalid JSON, use defaults (Requirement 28.4)
            logger.warning(f"⚠️ Invalid JSON in config file {config_path}: {e}, using default weights")
            return self._get_default_config()
        except Exception as e:
            # Other errors, use defaults (Requirement 28.4)
            logger.warning(f"⚠️ Error loading config from {config_path}: {e}, using default weights")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """
        Return default configuration when config.json is missing or invalid.
        
        Returns:
            Default configuration dictionary
            
        Requirement: 28.4
        """
        return {
            'internship_score_weights': {
                'count_weight': 0.4,
                'months_weight': 0.3,
                'employer_weight': 0.3,
                'months_denominator': 24.0
            },
            'skill_gap_weights': {
                'cgpa_multiplier': 5.0,
                'internship_multiplier': 5.0
            },
            'certification_cap': {
                'max_certifications': 5
            },
            'historical_defaults': {
                'placement_rate_3m': 0.45,
                'placement_rate_6m': 0.65,
                'placement_rate_12m': 0.80,
                'salary_benchmark': 5.0,
                'job_demand_score': 5.0,
                'region_job_density': 0.5,
                'macro_hiring_index': 0.6
            },
            'employer_type_scores': {
                'MNC': 4, 'Startup': 3, 'PSU': 2, 'NGO': 1, 'None': 0, None: 0
            },
            'course_type_encoding': {
                'Engineering': 0, 'MBA': 1, 'MCA': 2, 'MSc': 3, 'Other': 4
            }
        }
    
    def transform(self, student_data: Dict) -> np.ndarray:
        """
        Transform raw student data into feature vector.
        
        Args:
            student_data: Dictionary with keys:
                - cgpa: float
                - cgpa_scale: float (default 10.0)
                - internship_count: int
                - internship_months: int
                - internship_employer_type: str
                - certifications: int
                - institute_tier: int (1, 2, or 3)
                - course_type: str
                - loan_emi: float
                
        Returns:
            numpy array of shape (1, 16) ready for model inference
            
        Raises:
            ValueError: If required fields missing or invalid values
        """
        # Validate required fields
        required_fields = ['cgpa', 'institute_tier', 'course_type']
        for field in required_fields:
            if field not in student_data:
                raise ValueError(f"Required field '{field}' missing from student_data")
        
        # Extract values with defaults
        cgpa = float(student_data['cgpa'])
        cgpa_scale = float(student_data.get('cgpa_scale', 10.0))
        internship_count = int(student_data.get('internship_count', 0))
        internship_months = int(student_data.get('internship_months', 0))
        internship_employer_type = student_data.get('internship_employer_type', 'None')
        certifications = int(student_data.get('certifications', 0))
        institute_tier = int(student_data['institute_tier'])
        course_type = student_data['course_type']
        loan_emi = float(student_data.get('loan_emi', 0.0))
        
        # Validate ranges
        if not (1 <= institute_tier <= 3):
            raise ValueError(f"institute_tier must be 1, 2, or 3, got {institute_tier}")
        if cgpa < 0 or cgpa > cgpa_scale:
            raise ValueError(f"cgpa must be between 0 and {cgpa_scale}, got {cgpa}")
        
        # Feature 1: CGPA Normalized (Requirement 17.1)
        cgpa_normalized = cgpa / cgpa_scale
        
        # Feature 2: Internship Score (Requirement 17.2)
        internship_score = self._compute_internship_score(
            internship_count, internship_months, internship_employer_type
        )
        
        # Feature 3: Employer Type Score (Requirement 17.3)
        employer_type_score = self._get_employer_type_score(internship_employer_type)
        
        # Feature 4: Certifications (capped at max from config - Requirement 28.3)
        certifications_capped = min(certifications, self.max_certifications)
        
        # Features 5-7: Institute Tier One-Hot Encoding (Requirement 17.7)
        institute_tier_1 = 1.0 if institute_tier == 1 else 0.0
        institute_tier_2 = 1.0 if institute_tier == 2 else 0.0
        institute_tier_3 = 1.0 if institute_tier == 3 else 0.0
        
        # Feature 8: Course Type Label Encoding (Requirement 17.7)
        course_type_encoded = self._encode_course_type(course_type)
        
        # Feature 9: Placement Rate 3m (historical)
        placement_rate_3m = self.placement_rate_3m
        
        # Feature 10: Placement Rate 6m (historical)
        placement_rate_6m = self.placement_rate_6m
        
        # Feature 11: Salary Benchmark (historical)
        salary_benchmark = self.salary_benchmark
        
        # Feature 12: Job Demand Score (sector index)
        job_demand_score = self.job_demand_score
        
        # Feature 13: Region Job Density
        region_job_density = self.region_job_density
        
        # Feature 14: Macro Hiring Index
        macro_hiring_index = self.macro_hiring_index
        
        # Feature 15: Skill Gap Score (Requirement 17.4)
        skill_gap_score = self._compute_skill_gap_score(
            job_demand_score, cgpa_normalized, internship_score
        )
        
        # Feature 16: EMI Stress Ratio (Requirement 17.5)
        emi_stress_ratio = self._compute_emi_stress_ratio(
            loan_emi, salary_benchmark
        )
        
        # Assemble feature vector
        features = np.array([
            cgpa_normalized,
            internship_score,
            employer_type_score,
            certifications_capped,
            institute_tier_1,
            institute_tier_2,
            institute_tier_3,
            course_type_encoded,
            placement_rate_3m,
            placement_rate_6m,
            salary_benchmark,
            job_demand_score,
            region_job_density,
            macro_hiring_index,
            skill_gap_score,
            emi_stress_ratio
        ], dtype=np.float32)
        
        # Reshape to (1, n_features) for model inference
        return features.reshape(1, -1)
    
    def _compute_internship_score(
        self,
        internship_count: int,
        internship_months: int,
        internship_employer_type: str
    ) -> float:
        """
        Compute internship score using weighted formula from config.
        
        Formula (Requirement 17.2, 28.2, 28.3):
        internship_score = (count × count_weight) + (months/months_denominator × months_weight) + (employer_score × employer_weight)
        
        Weights are loaded from config.json, not hardcoded.
        
        Args:
            internship_count: Number of internships
            internship_months: Total months of internship experience
            internship_employer_type: Type of employer (MNC, Startup, PSU, NGO, None)
            
        Returns:
            Internship score as float
        """
        count_component = internship_count * self.internship_count_weight
        months_component = (internship_months / self.internship_months_denominator) * self.internship_months_weight
        employer_score = self._get_employer_type_score(internship_employer_type)
        employer_component = employer_score * self.internship_employer_weight
        
        return count_component + months_component + employer_component
    
    def _get_employer_type_score(self, employer_type: Optional[str]) -> float:
        """
        Map employer type to numeric score.
        
        Mapping (Requirement 17.3):
        - MNC: 4
        - Startup: 3
        - PSU: 2
        - NGO: 1
        - None/null: 0
        
        Args:
            employer_type: Employer type string
            
        Returns:
            Numeric score
        """
        # Handle None, NaN, or empty values
        if employer_type is None or (isinstance(employer_type, float) and np.isnan(employer_type)) or employer_type == '':
            return 0.0
        
        # Convert to string if not already
        employer_type = str(employer_type)
        
        # Case-insensitive lookup
        employer_type_upper = employer_type.upper()
        
        # Try exact match first
        if employer_type in self.EMPLOYER_TYPE_SCORES:
            return float(self.EMPLOYER_TYPE_SCORES[employer_type])
        
        # Try uppercase match
        for key, value in self.EMPLOYER_TYPE_SCORES.items():
            if key and key.upper() == employer_type_upper:
                return float(value)
        
        # Default to 0 if not found
        return 0.0
    
    def _compute_skill_gap_score(
        self,
        job_demand_score: float,
        cgpa_normalized: float,
        internship_score: float
    ) -> float:
        """
        Compute skill gap score using weights from config.
        
        Formula (Requirement 17.4, 28.2, 28.3):
        skill_gap_score = job_demand_score - (cgpa_normalized × cgpa_multiplier + internship_score × internship_multiplier)
        
        Multipliers are loaded from config.json, not hardcoded.
        
        Args:
            job_demand_score: Job demand index (1-10)
            cgpa_normalized: Normalized CGPA (0-1)
            internship_score: Computed internship score
            
        Returns:
            Skill gap score
        """
        return job_demand_score - (cgpa_normalized * self.skill_gap_cgpa_multiplier + 
                                   internship_score * self.skill_gap_internship_multiplier)
    
    def _compute_emi_stress_ratio(
        self,
        loan_emi: float,
        salary_benchmark: float
    ) -> float:
        """
        Compute EMI stress ratio.
        
        Formula (Requirement 17.5):
        emi_stress_ratio = loan_emi / monthly_salary
        where monthly_salary = (salary_benchmark_lpa * 100000) / 12
        
        Args:
            loan_emi: Monthly loan EMI in rupees
            salary_benchmark: Benchmark salary in LPA
            
        Returns:
            EMI stress ratio
        """
        if salary_benchmark <= 0:
            return 0.0
        
        # Convert LPA to monthly salary in rupees
        # LPA * 100000 = annual rupees, / 12 = monthly rupees
        monthly_salary = (salary_benchmark * 100000) / 12
        
        return loan_emi / monthly_salary
    
    def _encode_course_type(self, course_type: str) -> float:
        """
        Label encode course type.
        
        Encoding (Requirement 17.7):
        - Engineering: 0
        - MBA: 1
        - MCA: 2
        - MSc: 3
        - Other: 4
        
        Args:
            course_type: Course type string
            
        Returns:
            Encoded value as float
        """
        # Try exact match
        if course_type in self.COURSE_TYPE_ENCODING:
            return float(self.COURSE_TYPE_ENCODING[course_type])
        
        # Try case-insensitive match
        for key, value in self.COURSE_TYPE_ENCODING.items():
            if key.lower() == course_type.lower():
                return float(value)
        
        # Default to 'Other'
        return float(self.COURSE_TYPE_ENCODING['Other'])
    
    def get_feature_names(self) -> List[str]:
        """
        Return ordered list of feature names matching transform output.
        
        Returns:
            List of 16 feature names in order
        """
        return [
            'cgpa_normalized',
            'internship_score',
            'employer_type_score',
            'certifications',
            'institute_tier_1',
            'institute_tier_2',
            'institute_tier_3',
            'course_type_encoded',
            'placement_rate_3m',
            'placement_rate_6m',
            'salary_benchmark',
            'job_demand_score',
            'region_job_density',
            'macro_hiring_index',
            'skill_gap_score',
            'emi_stress_ratio'
        ]
