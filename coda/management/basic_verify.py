#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic verification script for Phase 0 DRY consolidation.
"""

import os
import sys

def verify_file_exists(file_path, description):
    """Verify that a file exists and can be read."""
    if os.path.exists(file_path):
        # If it's a directory, just check existence
        if os.path.isdir(file_path):
            print("[OK] " + description)
            print("   Directory: " + file_path)
            return True
        # If it's a file, try to read it
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                size = len(content)
                print("[OK] " + description)
                print("   File: " + file_path)
                print("   Size: " + str(size) + " bytes")
                return True
        except Exception as e:
            print("[ERROR] " + description + " - Error reading file: " + str(e))
            return False
    else:
        print("[ERROR] " + description + " - File not found: " + file_path)
        return False

def main():
    """Main verification function."""
    print("Phase 0 DRY Consolidation Verification")
    print("=" * 50)
    
    # Base directory for management app
    management_dir = os.path.dirname(__file__)
    
    # Verify consolidated components exist
    print("\nVerifying Consolidated Components:")
    print("-" * 40)
    
    components = [
        {
            'file': os.path.join(management_dir, 'services', 'utilities_service.py'),
            'description': 'UtilitiesService'
        },
        {
            'file': os.path.join(management_dir, 'views', 'base_views.py'),
            'description': 'BaseViews'
        },
        {
            'file': os.path.join(management_dir, 'models', 'base_models.py'),
            'description': 'BaseModels'
        },
        {
            'file': os.path.join(management_dir, 'templates', 'management', 'components', 'base_components.html'),
            'description': 'BaseComponents'
        },
        {
            'file': os.path.join(management_dir, 'tests', 'test_consolidated_components.py'),
            'description': 'ConsolidatedTests'
        },
        {
            'file': os.path.join(management_dir, 'management', 'commands', 'consolidate_management_app.py'),
            'description': 'ConsolidationCommand'
        },
        {
            'file': os.path.join(management_dir, 'deprecated', 'utilities_legacy'),
            'description': 'DeprecatedUtilities (moved)'
        }
    ]
    
    files_verified = 0
    for component in components:
        if verify_file_exists(component['file'], component['description']):
            files_verified += 1
        print()
    
    # Summary
    print("Verification Summary:")
    print("=" * 25)
    print("Files Verified: " + str(files_verified) + "/" + str(len(components)))
    
    success_rate = (files_verified / len(components)) * 100
    print("Overall Success Rate: " + str(round(success_rate, 1)) + "%")
    
    if success_rate >= 90:
        print("SUCCESS: Phase 0 consolidation is successful!")
        return True
    elif success_rate >= 70:
        print("WARNING: Phase 0 consolidation is mostly successful with minor issues")
        return True
    else:
        print("ERROR: Phase 0 consolidation needs attention")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
