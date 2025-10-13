#!/usr/bin/env python3
"""
CODA Development Environment Setup Script

This script helps set up the development environment for the CODA platform.
Run this script to verify your environment and get setup recommendations.

Usage:
    python setup_development_environment.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def check_python_version():
    """Check Python version"""
    print_header("Python Version Check")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False


def check_pip():
    """Check if pip is available"""
    print_header("Pip Check")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Pip is available")
            return True
        else:
            print_error("Pip is not available")
            return False
    except Exception as e:
        print_error(f"Error checking pip: {e}")
        return False


def check_virtual_environment():
    """Check if we're in a virtual environment"""
    print_header("Virtual Environment Check")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Virtual environment detected")
        return True
    else:
        print_warning("Not in a virtual environment")
        print_info("Consider creating one: python -m venv venv")
        return False


def check_django():
    """Check Django installation"""
    print_header("Django Check")
    
    try:
        import django
        version = django.get_version()
        print_success(f"Django {version} - OK")
        return True
    except ImportError:
        print_error("Django not installed")
        print_info("Install with: pip install django")
        return False


def check_requirements():
    """Check if requirements.txt exists and dependencies are installed"""
    print_header("Requirements Check")
    
    project_root = Path(__file__).parent.parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if requirements_file.exists():
        print_success("requirements.txt found")
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            missing_packages = []
            for req in requirements:
                if req.strip() and not req.startswith('#'):
                    package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                    try:
                        __import__(package_name.replace('-', '_'))
                    except ImportError:
                        missing_packages.append(req.strip())
            
            if missing_packages:
                print_warning(f"Missing packages: {', '.join(missing_packages)}")
                print_info("Install with: pip install -r requirements.txt")
                return False
            else:
                print_success("All requirements satisfied")
                return True
                
        except Exception as e:
            print_error(f"Error checking requirements: {e}")
            return False
    else:
        print_error("requirements.txt not found")
        return False


def check_database():
    """Check database configuration"""
    print_header("Database Check")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
        import django
        django.setup()
        
        from django.db import connection
        connection.ensure_connection()
        print_success("Database connection successful")
        return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("Run migrations: python manage.py migrate")
        return False


def check_manage_py():
    """Check if manage.py exists"""
    print_header("Django Project Check")
    
    project_root = Path(__file__).parent.parent.parent
    manage_py = project_root / "manage.py"
    
    if manage_py.exists():
        print_success("manage.py found")
        return True
    else:
        print_error("manage.py not found - not a Django project")
        return False


def check_git():
    """Check Git configuration"""
    print_header("Git Check")
    
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Git is available")
            
            # Check if we're in a git repository
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                print_success("Git repository detected")
                return True
            else:
                print_warning("Not in a git repository")
                return False
        else:
            print_error("Git not available")
            return False
    except Exception as e:
        print_error(f"Error checking git: {e}")
        return False


def check_cursor_ai():
    """Check Cursor AI installation (if possible)"""
    print_header("Cursor AI Check")
    
    # This is a placeholder - we can't actually check if Cursor AI is installed
    # from a Python script, but we can provide guidance
    print_info("Cursor AI installation check not available from Python")
    print_info("Please verify Cursor AI is installed manually")
    print_info("Download from: https://cursor.sh/")
    return True


def generate_setup_commands():
    """Generate setup commands based on checks"""
    print_header("Setup Commands")
    
    commands = []
    
    # Virtual environment
    if not check_virtual_environment():
        commands.append("python -m venv venv")
        commands.append("source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    
    # Install requirements
    commands.append("pip install -r requirements.txt")
    
    # Database setup
    commands.append("python manage.py makemigrations")
    commands.append("python manage.py migrate")
    
    # Create superuser
    commands.append("python manage.py createsuperuser")
    
    # Run server
    commands.append("python manage.py runserver")
    
    print("Run these commands to complete setup:")
    for i, cmd in enumerate(commands, 1):
        print(f"{i:2d}. {cmd}")


def main():
    """Main setup check function"""
    print_header("CODA Development Environment Setup")
    print("This script will check your development environment setup.")
    print("Follow the recommendations to ensure a smooth development experience.")
    
    checks = [
        check_python_version,
        check_pip,
        check_virtual_environment,
        check_manage_py,
        check_django,
        check_requirements,
        check_database,
        check_git,
        check_cursor_ai,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print_error(f"Check failed: {e}")
            results.append(False)
    
    # Summary
    print_header("Setup Summary")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print_success(f"All checks passed ({passed}/{total})")
        print_success("Your development environment is ready!")
    else:
        print_warning(f"Some checks failed ({passed}/{total})")
        print_info("Please address the issues above before starting development")
    
    # Generate setup commands
    generate_setup_commands()
    
    # Next steps
    print_header("Next Steps")
    print("1. Read the Cursor AI Guide: docs/01_GETTING_STARTED/Cursor_AI_Guide.md")
    print("2. Follow the development workflow")
    print("3. Start with a simple feature implementation")
    print("4. Use AI assistance for development")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Happy coding with CODA! 🚀{Colors.END}")


if __name__ == "__main__":
    main()
