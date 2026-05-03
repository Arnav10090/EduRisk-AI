"""
Unit tests for Feature Engineering Configuration (Requirement 28)

Tests that feature engineering weights are loaded from config.json
and that the system falls back to defaults when config is missing.
"""

import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
from ml.pipeline.feature_engineering import FeatureEngineer


class TestFeatureEngineeringConfig:
    """Test feature engineering configuration loading and usage."""
    
    def test_load_default_config(self):
        """Test loading default config.json file (Requirement 28.1)."""
        engineer = FeatureEngineer()
        
        # Verify default weights are loaded
        assert engineer.internship_count_weight == 0.4
        assert engineer.internship_months_weight == 0.3
        assert engineer.internship_employer_weight == 0.3
        assert engineer.internship_months_denominator == 24.0
        
        assert engineer.skill_gap_cgpa_multiplier == 5.0
        assert engineer.skill_gap_internship_multiplier == 5.0
        
        assert engineer.max_certifications == 5
        
        assert engineer.placement_rate_3m == 0.45
        assert engineer.placement_rate_6m == 0.65
        assert engineer.salary_benchmark == 5.0
    
    def test_config_includes_all_weights(self):
        """Test that config.json includes all required weights (Requirement 28.2)."""
        config_path = Path(__file__).parent / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify internship score weights
        assert 'internship_score_weights' in config
        assert 'count_weight' in config['internship_score_weights']
        assert 'months_weight' in config['internship_score_weights']
        assert 'employer_weight' in config['internship_score_weights']
        
        # Verify skill gap weights
        assert 'skill_gap_weights' in config
        assert 'cgpa_multiplier' in config['skill_gap_weights']
        assert 'internship_multiplier' in config['skill_gap_weights']
        
        # Verify certification cap
        assert 'certification_cap' in config
        assert 'max_certifications' in config['certification_cap']
        
        # Verify historical defaults
        assert 'historical_defaults' in config
        assert 'placement_rate_3m' in config['historical_defaults']
        assert 'salary_benchmark' in config['historical_defaults']
    
    def test_no_hardcoded_weights_in_methods(self):
        """Test that methods use config values, not hardcoded weights (Requirement 28.3)."""
        # Create engineer with custom weights
        custom_config = {
            'internship_score_weights': {
                'count_weight': 0.5,  # Changed from 0.4
                'months_weight': 0.25,  # Changed from 0.3
                'employer_weight': 0.25,  # Changed from 0.3
                'months_denominator': 20.0  # Changed from 24.0
            },
            'skill_gap_weights': {
                'cgpa_multiplier': 6.0,  # Changed from 5.0
                'internship_multiplier': 4.0  # Changed from 5.0
            },
            'certification_cap': {
                'max_certifications': 3  # Changed from 5
            },
            'historical_defaults': {
                'placement_rate_3m': 0.5,
                'placement_rate_6m': 0.7,
                'placement_rate_12m': 0.85,
                'salary_benchmark': 6.0,
                'job_demand_score': 6.0,
                'region_job_density': 0.6,
                'macro_hiring_index': 0.7
            },
            'employer_type_scores': {
                'MNC': 4, 'Startup': 3, 'PSU': 2, 'NGO': 1, 'None': 0
            },
            'course_type_encoding': {
                'Engineering': 0, 'MBA': 1, 'MCA': 2, 'MSc': 3, 'Other': 4
            }
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_config_path = Path(f.name)
        
        try:
            engineer = FeatureEngineer(config_path=temp_config_path)
            
            # Verify custom weights are loaded
            assert engineer.internship_count_weight == 0.5
            assert engineer.internship_months_weight == 0.25
            assert engineer.skill_gap_cgpa_multiplier == 6.0
            assert engineer.max_certifications == 3
            
            # Test that internship score uses custom weights
            student_data = {
                'cgpa': 8.5,
                'cgpa_scale': 10.0,
                'internship_count': 2,
                'internship_months': 12,
                'internship_employer_type': 'MNC',
                'certifications': 3,
                'institute_tier': 1,
                'course_type': 'Engineering',
                'loan_emi': 10000
            }
            
            features = engineer.transform(student_data)
            
            # Verify features are computed with custom weights
            # internship_score = (2 × 0.5) + (12/20 × 0.25) + (4 × 0.25)
            expected_internship_score = (2 * 0.5) + (12/20.0 * 0.25) + (4 * 0.25)
            actual_internship_score = features[0, 1]  # Second feature
            
            assert abs(actual_internship_score - expected_internship_score) < 0.01
            
            # Verify certifications are capped at custom max (3)
            certifications_feature = features[0, 3]  # Fourth feature
            assert certifications_feature == 3  # Should be capped at 3, not 5
            
        finally:
            # Clean up temp file
            temp_config_path.unlink()
    
    def test_fallback_to_defaults_when_config_missing(self):
        """Test fallback to default weights when config.json is missing (Requirement 28.4)."""
        # Create engineer with non-existent config path
        non_existent_path = Path("/tmp/nonexistent_config_12345.json")
        engineer = FeatureEngineer(config_path=non_existent_path)
        
        # Verify default weights are used
        assert engineer.internship_count_weight == 0.4
        assert engineer.internship_months_weight == 0.3
        assert engineer.skill_gap_cgpa_multiplier == 5.0
        assert engineer.max_certifications == 5
    
    def test_fallback_to_defaults_when_config_invalid_json(self):
        """Test fallback to defaults when config.json has invalid JSON (Requirement 28.4)."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content }")
            temp_config_path = Path(f.name)
        
        try:
            engineer = FeatureEngineer(config_path=temp_config_path)
            
            # Verify default weights are used despite invalid JSON
            assert engineer.internship_count_weight == 0.4
            assert engineer.skill_gap_cgpa_multiplier == 5.0
        finally:
            temp_config_path.unlink()
    
    def test_features_calculated_correctly_with_default_config(self):
        """Test that features are calculated correctly with default config (Requirement 28.3.1)."""
        engineer = FeatureEngineer()
        
        student_data = {
            'cgpa': 8.5,
            'cgpa_scale': 10.0,
            'internship_count': 2,
            'internship_months': 12,
            'internship_employer_type': 'MNC',
            'certifications': 3,
            'institute_tier': 1,
            'course_type': 'Engineering',
            'loan_emi': 10000
        }
        
        features = engineer.transform(student_data)
        
        # Verify shape
        assert features.shape == (1, 16)
        
        # Verify CGPA normalized
        assert abs(features[0, 0] - 0.85) < 0.01
        
        # Verify internship score with default weights
        # (2 × 0.4) + (12/24 × 0.3) + (4 × 0.3) = 0.8 + 0.15 + 1.2 = 2.15
        expected_internship_score = (2 * 0.4) + (12/24.0 * 0.3) + (4 * 0.3)
        assert abs(features[0, 1] - expected_internship_score) < 0.01
        
        # Verify employer type score
        assert features[0, 2] == 4.0  # MNC = 4
        
        # Verify certifications (capped at 5)
        assert features[0, 3] == 3.0
        
        # Verify institute tier one-hot encoding
        assert features[0, 4] == 1.0  # tier 1
        assert features[0, 5] == 0.0  # tier 2
        assert features[0, 6] == 0.0  # tier 3
        
        # Verify course type encoding
        assert features[0, 7] == 0.0  # Engineering = 0
    
    def test_features_calculated_correctly_with_modified_weights(self):
        """Test that features are calculated correctly with modified weights (Requirement 28.3.2)."""
        custom_config = {
            'internship_score_weights': {
                'count_weight': 0.6,
                'months_weight': 0.2,
                'employer_weight': 0.2,
                'months_denominator': 30.0
            },
            'skill_gap_weights': {
                'cgpa_multiplier': 4.0,
                'internship_multiplier': 6.0
            },
            'certification_cap': {
                'max_certifications': 10
            },
            'historical_defaults': {
                'placement_rate_3m': 0.5,
                'placement_rate_6m': 0.7,
                'placement_rate_12m': 0.85,
                'salary_benchmark': 6.0,
                'job_demand_score': 7.0,
                'region_job_density': 0.6,
                'macro_hiring_index': 0.7
            },
            'employer_type_scores': {
                'MNC': 4, 'Startup': 3, 'PSU': 2, 'NGO': 1, 'None': 0
            },
            'course_type_encoding': {
                'Engineering': 0, 'MBA': 1, 'MCA': 2, 'MSc': 3, 'Other': 4
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_config, f)
            temp_config_path = Path(f.name)
        
        try:
            engineer = FeatureEngineer(config_path=temp_config_path)
            
            student_data = {
                'cgpa': 8.5,
                'cgpa_scale': 10.0,
                'internship_count': 2,
                'internship_months': 15,
                'internship_employer_type': 'Startup',
                'certifications': 7,
                'institute_tier': 2,
                'course_type': 'MBA',
                'loan_emi': 15000
            }
            
            features = engineer.transform(student_data)
            
            # Verify internship score with custom weights
            # (2 × 0.6) + (15/30 × 0.2) + (3 × 0.2) = 1.2 + 0.1 + 0.6 = 1.9
            expected_internship_score = (2 * 0.6) + (15/30.0 * 0.2) + (3 * 0.2)
            assert abs(features[0, 1] - expected_internship_score) < 0.01
            
            # Verify certifications (capped at 10, so should be 7)
            assert features[0, 3] == 7.0
            
            # Verify historical defaults
            assert abs(features[0, 8] - 0.5) < 0.01  # placement_rate_3m
            assert abs(features[0, 9] - 0.7) < 0.01  # placement_rate_6m
            assert abs(features[0, 10] - 6.0) < 0.01  # salary_benchmark
            assert abs(features[0, 11] - 7.0) < 0.01  # job_demand_score
            
            # Verify skill gap score uses custom multipliers
            cgpa_normalized = 0.85
            internship_score = expected_internship_score
            job_demand = 7.0
            expected_skill_gap = job_demand - (cgpa_normalized * 4.0 + internship_score * 6.0)
            assert abs(features[0, 14] - expected_skill_gap) < 0.01
            
        finally:
            temp_config_path.unlink()
    
    def test_config_logging(self, caplog):
        """Test that config loading is logged (Requirement 28.6)."""
        import logging
        caplog.set_level(logging.INFO)
        
        engineer = FeatureEngineer()
        
        # Verify logging messages
        log_messages = [record.message for record in caplog.records]
        
        # Should log config file path
        assert any('config from' in msg.lower() for msg in log_messages)
        
        # Should log internship weights
        assert any('internship weights' in msg.lower() for msg in log_messages)
        
        # Should log skill gap multipliers
        assert any('skill gap multipliers' in msg.lower() for msg in log_messages)
        
        # Should log historical defaults
        assert any('historical defaults' in msg.lower() for msg in log_messages)


class TestConfigComments:
    """Test that config.json includes explanatory comments (Requirement 28.7)."""
    
    def test_config_has_comments(self):
        """Test that config.json includes comments explaining each weight (Requirement 28.7)."""
        config_path = Path(__file__).parent / "config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Verify top-level comments
        assert '_comment' in config or '_description' in config
        
        # Verify internship score weights have comments
        assert '_comment' in config['internship_score_weights'] or '_formula' in config['internship_score_weights']
        
        # Verify skill gap weights have comments
        assert '_comment' in config['skill_gap_weights'] or '_formula' in config['skill_gap_weights']
        
        # Verify certification cap has comment
        assert '_comment' in config['certification_cap']
        
        # Verify historical defaults have comments
        assert '_comment' in config['historical_defaults'] or '_units' in config['historical_defaults']
        
        # Verify employer type scores have comment
        assert '_comment' in config['employer_type_scores']
        
        # Verify course type encoding has comment
        assert '_comment' in config['course_type_encoding']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
