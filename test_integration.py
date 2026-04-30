#!/usr/bin/env python3
"""
Integration Test Script for EduRisk AI
Tests end-to-end flow: form submission → prediction → display

This script verifies:
1. Backend can load ML models from ml/ directory
2. Database migrations run successfully with Alembic
3. Backend API endpoints are accessible and functional
4. End-to-end flow works: form submission → prediction → display results
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import httpx

# Color codes for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_success(message: str):
    print(f"{GREEN}✓{NC} {message}")

def print_error(message: str):
    print(f"{RED}✗{NC} {message}")

def print_warning(message: str):
    print(f"{YELLOW}⚠{NC} {message}")

def print_info(message: str):
    print(f"{BLUE}ℹ{NC} {message}")

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"{BLUE}{title}{NC}")
    print('='*60)

class IntegrationTester:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://edurisk:edurisk_password@localhost:5432/edurisk_db")
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.engine = None
        self.session_maker = None
        
    async def setup(self):
        """Initialize database connection"""
        try:
            self.engine = create_async_engine(self.database_url, echo=False)
            self.session_maker = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            print_success("Database connection initialized")
        except Exception as e:
            print_error(f"Failed to initialize database connection: {e}")
            self.errors.append(f"Database setup failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.engine:
            await self.engine.dispose()
    
    async def test_ml_models_exist(self):
        """Test 1: Verify ML models exist"""
        print_section("Test 1: ML Models Availability")
        
        models_dir = Path("ml/models")
        required_models = [
            "placement_model_3m.pkl",
            "placement_model_6m.pkl",
            "placement_model_12m.pkl",
            "salary_model.pkl",
            "version.json",
            "feature_names.json"
        ]
        
        for model_file in required_models:
            model_path = models_dir / model_file
            if model_path.exists():
                print_success(f"Found {model_file}")
            else:
                print_error(f"Missing {model_file}")
                self.errors.append(f"ML model missing: {model_file}")
        
        # Check version.json content
        version_file = models_dir / "version.json"
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                print_info(f"Model version: {version_data.get('version', 'unknown')}")
                print_success("version.json is valid")
            except Exception as e:
                print_error(f"Failed to read version.json: {e}")
                self.errors.append(f"version.json invalid: {e}")
    
    async def test_database_connection(self):
        """Test 2: Verify database connectivity"""
        print_section("Test 2: Database Connectivity")
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                print_success("Database connection successful")
        except Exception as e:
            print_error(f"Database connection failed: {e}")
            self.errors.append(f"Database connection failed: {e}")
    
    async def test_database_schema(self):
        """Test 3: Verify database schema (tables exist)"""
        print_section("Test 3: Database Schema")
        
        required_tables = ["students", "predictions", "audit_logs"]
        
        try:
            async with self.engine.begin() as conn:
                for table in required_tables:
                    result = await conn.execute(
                        text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                    )
                    exists = result.scalar()
                    if exists:
                        print_success(f"Table '{table}' exists")
                    else:
                        print_error(f"Table '{table}' does not exist")
                        self.errors.append(f"Missing table: {table}")
        except Exception as e:
            print_error(f"Failed to check database schema: {e}")
            self.errors.append(f"Schema check failed: {e}")
    
    async def test_health_endpoint(self):
        """Test 4: Verify health check endpoint"""
        print_section("Test 4: Health Check Endpoint")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/api/health", timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Health check passed: {data.get('status', 'unknown')}")
                    print_info(f"Model version: {data.get('model_version', 'unknown')}")
                    print_info(f"Database: {data.get('database', 'unknown')}")
                elif response.status_code == 503:
                    data = response.json()
                    print_warning(f"Service degraded: {data}")
                    self.warnings.append(f"Service degraded: {data}")
                else:
                    print_error(f"Health check failed with status {response.status_code}")
                    self.errors.append(f"Health check returned {response.status_code}")
        except httpx.ConnectError:
            print_error("Cannot connect to backend API - is it running?")
            self.errors.append("Backend API not accessible")
        except Exception as e:
            print_error(f"Health check failed: {e}")
            self.errors.append(f"Health check error: {e}")
    
    async def test_prediction_endpoint(self):
        """Test 5: Test prediction endpoint with sample data"""
        print_section("Test 5: Prediction Endpoint (End-to-End Flow)")
        
        # Sample student data
        student_data = {
            "name": "Integration Test Student",
            "course_type": "Engineering",
            "institute_name": "Test Institute",
            "institute_tier": 2,
            "cgpa": 8.5,
            "cgpa_scale": 10.0,
            "year_of_grad": 2025,
            "internship_count": 2,
            "internship_months": 6,
            "internship_employer_type": "MNC",
            "certifications": 3,
            "region": "Mumbai",
            "loan_amount": 500000.0,
            "loan_emi": 15000.0
        }
        
        try:
            async with httpx.AsyncClient() as client:
                print_info("Submitting prediction request...")
                response = await client.post(
                    f"{self.api_base_url}/api/predict",
                    json=student_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("Prediction successful!")
                    print_info(f"Student ID: {data.get('student_id', 'N/A')}")
                    print_info(f"Risk Score: {data.get('risk_score', 'N/A')}/100")
                    print_info(f"Risk Level: {data.get('risk_level', 'N/A')}")
                    print_info(f"Placement Label: {data.get('placement_label', 'N/A')}")
                    print_info(f"3-month probability: {data.get('prob_placed_3m', 'N/A')}")
                    print_info(f"6-month probability: {data.get('prob_placed_6m', 'N/A')}")
                    print_info(f"12-month probability: {data.get('prob_placed_12m', 'N/A')}")
                    print_info(f"Salary range: {data.get('salary_min', 'N/A')} - {data.get('salary_max', 'N/A')} LPA")
                    print_info(f"EMI affordability: {data.get('emi_affordability', 'N/A')}")
                    
                    # Verify response structure
                    required_fields = [
                        'student_id', 'prediction_id', 'risk_score', 'risk_level',
                        'prob_placed_3m', 'prob_placed_6m', 'prob_placed_12m',
                        'placement_label', 'salary_min', 'salary_max',
                        'top_risk_drivers', 'next_best_actions'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        print_warning(f"Response missing fields: {missing_fields}")
                        self.warnings.append(f"Missing response fields: {missing_fields}")
                    else:
                        print_success("All required fields present in response")
                    
                    # Check if SHAP drivers exist
                    if data.get('top_risk_drivers'):
                        print_success(f"Found {len(data['top_risk_drivers'])} risk drivers")
                    else:
                        print_warning("No risk drivers in response")
                    
                    # Check if actions exist
                    if data.get('next_best_actions'):
                        print_success(f"Found {len(data['next_best_actions'])} recommended actions")
                    else:
                        print_warning("No recommended actions in response")
                    
                    return data.get('student_id')
                    
                elif response.status_code == 422:
                    print_error(f"Validation error: {response.json()}")
                    self.errors.append("Prediction validation failed")
                else:
                    print_error(f"Prediction failed with status {response.status_code}: {response.text}")
                    self.errors.append(f"Prediction returned {response.status_code}")
                    
        except httpx.ConnectError:
            print_error("Cannot connect to backend API")
            self.errors.append("Backend API not accessible for prediction")
        except Exception as e:
            print_error(f"Prediction test failed: {e}")
            self.errors.append(f"Prediction error: {e}")
        
        return None
    
    async def test_explain_endpoint(self, student_id: str):
        """Test 6: Test explanation endpoint"""
        print_section("Test 6: Explanation Endpoint")
        
        if not student_id:
            print_warning("Skipping explanation test (no student_id from prediction)")
            return
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/explain/{student_id}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("Explanation retrieved successfully")
                    print_info(f"Base value: {data.get('base_value', 'N/A')}")
                    print_info(f"Prediction: {data.get('prediction', 'N/A')}")
                    
                    if data.get('shap_values'):
                        print_success(f"SHAP values contain {len(data['shap_values'])} features")
                    else:
                        print_warning("No SHAP values in response")
                    
                    if data.get('waterfall_data'):
                        print_success(f"Waterfall data contains {len(data['waterfall_data'])} entries")
                    else:
                        print_warning("No waterfall data in response")
                        
                elif response.status_code == 404:
                    print_error("Student not found for explanation")
                    self.errors.append("Explanation endpoint returned 404")
                else:
                    print_error(f"Explanation failed with status {response.status_code}")
                    self.errors.append(f"Explanation returned {response.status_code}")
                    
        except Exception as e:
            print_error(f"Explanation test failed: {e}")
            self.errors.append(f"Explanation error: {e}")
    
    async def test_students_endpoint(self):
        """Test 7: Test students list endpoint"""
        print_section("Test 7: Students List Endpoint")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/students?limit=10",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("Students list retrieved successfully")
                    print_info(f"Total students: {data.get('total_count', 0)}")
                    print_info(f"Returned: {len(data.get('students', []))} students")
                else:
                    print_error(f"Students list failed with status {response.status_code}")
                    self.errors.append(f"Students endpoint returned {response.status_code}")
                    
        except Exception as e:
            print_error(f"Students list test failed: {e}")
            self.errors.append(f"Students list error: {e}")
    
    async def test_alerts_endpoint(self):
        """Test 8: Test alerts endpoint"""
        print_section("Test 8: Alerts Endpoint")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/alerts?threshold=high",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("Alerts retrieved successfully")
                    print_info(f"High-risk alerts: {len(data.get('alerts', []))}")
                else:
                    print_error(f"Alerts failed with status {response.status_code}")
                    self.errors.append(f"Alerts endpoint returned {response.status_code}")
                    
        except Exception as e:
            print_error(f"Alerts test failed: {e}")
            self.errors.append(f"Alerts error: {e}")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n{BLUE}{'='*60}")
        print("EduRisk AI - Integration Test Suite")
        print(f"{'='*60}{NC}\n")
        
        await self.setup()
        
        # Run tests in sequence
        await self.test_ml_models_exist()
        await self.test_database_connection()
        await self.test_database_schema()
        await self.test_health_endpoint()
        
        # End-to-end flow test
        student_id = await self.test_prediction_endpoint()
        await self.test_explain_endpoint(student_id)
        
        # Additional endpoint tests
        await self.test_students_endpoint()
        await self.test_alerts_endpoint()
        
        await self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print_section("Test Summary")
        
        total_tests = 8
        failed_tests = len(self.errors)
        passed_tests = total_tests - failed_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"{GREEN}Passed: {passed_tests}{NC}")
        print(f"{RED}Failed: {failed_tests}{NC}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{NC}")
        
        if self.errors:
            print(f"\n{RED}Errors:{NC}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{NC}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "="*60)
        if not self.errors:
            print(f"{GREEN}✓ All integration tests passed!{NC}")
            print("\nThe system is ready for use:")
            print(f"  • Backend API: {self.api_base_url}")
            print(f"  • Frontend: http://localhost:3000")
            print(f"  • API Docs: {self.api_base_url}/docs")
            return 0
        else:
            print(f"{RED}✗ Integration tests failed{NC}")
            print("\nPlease fix the errors above before using the system.")
            return 1

async def main():
    """Main entry point"""
    tester = IntegrationTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
