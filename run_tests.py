#!/usr/bin/env python3
import os
import sys
import pytest
import argparse
import coverage
from datetime import datetime
from typing import List, Optional

def setup_test_environment():
    """Set up test environment variables"""
    os.environ['TESTING'] = 'true'
    os.environ['TEST_DB_URL'] = 'sqlite:///:memory:'
    os.environ['TEST_REDIS_URL'] = 'redis://localhost:6379/1'
    os.environ['TEST_JWT_SECRET'] = 'test-secret-key'

def run_tests(
    test_paths: Optional[List[str]] = None,
    verbose: bool = False,
    coverage_report: bool = False,
    junit_report: bool = False,
    html_report: bool = False,
    fail_fast: bool = False
) -> int:
    """Run test suite"""
    # Set up arguments
    args = ['-v'] if verbose else []
    
    if fail_fast:
        args.append('-x')
    
    if junit_report:
        args.extend(['--junitxml', 'test-reports/junit.xml'])
    
    if test_paths:
        args.extend(test_paths)
    else:
        args.append('tests/')

    # Add HTML report after test paths to avoid argument conflict
    if html_report:
        args.append('--html')
        args.append('test-reports/report.html')
    
    # Set up coverage if requested
    if coverage_report:
        cov = coverage.Coverage(
            branch=True,
            source=['.'],
            omit=[
                'tests/*',
                'setup.py',
                'venv/*',
                '.*',
                'get-pip.py',
                'install_dependencies.py',
                'run_tests.py'
            ]
        )
        cov.start()
    
    # Run tests
    result = pytest.main(args)
    
    # Generate coverage report
    if coverage_report:
        cov.stop()
        cov.save()
        
        print("\nCoverage Report:")
        cov.report()
        
        cov.html_report(directory='test-reports/coverage')
        print("\nDetailed coverage report generated in test-reports/coverage/")
    
    return result

def setup_reports_directory():
    """Set up directories for test reports"""
    os.makedirs('test-reports', exist_ok=True)
    os.makedirs('test-reports/coverage', exist_ok=True)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run Terminusa Online test suite'
    )
    
    parser.add_argument(
        'test_paths',
        nargs='*',
        help='Specific test paths to run'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '-j', '--junit',
        action='store_true',
        help='Generate JUnit XML report'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML report'
    )
    
    parser.add_argument(
        '-x', '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Run in CI mode (enables all reports)'
    )
    
    args = parser.parse_args()
    
    # CI mode enables all reports
    if args.ci:
        args.coverage = True
        args.junit = True
        args.html = True
    
    # Set up environment
    setup_test_environment()
    setup_reports_directory()
    
    # Print test run info
    print(f"\nTerminusa Online Test Suite")
    print(f"Run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"pytest version: {pytest.__version__}")
    if args.test_paths:
        print(f"Running tests: {', '.join(args.test_paths)}")
    print("\n" + "="*50 + "\n")
    
    # Run tests
    start_time = datetime.now()
    result = run_tests(
        test_paths=args.test_paths,
        verbose=args.verbose,
        coverage_report=args.coverage,
        junit_report=args.junit,
        html_report=args.html,
        fail_fast=args.fail_fast
    )
    end_time = datetime.now()
    
    # Print summary
    duration = end_time - start_time
    print("\n" + "="*50)
    print(f"\nTest run completed in {duration.total_seconds():.2f} seconds")
    print(f"Result: {'PASSED' if result == 0 else 'FAILED'}")
    
    if args.coverage:
        print("\nCoverage reports generated in test-reports/coverage/")
    if args.junit:
        print("JUnit report generated in test-reports/junit.xml")
    if args.html:
        print("HTML report generated in test-reports/report.html")
    
    return result

if __name__ == '__main__':
    sys.exit(main())
