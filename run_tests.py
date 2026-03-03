# run_tests.py
import os
import sys
import subprocess

def run_tests():
    """Run all tests"""
    print("🚀 Running Community Tests...")
    print("=" * 50)
    
    # Run unit tests
    print("\n📦 UNIT TESTS:")
    result = subprocess.run([
        'python', 'manage.py', 'test', 
        'communities.tests.unit', '--verbosity=2'
    ])
    
    if result.returncode != 0:
        print("❌ Unit tests failed!")
        return result.returncode
    
    # Run integration tests
    print("\n🔄 INTEGRATION TESTS:")
    result = subprocess.run([
        'python', 'manage.py', 'test',
        'communities.tests.integration', '--verbosity=2'
    ])
    
    if result.returncode != 0:
        print("❌ Integration tests failed!")
        return result.returncode
    
    # Run performance tests (optional)
    print("\n⚡ PERFORMANCE TESTS:")
    result = subprocess.run([
        'python', 'manage.py', 'test',
        'communities.tests.performance', '--verbosity=1'
    ])
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    return 0

if __name__ == '__main__':
    sys.exit(run_tests())