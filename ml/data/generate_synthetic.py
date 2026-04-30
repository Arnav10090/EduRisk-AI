"""
Synthetic Data Generation for EduRisk AI

This script generates synthetic student data for model training.
Generates 5000 records with realistic distributions for academic,
internship, and placement data.

Feature: edurisk-ai-placement-intelligence
Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List
import random


class SyntheticDataGenerator:
    """
    Generates synthetic student data with realistic distributions.
    
    Distributions:
    - CGPA: Normal(mean=7.5, std=1.2), clipped to [4.0, 10.0]
    - Institute Tier: Multinomial([0.2, 0.5, 0.3] for tiers 1, 2, 3)
    - Internship Count: Poisson(lambda=1.5), capped at 6
    - Placement: Logistic function of tier, cgpa, internships
    - Salary: Lognormal based on tier and course type
    """
    
    # Course types and their distribution
    COURSE_TYPES = ['Engineering', 'MBA', 'MCA', 'MSc']
    COURSE_TYPE_PROBS = [0.5, 0.25, 0.15, 0.10]
    
    # Employer types
    EMPLOYER_TYPES = ['MNC', 'Startup', 'PSU', 'NGO', 'None']
    EMPLOYER_TYPE_PROBS = [0.3, 0.25, 0.15, 0.10, 0.20]
    
    # Regions
    REGIONS = ['North', 'South', 'East', 'West', 'Central']
    REGION_PROBS = [0.25, 0.30, 0.15, 0.20, 0.10]
    
    # Institute tier probabilities (Requirement 30.3)
    TIER_PROBS = [0.2, 0.5, 0.3]  # Tier 1, 2, 3
    
    # Salary benchmarks by tier and course (in LPA)
    SALARY_BENCHMARKS = {
        1: {'Engineering': 12.0, 'MBA': 15.0, 'MCA': 10.0, 'MSc': 8.0},
        2: {'Engineering': 7.0, 'MBA': 9.0, 'MCA': 6.5, 'MSc': 5.5},
        3: {'Engineering': 4.5, 'MBA': 6.0, 'MCA': 4.0, 'MSc': 3.5}
    }
    
    def __init__(self, n_records: int = 5000, random_seed: int = 42):
        """
        Initialize generator.
        
        Args:
            n_records: Number of records to generate (default 5000)
            random_seed: Random seed for reproducibility
        """
        self.n_records = n_records
        self.random_seed = random_seed
        np.random.seed(random_seed)
        random.seed(random_seed)
    
    def generate(self) -> pd.DataFrame:
        """
        Generate synthetic student dataset.
        
        Returns:
            DataFrame with synthetic student records
        """
        data = []
        
        for i in range(self.n_records):
            record = self._generate_student_record(i)
            data.append(record)
        
        df = pd.DataFrame(data)
        return df
    
    def _generate_student_record(self, index: int) -> Dict:
        """
        Generate a single student record.
        
        Args:
            index: Record index for unique ID generation
            
        Returns:
            Dictionary with student data
        """
        # Generate institute tier (Requirement 30.3)
        institute_tier = np.random.choice([1, 2, 3], p=self.TIER_PROBS)
        
        # Generate CGPA (Requirement 30.2)
        cgpa = np.random.normal(loc=7.5, scale=1.2)
        cgpa = np.clip(cgpa, 4.0, 10.0)
        cgpa = round(cgpa, 2)
        
        # Generate course type
        course_type = np.random.choice(self.COURSE_TYPES, p=self.COURSE_TYPE_PROBS)
        
        # Generate internship count (Requirement 30.4)
        internship_count = np.random.poisson(lam=1.5)
        internship_count = min(internship_count, 6)  # Cap at 6
        
        # Generate internship months (proportional to count)
        if internship_count > 0:
            internship_months = internship_count * np.random.randint(2, 7)
        else:
            internship_months = 0
        
        # Generate employer type
        if internship_count > 0:
            employer_type = np.random.choice(
                self.EMPLOYER_TYPES[:-1],  # Exclude 'None'
                p=[p / sum(self.EMPLOYER_TYPE_PROBS[:-1]) for p in self.EMPLOYER_TYPE_PROBS[:-1]]
            )
        else:
            employer_type = 'None'
        
        # Generate certifications (correlated with CGPA)
        cert_prob = (cgpa - 4.0) / 6.0  # Higher CGPA -> more certs
        certifications = np.random.binomial(n=5, p=cert_prob)
        
        # Generate region
        region = np.random.choice(self.REGIONS, p=self.REGION_PROBS)
        
        # Generate year of graduation
        year_of_grad = np.random.choice([2024, 2025, 2026], p=[0.3, 0.4, 0.3])
        
        # Generate placement labels (Requirement 30.5)
        # Logistic function based on tier, cgpa, internships
        placement_3m, placement_6m, placement_12m = self._generate_placement_labels(
            institute_tier, cgpa, internship_count
        )
        
        # Generate salary (Requirement 30.6)
        salary = self._generate_salary(institute_tier, course_type, cgpa, placement_3m)
        
        # Generate loan details
        loan_amount = self._generate_loan_amount(course_type, institute_tier)
        loan_emi = loan_amount * 0.012  # Approximate 1.2% monthly EMI
        
        # Generate institute name
        institute_name = self._generate_institute_name(institute_tier, index)
        
        return {
            'name': f'Student_{index:05d}',
            'course_type': course_type,
            'institute_name': institute_name,
            'institute_tier': institute_tier,
            'cgpa': cgpa,
            'cgpa_scale': 10.0,
            'year_of_grad': year_of_grad,
            'internship_count': internship_count,
            'internship_months': internship_months,
            'internship_employer_type': employer_type,
            'certifications': certifications,
            'region': region,
            'loan_amount': round(loan_amount, 2),
            'loan_emi': round(loan_emi, 2),
            'placed_3m': placement_3m,
            'placed_6m': placement_6m,
            'placed_12m': placement_12m,
            'salary_lpa': round(salary, 2) if salary > 0 else None
        }
    
    def _generate_placement_labels(
        self,
        institute_tier: int,
        cgpa: float,
        internship_count: int
    ) -> tuple:
        """
        Generate placement labels using logistic function.
        
        Logistic function based on:
        - Institute tier (tier 1 = higher probability)
        - CGPA > 8
        - Internship count > 2
        
        Args:
            institute_tier: Institute tier (1, 2, or 3)
            cgpa: Student CGPA
            internship_count: Number of internships
            
        Returns:
            Tuple of (placed_3m, placed_6m, placed_12m) as binary labels
        """
        # Compute logit score
        logit = 0.0
        
        # Tier contribution (tier 1 is best)
        if institute_tier == 1:
            logit += 2.0
        elif institute_tier == 2:
            logit += 0.5
        else:
            logit -= 1.0
        
        # CGPA contribution
        if cgpa > 8.0:
            logit += 1.5
        elif cgpa > 7.0:
            logit += 0.5
        else:
            logit -= 0.5
        
        # Internship contribution
        if internship_count > 2:
            logit += 1.5
        elif internship_count > 0:
            logit += 0.5
        else:
            logit -= 1.0
        
        # Convert to probability using sigmoid
        prob_3m = 1 / (1 + np.exp(-logit))
        
        # 6-month probability is higher
        prob_6m = 1 / (1 + np.exp(-(logit + 1.0)))
        
        # 12-month probability is even higher
        prob_12m = 1 / (1 + np.exp(-(logit + 2.0)))
        
        # Sample binary labels
        placed_3m = 1 if np.random.random() < prob_3m else 0
        placed_6m = 1 if (placed_3m == 1 or np.random.random() < prob_6m) else 0
        placed_12m = 1 if (placed_6m == 1 or np.random.random() < prob_12m) else 0
        
        return placed_3m, placed_6m, placed_12m
    
    def _generate_salary(
        self,
        institute_tier: int,
        course_type: str,
        cgpa: float,
        placed: int
    ) -> float:
        """
        Generate salary using lognormal distribution.
        
        Salary depends on tier, course type, and CGPA.
        Only generate salary if student is placed.
        
        Args:
            institute_tier: Institute tier
            course_type: Course type
            cgpa: Student CGPA
            placed: Whether student is placed (1 or 0)
            
        Returns:
            Salary in LPA (0 if not placed)
        """
        if placed == 0:
            return 0.0
        
        # Get base salary benchmark
        base_salary = self.SALARY_BENCHMARKS[institute_tier][course_type]
        
        # Add CGPA bonus (higher CGPA -> higher salary)
        cgpa_multiplier = 1.0 + (cgpa - 7.5) * 0.1
        
        # Generate from lognormal distribution
        mu = np.log(base_salary * cgpa_multiplier)
        sigma = 0.3  # 30% variability
        
        salary = np.random.lognormal(mean=mu, sigma=sigma)
        
        # Ensure minimum salary of 3 LPA
        salary = max(salary, 3.0)
        
        return salary
    
    def _generate_loan_amount(self, course_type: str, institute_tier: int) -> float:
        """
        Generate loan amount based on course and tier.
        
        Args:
            course_type: Course type
            institute_tier: Institute tier
            
        Returns:
            Loan amount in lakhs
        """
        # Base loan amounts by course
        base_loans = {
            'Engineering': 15.0,
            'MBA': 20.0,
            'MCA': 10.0,
            'MSc': 8.0
        }
        
        base = base_loans[course_type]
        
        # Tier 1 institutes are more expensive
        if institute_tier == 1:
            base *= 1.5
        elif institute_tier == 2:
            base *= 1.0
        else:
            base *= 0.7
        
        # Add some randomness
        loan = base * np.random.uniform(0.8, 1.2)
        
        return loan
    
    def _generate_institute_name(self, tier: int, index: int) -> str:
        """
        Generate institute name based on tier.
        
        Args:
            tier: Institute tier
            index: Record index
            
        Returns:
            Institute name
        """
        tier_prefixes = {
            1: ['IIT', 'NIT', 'BITS'],
            2: ['State Engineering College', 'Regional Institute', 'University'],
            3: ['College of', 'Institute of', 'Academy of']
        }
        
        prefix = random.choice(tier_prefixes[tier])
        suffix = f'{index % 100:02d}'
        
        return f'{prefix} {suffix}'
    
    def save(self, df: pd.DataFrame, output_dir: str = 'ml/data/synthetic') -> str:
        """
        Save synthetic data to CSV file.
        
        Args:
            df: DataFrame to save
            output_dir: Output directory path
            
        Returns:
            Path to saved file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV (Requirement 30.7)
        output_file = output_path / 'students.csv'
        df.to_csv(output_file, index=False)
        
        print(f'Saved {len(df)} records to {output_file}')
        print(f'\nDataset statistics:')
        print(f'  - Institute Tier distribution: {df["institute_tier"].value_counts().sort_index().to_dict()}')
        print(f'  - Course Type distribution: {df["course_type"].value_counts().to_dict()}')
        print(f'  - Mean CGPA: {df["cgpa"].mean():.2f} (std: {df["cgpa"].std():.2f})')
        print(f'  - Mean internship count: {df["internship_count"].mean():.2f}')
        print(f'  - Placement rates: 3m={df["placed_3m"].mean():.2%}, 6m={df["placed_6m"].mean():.2%}, 12m={df["placed_12m"].mean():.2%}')
        
        return str(output_file)


def main():
    """
    Main function to generate and save synthetic data.
    """
    print('Generating synthetic student data...')
    print('=' * 60)
    
    # Generate 5000 records (Requirement 30.1)
    generator = SyntheticDataGenerator(n_records=5000, random_seed=42)
    df = generator.generate()
    
    # Save to CSV
    output_file = generator.save(df)
    
    print('=' * 60)
    print(f'✓ Synthetic data generation complete!')
    print(f'✓ Output file: {output_file}')


if __name__ == '__main__':
    main()
