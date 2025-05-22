import requests
from typing import Dict, List, Any
import sys
from pathlib import Path
import json
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.test_base import BaseEndpointTester

class IndustryGetEndpointTester(BaseEndpointTester):
    def __init__(self, base_url: str = "http://localhost:8002"):
        super().__init__(base_url=base_url, endpoint="industry")
        # Override the tokens path to use the one from tests directory
        self.tokens = self._load_tokens()

    def _load_tokens(self) -> Dict[str, str]:
        """Load authentication tokens from the tokens file"""
        tokens_file = Path(__file__).parent.parent.parent / "test_tokens.json"
        if not tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found at {tokens_file}")
        
        with open(tokens_file, 'r') as f:
            return json.load(f)

    def get_results_directory(self) -> str:
        """Get the directory for storing test results"""
        # Get the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to industry directory, then into results
        results_dir = os.path.join(os.path.dirname(current_dir), "results")
        # Create directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def test_endpoint(self, role: str) -> bool:
        """Test the industry GET endpoint with a specific role"""
        test_name = f"Industry GET - {role} role"
        
        try:
            # Get token for the role
            token = self.tokens.get(role)
            if not token:
                self.log_test_result(test_name, "ERROR", {
                    "error": f"No token available for {role} role"
                })
                return False

            # Make request to GET endpoint
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/v1/industry",
                headers=headers
            )
            
            # Validate response
            validation_results = self.validate_get_response(response.json(), role)
            
            # Log test result
            self.log_test_result(test_name, "PASS" if validation_results["is_valid"] else "FAIL", {
                "status_code": response.status_code,
                "response": response.json(),
                "validation_results": validation_results
            })
            
            return validation_results["is_valid"]
            
        except Exception as e:
            self.log_test_result(test_name, "ERROR", {
                "error": str(e)
            })
            return False

    def validate_get_response(self, response_data: List[Dict[str, Any]], role: str) -> Dict[str, Any]:
        """Validate the industry GET endpoint response"""
        errors = []
        warnings = []
        
        # Check if response is a list
        if not isinstance(response_data, list):
            errors.append("Response is not a list")
            return {"is_valid": False, "errors": errors, "warnings": warnings}
        
        # Validate each industry in the response
        for industry in response_data:
            industry_errors = self.validate_industry_data(industry)
            errors.extend(industry_errors)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_industry_data(self, industry: Dict[str, Any]) -> List[str]:
        """Validate a single industry's data structure"""
        errors = []
        
        # Required fields for an industry
        required_fields = [
            "id",
            "name",
            "created_by",
            "created_date"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in industry:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        if "id" in industry and not isinstance(industry["id"], str):
            errors.append("Invalid id type")
        
        if "name" in industry and not isinstance(industry["name"], str):
            errors.append("Invalid name type")
        
        if "created_by" in industry and not isinstance(industry["created_by"], str):
            errors.append("Invalid created_by type")
        
        if "created_date" in industry and not isinstance(industry["created_date"], str):
            errors.append("Invalid created_date type")
        
        return errors

if __name__ == "__main__":
    # Create tester instance
    tester = IndustryGetEndpointTester()
    
    # Run all tests
    success = tester.run_all_tests()
    
    # Exit with appropriate status code
    exit(0 if success else 1)