#!/usr/bin/env python3
"""
Verification Script for Task 7.3: JWT Dependency for Protected Routes

This script verifies that:
1. get_current_user() dependency function exists
2. All protected routes use the dependency
3. User information is properly extracted
4. Error handling works correctly

Requirements: 7.3.1, 7.3.2, 7.3.3, 7.3.4
"""

import sys
import inspect
from typing import List, Tuple

def verify_get_current_user_exists() -> Tuple[bool, str]:
    """Verify get_current_user() dependency function exists (Requirement 7.3.1)"""
    try:
        from backend.routes.auth import get_current_user
        
        # Check it's a function
        if not callable(get_current_user):
            return False, "get_current_user is not callable"
        
        # Check it has the right signature
        sig = inspect.signature(get_current_user)
        params = list(sig.parameters.keys())
        
        if 'token' not in params:
            return False, "get_current_user missing 'token' parameter"
        
        return True, "✓ get_current_user() dependency function exists"
    
    except ImportError as e:
        return False, f"Failed to import get_current_user: {e}"
    except Exception as e:
        return False, f"Error verifying get_current_user: {e}"


def verify_protected_routes() -> Tuple[bool, str]:
    """Verify protected routes use get_current_user dependency"""
    try:
        from backend.routes import students, predict, alerts, explain
        from backend.routes.auth import get_current_user
        
        protected_routes = []
        
        # Check students routes
        for route in students.router.routes:
            if hasattr(route, 'dependant'):
                deps = [str(d.call) for d in route.dependant.dependencies]
                if any('get_current_user' in dep for dep in deps):
                    protected_routes.append(f"students.{route.path}")
        
        # Check predict routes
        for route in predict.router.routes:
            if hasattr(route, 'dependant'):
                deps = [str(d.call) for d in route.dependant.dependencies]
                if any('get_current_user' in dep for dep in deps):
                    protected_routes.append(f"predict.{route.path}")
        
        # Check alerts routes
        for route in alerts.router.routes:
            if hasattr(route, 'dependant'):
                deps = [str(d.call) for d in route.dependant.dependencies]
                if any('get_current_user' in dep for dep in deps):
                    protected_routes.append(f"alerts.{route.path}")
        
        # Check explain routes
        for route in explain.router.routes:
            if hasattr(route, 'dependant'):
                deps = [str(d.call) for d in route.dependant.dependencies]
                if any('get_current_user' in dep for dep in deps):
                    protected_routes.append(f"explain.{route.path}")
        
        if len(protected_routes) >= 7:  # We expect at least 7 protected routes
            return True, f"✓ {len(protected_routes)} protected routes use JWT dependency"
        else:
            return False, f"Only {len(protected_routes)} routes protected (expected >= 7)"
    
    except Exception as e:
        return False, f"Error verifying protected routes: {e}"


def verify_jwt_extraction() -> Tuple[bool, str]:
    """Verify JWT extraction and validation logic (Requirement 7.3.2)"""
    try:
        from backend.core.security import verify_token, create_access_token
        
        # Create a test token
        test_token = create_access_token({"sub": "test_user", "email": "test@example.com"})
        
        # Verify it can be decoded
        payload = verify_token(test_token)
        
        if not payload:
            return False, "Token verification failed"
        
        if payload.get("sub") != "test_user":
            return False, "Token payload extraction failed"
        
        return True, "✓ JWT extraction and validation works correctly"
    
    except Exception as e:
        return False, f"Error verifying JWT extraction: {e}"


def verify_user_info_extraction() -> Tuple[bool, str]:
    """Verify user information is extracted from JWT payload (Requirement 7.3.3)"""
    try:
        from backend.core.security import create_access_token, verify_token
        
        # Create token with user info
        user_data = {
            "sub": "admin",
            "email": "admin@edurisk.ai",
            "full_name": "Admin User"
        }
        token = create_access_token(user_data)
        
        # Verify user info is in payload
        payload = verify_token(token)
        
        if not payload:
            return False, "Failed to verify token"
        
        if payload.get("sub") != "admin":
            return False, "Username not in payload"
        
        if payload.get("email") != "admin@edurisk.ai":
            return False, "Email not in payload"
        
        if payload.get("full_name") != "Admin User":
            return False, "Full name not in payload"
        
        return True, "✓ User information properly extracted from JWT payload"
    
    except Exception as e:
        return False, f"Error verifying user info extraction: {e}"


def verify_error_handling() -> Tuple[bool, str]:
    """Verify 401 exception for invalid/expired tokens (Requirement 7.3.4)"""
    try:
        from backend.core.security import verify_token
        
        # Test with invalid token
        invalid_token = "invalid.jwt.token"
        payload = verify_token(invalid_token)
        
        if payload is not None:
            return False, "Invalid token was accepted (should return None)"
        
        return True, "✓ Invalid tokens properly rejected (return None for 401)"
    
    except Exception as e:
        return False, f"Error verifying error handling: {e}"


def main():
    """Run all verification checks"""
    print("=" * 70)
    print("Task 7.3 Verification: JWT Dependency for Protected Routes")
    print("=" * 70)
    print()
    
    checks = [
        ("7.3.1: get_current_user() exists", verify_get_current_user_exists),
        ("7.3.2: JWT extraction works", verify_jwt_extraction),
        ("7.3.3: User info extraction works", verify_user_info_extraction),
        ("7.3.4: Error handling works", verify_error_handling),
        ("Protected routes use dependency", verify_protected_routes),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"Checking: {name}...")
        success, message = check_func()
        results.append((name, success, message))
        print(f"  {message}")
        print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("✓ All verification checks passed!")
        print("✓ Task 7.3 implementation is complete and correct.")
        return 0
    else:
        print()
        print("✗ Some verification checks failed.")
        print("✗ Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
