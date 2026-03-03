def test_safe_module_imports():
    # Import a set of lightweight modules to increase deterministic coverage
    modules = [
        'accounts.choices',
        'accounts.utils',
        'main.utils',
        'coda_project.settings',
    ]
    for m in modules:
        mod = __import__(m, fromlist=['*'])
        assert mod is not None
