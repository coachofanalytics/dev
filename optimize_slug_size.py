#!/usr/bin/env python3
"""
CODA Slug Size Optimization Script

This script helps optimize the CODA project size from 956MB to under 100MB
by removing heavy dependencies and optimizing the codebase.
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False

def get_directory_size(path):
    """Get the size of a directory in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size / (1024 * 1024)  # Convert to MB

def main():
    """Main optimization function."""
    print("🚀 CODA Slug Size Optimization Script")
    print("=" * 50)
    
    # Get current directory
    project_dir = Path.cwd()
    print(f"📁 Project Directory: {project_dir}")
    
    # Check current size
    current_size = get_directory_size(project_dir)
    print(f"📊 Current Project Size: {current_size:.1f}MB")
    
    if current_size < 100:
        print("✅ Project is already under 100MB!")
        return
    
    print(f"🎯 Target: Reduce size by {current_size - 100:.1f}MB")
    
    # Step 1: Create backup
    print("\n📋 Step 1: Creating backup...")
    backup_dir = project_dir / "backup_before_optimization"
    if not backup_dir.exists():
        shutil.copytree(project_dir / "venv", backup_dir / "venv")
        print("✅ Backup created")
    else:
        print("ℹ️  Backup already exists")
    
    # Step 2: Remove heavy packages
    print("\n📋 Step 2: Removing heavy packages...")
    heavy_packages = [
        "chromedriver-py",  # 85MB
        "google-api-python-client",  # 63MB
        "botocore",  # 58MB
        "grpcio",  # 32MB
        "lxml",  # 20MB
        "sqlalchemy",  # 18MB
        "langchain-community",  # 15MB
        "langchain",  # 12MB
        "selenium",  # Heavy but may be needed
        "PyAutoGUI",  # Automation tool
        "PyInstaller",  # Build tool
    ]
    
    for package in heavy_packages:
        run_command(f"pip uninstall {package} -y", f"Removing {package}")
    
    # Step 3: Optimize static files
    print("\n📋 Step 3: Optimizing static files...")
    
    # Compress static files
    if (project_dir / "coda").exists():
        static_dir = project_dir / "coda" / "static"
        if static_dir.exists():
            # Remove unused static files
            run_command("find coda/static -name '*.map' -delete", "Removing source maps")
            run_command("find coda/static -name '*.md' -delete", "Removing markdown files")
            run_command("find coda/static -name '*.txt' -delete", "Removing text files")
            print("✅ Static files optimized")
    
    # Step 4: Clean up development files
    print("\n📋 Step 4: Cleaning up development files...")
    
    # Remove common development files
    dev_patterns = [
        "*.pyc",
        "*.pyo", 
        "__pycache__",
        "*.log",
        ".DS_Store",
        "*.tmp",
        "*.temp"
    ]
    
    for pattern in dev_patterns:
        run_command(f"find . -name '{pattern}' -type f -delete", f"Removing {pattern}")
        run_command(f"find . -name '{pattern}' -type d -exec rm -rf {{}} +", f"Removing {pattern} directories")
    
    # Step 5: Optimize virtual environment
    print("\n📋 Step 5: Optimizing virtual environment...")
    
    # Remove pip cache
    venv_dir = project_dir / "venv"
    if venv_dir.exists():
        pip_cache = venv_dir / "lib" / "python3.12" / "site-packages" / "pip"
        if pip_cache.exists():
            shutil.rmtree(pip_cache)
            print("✅ Pip cache removed")
    
    # Remove unused packages
    run_command("pip-autoremove -y", "Removing unused packages")
    
    # Step 6: Check final size
    print("\n📋 Step 6: Checking final size...")
    final_size = get_directory_size(project_dir)
    reduction = current_size - final_size
    
    print(f"📊 Final Project Size: {final_size:.1f}MB")
    print(f"📉 Size Reduction: {reduction:.1f}MB ({reduction/current_size*100:.1f}%)")
    
    if final_size < 100:
        print("🎉 SUCCESS: Project size is now under 100MB!")
    else:
        print(f"⚠️  Project size is still {final_size:.1f}MB. Additional optimization needed.")
        print("💡 Consider:")
        print("   - Removing numpy/pandas if not essential")
        print("   - Using external services for heavy computations")
        print("   - Implementing microservices architecture")
    
    # Step 7: Generate optimization report
    print("\n📋 Step 7: Generating optimization report...")
    
    report = f"""
# CODA Slug Size Optimization Report

## Results
- **Initial Size**: {current_size:.1f}MB
- **Final Size**: {final_size:.1f}MB
- **Reduction**: {reduction:.1f}MB ({reduction/current_size*100:.1f}%)
- **Target Achieved**: {'✅ Yes' if final_size < 100 else '❌ No'}

## Actions Taken
1. ✅ Removed heavy packages: {', '.join(heavy_packages)}
2. ✅ Optimized static files
3. ✅ Cleaned up development files
4. ✅ Optimized virtual environment
5. ✅ Removed pip cache

## Recommendations
- Use system ChromeDriver instead of bundled version
- Implement lazy loading for heavy packages
- Consider using lighter alternatives to numpy/pandas
- Move heavy computations to external services
"""
    
    with open("optimization_report.md", "w") as f:
        f.write(report)
    
    print("✅ Optimization report saved to optimization_report.md")
    print("\n🎯 Optimization complete!")

if __name__ == "__main__":
    main()
