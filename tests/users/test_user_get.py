import requests
from typing import Dict, List, Any
import sys
from pathlib import Path
import json
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.test_base import BaseEndpointTester

class UserGetEndpointTester(BaseEndpointTester):
    def __init__(self, base_url: str = "http://localhost:8002"):
        super().__init__(base_url=base_url, endpoint="users")

    def test_endpoint(self, limit: int = 10) -> bool:
        """Test the users GET endpoint with a specific limit"""
        test_name = f"Users GET - limit {limit}"

        try:
            # Make request to GET endpoint
            response = requests.get(f"{self.base_url}/users/?limit={limit}")

            # Validate response
            validation_results = self.validate_get_response(response.json(), limit)

            # Log test result
            self.log_test_result(
                test_name,
                "PASS" if validation_results["is_valid"] else "FAIL",
                {
                    "status_code": response.status_code,
                    "response": response.json(),
                    "validation_results": validation_results,
                },
            )

            return validation_results["is_valid"]

        except Exception as e:
            self.log_test_result(test_name, "ERROR", {"error": str(e)})
            return False

    def validate_get_response(
        self, response_data: List[Dict[str, Any]], limit: int
    ) -> Dict[str, Any]:
        """Validate the users GET endpoint response"""
        errors = []
        warnings = []

        # Check if response is a list
        if not isinstance(response_data, list):
            errors.append("Response is not a list")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        # Check if the number of results matches the limit
        if len(response_data) > limit:
            errors.append(f"Response contains more items than limit ({limit})")

        # Validate each user in the response
        for user in response_data:
            user_errors = self.validate_user_data(user)
            errors.extend(user_errors)

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def validate_user_data(self, user: Dict[str, Any]) -> List[str]:
        """Validate a single user's data structure"""
        errors = []

        # Required fields for a user
        required_fields = ["id", "username", "first_name", "last_name", "email", "phone"]

        # Check required fields
        for field in required_fields:
            if field not in user:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        if "id" in user and not isinstance(user["id"], str):
            errors.append("Invalid id type")

        if "username" in user and not isinstance(user["username"], str):
            errors.append("Invalid username type")

        if "first_name" in user and not isinstance(user["first_name"], str):
            errors.append("Invalid first_name type")

        if "last_name" in user and not isinstance(user["last_name"], str):
            errors.append("Invalid last_name type")

        if "email" in user and not isinstance(user["email"], str):
            errors.append("Invalid email type")

        if "phone" in user and not isinstance(user["phone"], str):
            errors.append("Invalid phone type")

        return errors

def run_tests():
    """Run all user endpoint tests"""
    tester = UserGetEndpointTester()
    
    # Test with different limits
    test_cases = [5, 10, 20]
    all_passed = True
    
    for limit in test_cases:
        if not tester.test_endpoint(limit):
            all_passed = False
            print(f"Test failed for limit={limit}")
        else:
            print(f"Test passed for limit={limit}")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
