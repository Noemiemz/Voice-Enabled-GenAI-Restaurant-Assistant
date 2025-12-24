"""
Test runner for the agent system integration tests
"""

import sys
import os
import unittest

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test modules
from test_agent_integration import TestAgentIntegration
from test_audio_agents import TestAudioAgentIntegration


def run_all_tests():
    """Run all tests and report results"""
    
    print("=" * 60)
    print("AGENT SYSTEM INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAgentIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioAgentIntegration))
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.wasSuccessful():
        print("\n[OK] ALL TESTS PASSED!")
        return 0
    else:
        print("\n[ERROR] SOME TESTS FAILED!")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
                
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
        
        return 1


if __name__ == '__main__':
    # Run tests and exit with appropriate code
    exit_code = run_all_tests()
    sys.exit(exit_code)