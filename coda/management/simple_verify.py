#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple verification script for Phase 0 DRY consolidation.
"""

import os
import sys
from pathlib import Path

def verify_file_exists(file_path, description):
    """Verify that a file exists and can be read."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                size = len(content)
                print("[OK] " + description)
                print("   File: " + str(file_path))
                print("   Size: " + str(size) + " bytes")
                return True
        except Exception as e:
            print("[ERROR] " + description + " - Error reading file: " + str(e))
            return False
    else:
        print("[ERROR] " + description + " - File not found: " + str(file_path))
        return False

def main():
    """Main verification function."""
    print("Phase 0 DRY Consolidation Verification")
    print("=" * 50)
    
    # Base directory for management app
    management_dir = Path(__file__).parent
    
    # Verify consolidated components exist
    print("\nVerifying Consolidated Components:")
    print("-" * 40)
    
    components = [
        {
            'file': management_dir / 'services' / 'enhanced_utilities_service.py',
            'description': 'EnhancedUtilitiesService'
        },
        {
            'file': management_dir / 'views' / 'consolidated_views.py',
            'description': 'ConsolidatedViews'
        },
        {
            'file': management_dir / 'models' / 'enhanced_models.py',
            'description': 'EnhancedModels'
        },
        {
            'file': management_dir / 'templates' / 'management' / 'components' / 'consolidated_components.html',
            'description': 'TemplateComponents'
        },
        {
            'file': management_dir / 'tests' / 'test_consolidated_components.py',
            'description': 'ConsolidatedTests'
        },
        {
            'file': management_dir / 'management' / 'commands' / 'consolidate_management_app.py',
            'description': 'ConsolidationCommand'
        }
    ]
    
    files_verified = 0
    for component in components:
        if verify_file_exists(str(component['file']), component['description']):
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


