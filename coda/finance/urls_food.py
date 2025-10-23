"""
Food Management URLs

URL patterns for food inventory, consumption, and purchase management
"""

from django.urls import path
from finance import views_food

app_name = 'food'

urlpatterns = [
    # Dashboard
    path('dashboard/', views_food.food_inventory_dashboard, name='dashboard'),
    
    # Consumption Logging
    path('log-consumption/', views_food.log_daily_consumption, name='log_consumption'),
    path('api/quick-log/', views_food.quick_log_consumption, name='quick_log_consumption'),
    
    # Purchase Recording
    path('record-purchase/', views_food.record_food_purchase, name='record_purchase'),
    path('fulfill-restock/<int:request_id>/', views_food.fulfill_restock_request, name='fulfill_restock'),
    
    # Restock Requests
    path('create-restock/', views_food.create_restock_request, name='create_restock'),
    path('restock-requests/', views_food.restock_request_list, name='restock_requests'),
    
    # Inventory Detail
    path('inventory/<int:inventory_id>/', views_food.inventory_detail, name='inventory_detail'),
    
    # API Endpoints
    path('api/inventory-by-location/', views_food.api_get_inventory_by_location, name='api_inventory_by_location'),
    path('api/inventory/<int:inventory_id>/', views_food.api_get_inventory_details, name='api_inventory_details'),
    path('api/consumption-chart/<int:inventory_id>/', views_food.api_consumption_chart_data, name='api_consumption_chart'),
    
    # Reports
    path('spending-report/', views_food.food_spending_report, name='spending_report'),
]

