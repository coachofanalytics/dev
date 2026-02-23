import importlib
print('coverage' if importlib.util.find_spec('coverage') else 'no-coverage')