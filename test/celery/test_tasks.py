"""Compatibility shim: re-export celery task tests from the newer module.
"""
from .test_celery_tasks import test_celery_task_delay_mocked as test_celery_task_delay_mocked_copy
