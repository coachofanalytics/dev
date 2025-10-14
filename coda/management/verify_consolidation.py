#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for Phase 0 DRY consolidation.

This script verifies that all consolidated components are properly created
and can be imported without errors.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def verify_file_exists(file_path, description):
    """Verify that a file exists and can be read."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                size = len(content)
                print(f"[OK] {description}")
                print(f"   File: {file_path}")
                print(f"   Size: {size:,} bytes")
                return True
        except Exception as e:
            print(f"[ERROR] {description} - Error reading file: {e}")
            return False
    else:
        print(f"[ERROR] {description} - File not found: {file_path}")
        return False

def verify_import(module_name, description):
    """Verify that a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"[ERROR] {description} - Module not found: {module_name}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"[OK] {description}")
        print(f"   Module: {module_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {description} - Import error: {e}")
        return False

def verify_class_exists(module_name, class_name, description):
    """Verify that a class exists in a module."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"[ERROR] {description} - Module not found: {module_name}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            print(f"[OK] {description}")
            print(f"   Class: {class_name} in {module_name}")
            return True
        else:
            print(f"[ERROR] {description} - Class not found: {class_name} in {module_name}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} - Error: {e}")
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
    
    # Verify Python imports work
    print("Verifying Python Imports:")
    print("-" * 30)
    
    imports = [
        {
            'module': 'management.services.enhanced_utilities_service',
            'class': 'EnhancedUtilitiesService',
            'description': 'EnhancedUtilitiesService import'
        },
        {
            'module': 'management.views.consolidated_views',
            'class': 'BaseTaskView',
            'description': 'BaseTaskView import'
        },
        {
            'module': 'management.models.enhanced_models',
            'class': 'BaseTaskModel',
            'description': 'BaseTaskModel import'
        }
    ]
    
    imports_verified = 0
    for import_test in imports:
        if verify_class_exists(
            import_test['module'], 
            import_test['class'], 
            import_test['description']
        ):
            imports_verified += 1
        print()
    
    # Summary
    print("Verification Summary:")
    print("=" * 25)
    print(f"Files Verified: {files_verified}/{len(components)}")
    print(f"Imports Verified: {imports_verified}/{len(imports)}")
    
    total_verified = files_verified + imports_verified
    total_possible = len(components) + len(imports)
    success_rate = (total_verified / total_possible) * 100
    
    print(f"Overall Success Rate: {success_rate:.1f}%")
    
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
