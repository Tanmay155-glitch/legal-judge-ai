"""
Test Runner - Execute all tests with proper configuration
"""

import sys
import subprocess


def run_unit_tests():
    """Run unit tests"""
    print("\n" + "="*80)
    print("RUNNING UNIT TESTS")
    print("="*80 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_models.py",
        "tests/test_embedding.py",
        "tests/test_vector_index.py",
        "-v", "--tb=short"
    ])
    
    return result.returncode == 0


def run_property_tests():
    """Run property-based tests"""
    print("\n" + "="*80)
    print("RUNNING PROPERTY-BASED TESTS")
    print("="*80 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_api_properties.py",
        "-v", "--tb=short",
        "--hypothesis-show-statistics"
    ])
    
    return result.returncode == 0


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "="*80)
    print("RUNNING INTEGRATION TESTS")
    print("="*80 + "\n")
    print("NOTE: Integration tests require services to be running")
    print("Start services with: python main.py")
    print("="*80 + "\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_integration.py",
        "-v", "--tb=short",
        "-m", "integration"
    ])
    
    return result.returncode == 0


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("LEGAL LLM SYSTEM - TEST SUITE")
    print("="*80)
    
    results = {
        "Unit Tests": run_unit_tests(),
        "Property Tests": run_property_tests(),
        "Integration Tests": run_integration_tests()
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_type, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_type}: {status}")
    
    print("="*80 + "\n")
    
    # Exit with error if any tests failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
