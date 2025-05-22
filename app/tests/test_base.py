import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from app
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.authenticator.jwt_token import get_test_tokens
from app.core.logger import setup_logger

# Set up logger
logger = setup_logger(__name__)

class BaseEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8002", endpoint: str = ""):
        self.base_url = base_url
        self.endpoint = endpoint
        self.test_results = []
        self.test_type = endpoint.replace("/", "_")  # Convert endpoint to test type
        self.tokens = self.load_or_generate_tokens()

    def get_tokens_file_path(self) -> str:
        """Get the path to the tokens file"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "test_tokens.json")

    def save_tokens(self, tokens: dict):
        """Save tokens to a file"""
        filepath = self.get_tokens_file_path()
        try:
            with open(filepath, 'w') as f:
                json.dump(tokens, f, indent=2)
            logger.info(f"Tokens saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving tokens: {str(e)}")

    def load_tokens(self) -> dict:
        """Load tokens from file"""
        filepath = self.get_tokens_file_path()
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    tokens = json.load(f)
                logger.info(f"Tokens loaded from {filepath}")
                return tokens
        except Exception as e:
            logger.error(f"Error loading tokens: {str(e)}")
        return None

    def load_or_generate_tokens(self) -> dict:
        """Load tokens from file or generate new ones if not available"""
        tokens = self.load_tokens()
        if tokens:
            return tokens
        
        # Generate new tokens if not found
        tokens = get_test_tokens(expiry_days=360)
        self.save_tokens(tokens)
        return tokens

    def get_endpoint_type(self) -> str:
        """Get the type of endpoint (GET, POST, PUT, DELETE) from the class name"""
        class_name = self.__class__.__name__.lower()
        if 'get' in class_name:
            return 'get'
        elif 'post' in class_name:
            return 'post'
        elif 'put' in class_name:
            return 'put'
        elif 'delete' in class_name:
            return 'delete'
        return 'unknown'

    def get_results_directory(self) -> str:
        """Get the appropriate directory for test results based on test type"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Use the project's results directory with endpoint type subdirectory
        endpoint_type = self.get_endpoint_type()
        results_dir = os.path.join(current_dir, "project", "results", endpoint_type)
        
        # Create directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def log_test_result(self, test_name: str, status: str, details: dict):
        """Log test results with timestamp"""
        # Extract role from test name
        role = test_name.split(" - ")[-1].replace(" role", "")
        
        # Structure the test result
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_name": test_name,
                "role": role,
                "status": status
            },
            "summary": {
                "status_code": details.get("status_code"),
                "records_count": details.get("records_count", 0),
                "validation_status": details.get("validation_results", {}).get("is_valid", False)
            },
            "validation_details": {
                "errors": details.get("validation_results", {}).get("errors", []),
                "warnings": details.get("validation_results", {}).get("warnings", [])
            },
            "response_data": {
                "sample": details.get("response", [])[:2] if isinstance(details.get("response"), list) else details.get("response"),
                "total_records": len(details.get("response", [])) if isinstance(details.get("response"), list) else 0
            }
        }
        
        self.test_results.append(result)
        
        # Log the result
        logger.info(f"\n=== Test Result: {test_name} ===")
        logger.info(f"Status: {status}")
        logger.info(f"Records Count: {result['summary']['records_count']}")
        if result['validation_details']['errors']:
            logger.info(f"Errors: {len(result['validation_details']['errors'])}")
        if result['validation_details']['warnings']:
            logger.info(f"Warnings: {len(result['validation_details']['warnings'])}")

    def generate_summary_report(self) -> str:
        """Generate a summary report from test results"""
        if not self.test_results:
            return "No test results available."

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["metadata"]["status"] == "PASS")
        failed_tests = sum(1 for r in self.test_results if r["metadata"]["status"] == "FAIL")
        error_tests = sum(1 for r in self.test_results if r["metadata"]["status"] == "ERROR")
        
        # Group results by role
        role_results = {}
        for result in self.test_results:
            role = result["metadata"]["role"]
            if role not in role_results:
                role_results[role] = {
                    "PASS": 0, 
                    "FAIL": 0, 
                    "ERROR": 0,
                    "total_records": 0,
                    "validation_errors": [],
                    "warnings": []
                }
            
            # Update counts
            role_results[role][result["metadata"]["status"]] += 1
            role_results[role]["total_records"] = result["summary"]["records_count"]
            
            # Collect validation errors and warnings
            if result["validation_details"]["errors"]:
                role_results[role]["validation_errors"].extend(result["validation_details"]["errors"])
            if result["validation_details"]["warnings"]:
                role_results[role]["warnings"].extend(result["validation_details"]["warnings"])

        # Generate report
        report = [
            "\n=== Test Summary Report ===",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nOverall Statistics:",
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Errors: {error_tests}",
            f"Success Rate: {(passed_tests/total_tests)*100:.1f}%",
            f"\nResults by Role:"
        ]

        for role, data in role_results.items():
            report.append(f"\n{role.upper()}:")
            report.append(f"  Passed: {data['PASS']}")
            report.append(f"  Failed: {data['FAIL']}")
            report.append(f"  Errors: {data['ERROR']}")
            report.append(f"  Total Records: {data['total_records']}")
            
            if data["validation_errors"]:
                report.append(f"  Validation Errors:")
                for error in data["validation_errors"]:
                    report.append(f"    - {error}")
            
            if data["warnings"]:
                report.append(f"  Warnings:")
                for warning in data["warnings"]:
                    report.append(f"    - {warning}")

        return "\n".join(report)

    def save_results(self, append: bool = False):
        """Save test results to a JSON file with organization by test type"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = self.get_results_directory()
        
        # Include endpoint name and type in filename
        endpoint_name = self.endpoint.replace("/", "_")
        endpoint_type = self.get_endpoint_type()
        
        if append:
            # Find the most recent results file for this endpoint
            existing_files = [f for f in os.listdir(results_dir) if f.endswith('.json') and f.startswith(f'test_results_{endpoint_name}_{endpoint_type}')]
            if existing_files:
                latest_file = max(existing_files)
                filepath = os.path.join(results_dir, latest_file)
                
                # Read existing results
                try:
                    with open(filepath, 'r') as f:
                        existing_results = json.load(f)
                    self.test_results = existing_results + self.test_results
                    filename = latest_file
                except Exception as e:
                    logger.error(f"Error reading existing results: {str(e)}")
                    filename = f"test_results_{endpoint_name}_{endpoint_type}_{timestamp}.json"
            else:
                filename = f"test_results_{endpoint_name}_{endpoint_type}_{timestamp}.json"
        else:
            filename = f"test_results_{endpoint_name}_{endpoint_type}_{timestamp}.json"
        
        filepath = os.path.join(results_dir, filename)
        
        # Structure the results file
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "endpoint": self.endpoint,
                "endpoint_type": endpoint_type,
                "total_tests": len(self.test_results)
            },
            "summary": {
                "passed": sum(1 for r in self.test_results if r["metadata"]["status"] == "PASS"),
                "failed": sum(1 for r in self.test_results if r["metadata"]["status"] == "FAIL"),
                "errors": sum(1 for r in self.test_results if r["metadata"]["status"] == "ERROR")
            },
            "results": self.test_results
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            logger.info(f"\n=== Test Results Saved ===")
            logger.info(f"File: {filename}")
            logger.info(f"Location: {filepath}")
            logger.info(f"Number of test results: {len(self.test_results)}")
            logger.info(f"Passed: {results_data['summary']['passed']}")
            logger.info(f"Failed: {results_data['summary']['failed']}")
            logger.info(f"Errors: {results_data['summary']['errors']}")
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"File size: {file_size} bytes")
            else:
                logger.error("File was not created successfully")
                
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")
            logger.error(f"Attempted to save to: {filepath}")

    def save_summary_report(self):
        """Save the summary report to a text file"""
        report = self.generate_summary_report()
        results_dir = self.get_results_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        endpoint_name = self.endpoint.replace("/", "_")
        endpoint_type = self.get_endpoint_type()
        filename = f"summary_report_{endpoint_name}_{endpoint_type}_{timestamp}.txt"
        filepath = os.path.join(results_dir, filename)

        try:
            with open(filepath, 'w') as f:
                f.write(report)
            logger.info(f"\nSummary report saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save summary report: {str(e)}")

    def run_all_tests(self, append_results: bool = False) -> bool:
        """Run tests for all roles"""
        roles = ["admin", "user", "viewer", "assessment", "multi_role"]
        all_passed = True
        
        for role in roles:
            if not self.test_endpoint(role):
                all_passed = False
        
        # Save results and generate report
        self.save_results(append=append_results)
        self.save_summary_report()
        
        return all_passed

    def test_endpoint(self, role: str) -> bool:
        """Test the endpoint with a specific role - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement test_endpoint method")

    def validate_response(self, response_data: List[Dict[str, Any]], role: str) -> Dict[str, Any]:
        """Validate the response data - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement validate_response method") 