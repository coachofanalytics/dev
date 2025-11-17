# Test Documentation

This directory (`main/test`) contains a comprehensive suite of tests for the `main` application, organized into three main categories: Integration, Performance, and Regression tests.

## Directory Structure

- `intergration/`: Contains integration tests that verify the interaction between different components of the application (e.g., models, views, forms, templates, URLs).
- `performance/`: Contains performance tests designed to measure the efficiency and scalability of key operations, such as bulk data creation, updates, and complex queryset executions.
- `regression/`: Contains regression tests to ensure that existing functionalities continue to work as expected after changes or updates to the codebase. These tests focus on maintaining consistent behavior of models, forms, and views over time.
- `unit/`: Contains unit tests that focus on testing individual components (e.g., models, forms, views, URLs, templates) in isolation to ensure they function correctly.

## Test Types and Their Focus

### Integration Tests

Integration tests in this project are designed to validate the end-to-end workflow of features. They cover scenarios where multiple parts of the application interact, such as:

- **Scholarship Workflow:** Testing the complete lifecycle of a scholarship, from model creation and data retrieval through views, to rendering in templates.
- **Form-Model Integration:** Ensuring that forms correctly interact with models, including validation and saving data.
- **URL-View-Template Integration:** Verifying that URLs resolve to the correct views, and that views pass the appropriate context to templates for rendering.
- **Filtering and Ordering:** Testing the integrated functionality of data filtering and ordering across the application stack.

### Performance Tests

Performance tests are crucial for identifying and preventing performance bottlenecks. They measure the time taken for critical operations, including:

- **Bulk Create/Update:** Assessing the efficiency of creating and updating a large number of records.
- **Complex Queryset Execution:** Evaluating the performance of database queries with multiple filters and ordering conditions.
- **Ordering Operations:** Measuring the time taken to order large datasets.

### Regression Tests

Regression tests are vital for maintaining the stability of the application. They ensure that new changes do not introduce unintended side effects or break existing features. Key areas covered include:

- **Field Constraints:** Verifying that model field constraints (e.g., `max_length`, choices) remain consistent.
- **Ordering Behavior:** Ensuring that default ordering of objects in models remains unchanged.
- **Choice Validation:** Confirming that choice fields (e.g., `level`, `field`, `status`) enforce valid options.
- **Required Fields:** Validating that required fields are consistently enforced.

### Unit Tests

Unit tests are focused on individual components and their isolated functionality. They cover aspects such as:

- **Model Creation and Representation:** Verifying the correct creation and string representation of model instances.
- **Default Ordering:** Ensuring models are ordered as expected.
- **Choices Validation:** Testing that all defined choices for fields are correctly handled.
- **Field Max Lengths:** Confirming that field maximum lengths are as expected.
- **Required Fields Enforcement:** Verifying that fields marked as required are indeed enforced.
- **Model Validation:** Testing the `full_clean()` method for comprehensive model validation.
- **Custom Manager Methods:** If any custom manager methods exist, they are tested here to ensure they return the expected querysets.

## Running Tests

To run all tests, navigate to the project's root directory and execute:

```bash
python manage.py test main
```

To run tests for a specific category (e.g., integration tests):

```bash
python manage.py test main.test.intergration
```

To run tests for a specific file (e.g., performance model tests):

```bash
python manage.py test main.test.performance.test_performance_models
```

This documentation provides an overview of the testing strategy and helps developers understand the purpose and scope of different test types within the `main` application.
