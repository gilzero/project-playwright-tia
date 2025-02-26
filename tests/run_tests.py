#!/usr/bin/env python3
# tests/run_tests.py
"""
Test runner script for the TechInAsia scraper.
This script discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

# Add the parent directory to the path so that app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Discover and run all tests in the tests directory."""
    # Discover all tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return the number of failures and errors
    return len(result.failures) + len(result.errors)

if __name__ == '__main__':
    print("Running TechInAsia scraper tests...")
    exit_code = run_tests()
    print("Tests completed.")
    sys.exit(exit_code) 