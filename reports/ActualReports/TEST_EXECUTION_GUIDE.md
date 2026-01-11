# Test Execution & Reporting Guide

This document provides a comprehensive guide on how to execute the various test suites within the `tests/` directory of the Biashara Bridges project. It details the commands for each test category, how to interpret the execution, and how to generate reports.

## Prerequisites
Ensure your Python virtual environment is activated before running any commands.
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

## Test Commands by Category

The project is organized into specific test folders. You can run these tests individually or as a whole using `pytest`.

### 1. Unit Tests
**Location**: `tests/unit/`
**Purpose**: Verify individual components (functions, classes, methods) in isolation without external dependencies like databases or APIs.

**Run Command**:
```bash
pytest tests/unit
```

**Generate Result File**:
```bash
pytest tests/unit > reports/unit_test_results.txt
```

### 2. Performance Tests
**Location**: `tests/performance/`
**Purpose**: Assess system responsiveness, stability, and resource usage under simulated load.

**Run Command**:
```bash
pytest tests/performance
```

**Generate Result File**:
```bash
pytest tests/performance > reports/performance_test_results.txt
```

### 3. Regression Tests
**Location**: `tests/regression/`
**Purpose**: Ensure that recent code changes have not negatively impacted or "broken" existing features.

**Run Command**:
```bash
pytest tests/regression
```

**Generate Result File**:
```bash
pytest tests/regression > reports/regression_test_results.txt
```

### 4. Integration Tests
**Location**: `tests/integration/`
**Purpose**: Verify that different modules, services, and the database work together correctly as a group.

**Run Command**:
```bash
pytest tests/integration
```

**Generate Result File**:
```bash
pytest tests/integration > reports/integration_test_results.txt
```

### 5. Architecture Tests
**Location**: `tests/architecture/`
**Purpose**: Enforce architectural patterns, circular dependency checks, and code structure rules.

**Run Command**:
```bash
pytest tests/architecture
```

**Generate Result File**:
```bash
pytest tests/architecture > reports/architecture_test_results.txt
```

### 6. Security Tests
**Location**: `tests/security/`
**Purpose**: Identify vulnerabilities, validate permission logic, and ensure security best practices (OWASP) are enforced.

**Run Command**:
```bash
pytest tests/security
```

**Generate Result File**:
```bash
pytest tests/security > reports/security_test_results.txt
```

---

## How Reports are Generated

### 1. Capturing Raw Test Results
The commands above use the `>` operator to redirect the standard output of the test runner into a text file.
- **Process**: The test runner executes the code and outputs pass/fail status to the console.
- **Capture**: `> reports/filename.txt` captures this stream and saves it.
- **Content**: The resulting file contains the execution log, including:
  - Passed tests (indicated by `.`)
  - Failed tests (indicated by `F` usually with detailed tracebacks)
  - Skipped tests (indicated by `s`)
  - Warnings and Errors

### 2. Generating Code Coverage Reports
To understand how much of the application code is covered by tests, you can use the `pytest-cov` plugin which is capturing execution data.

**Console Report:**
```bash
pytest --cov=. tests/
```

**HTML Report (Interactive):**
```bash
pytest --cov=. --cov-report=html tests/
```
*This creates a `htmlcov/` directory. Open `htmlcov/index.html` in your browser to inspect line-by-line coverage.*

### 3. Creating Audit Reports
The structured Markdown files found in this `reports/` folder (e.g., `SECURITY_TEST_AUDIT_REPORT.md`) are analytical documents.
- **Input**: They are derived from the raw text files generated in step 1.
- **Creation**: These are typically compiled by analyzing the raw results, classifying failures, and adding business context (Risks, Impact, Remediation).

The unit test failures are not caused by incorrect test logic but by an architectural inconsistency in user profile creation. Multiple components assume automatic profile existence, which is not consistently enforced by the system. This represents a critical functional and compliance risk 
