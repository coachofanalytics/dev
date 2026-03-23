call C:\Users\PC\Desktop\dc48k_train\dc_venv\Scripts\activate.bat
python manage.py test news.tests.unit --verbosity=2 > news\reports\actual\unit_raw.txt 2>&1
python manage.py test news.tests.integration --verbosity=2 > news\reports\actual\integration_raw.txt 2>&1
python manage.py test news.tests.regression --verbosity=2 > news\reports\actual\regression_raw.txt 2>&1
python manage.py test news.tests.system --verbosity=2 > news\reports\actual\system_raw.txt 2>&1
python manage.py test news.tests.performance --verbosity=2 > news\reports\actual\performance_raw.txt 2>&1
python manage.py test news.tests --verbosity=2 > news\reports\actual\full_raw.txt 2>&1
python news\reports\actual\generate_actual_report.py
python news\reports\summary\generate_summary_report.py
