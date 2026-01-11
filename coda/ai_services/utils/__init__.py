"""
AI Services Utilities Package

This package contains utility modules for the ai_services app.

For backward compatibility with existing code that imports from ai_services.utils,
we re-export items from the parent utils.py file.
"""

import os
# Import from parent utils.py file
# The parent ai_services/utils.py file contains all the utilities
import sys

# Get parent directory (ai_services/)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
utils_file_path = os.path.join(parent_dir, "utils.py")

if os.path.exists(utils_file_path):
    # Read and execute the parent utils.py file
    with open(utils_file_path, "r", encoding="utf-8") as f:
        utils_code = f.read()

    # Execute in this module's namespace to re-export everything
    exec(compile(utils_code, utils_file_path, "exec"), globals())
else:
    # Fallback if utils.py doesn't exist
    activity_mapping = {}

    def download_recording(*args, **kwargs):
        return None
