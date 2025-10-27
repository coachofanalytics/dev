"""
Shared test fixtures for CODA test suite
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from accounts.models import CustomerUser
from management.models import Department
from finance.models import Food, FoodInventory, Supplier


@pytest.fixture
def user(db):
    """Create a test user"""
    return CustomerUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user"""
    return CustomerUser.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        first_name='Staff',
        last_name='User',
        is_staff=True
    )


@pytest.fixture
def department(db):
    """Create a test department"""
    dept, _ = Department.objects.get_or_create(
        name='Test Department',
        defaults={'slug': 'test-dept'}
    )
    return dept


@pytest.fixture
def supplier(db):
    """Create a test supplier"""
    return Supplier.objects.create(
        name='Test Supplier',
        contact_person='John Doe',
        email='supplier@example.com',
        phone='+254712345678',
        is_active=True
    )


@pytest.fixture
def food_item(db, supplier):
    """Create a test food item"""
    return Food.objects.create(
        name='Test Rice',
        description='Long grain white rice for testing',
        category='grains',
        current_unit_price=Decimal("5.00"),
        currency='USD',
        unit_of_measurement='kg',
        current_supplier=supplier,
        is_active=True
    )


@pytest.fixture
def inventory(db, food_item, department):
    """Create a test inventory with good stock"""
    return FoodInventory.objects.create(
        food_item=food_item,
        location=department,
        quantity=Decimal("50.0"),
        reorder_level=Decimal("10.0"),
        reorder_quantity=Decimal("30.0")
    )


@pytest.fixture
def low_stock_inventory(db, department):
    """Create a low stock inventory"""
    supplier = Supplier.objects.create(
        name='Low Stock Supplier',
        email='lowstock@example.com'
    )
    food = Food.objects.create(
        name='Low Stock Sugar',
        category='grains',
        current_unit_price=Decimal("2.50"),
        currency='USD',
        unit_of_measurement='kg',
        current_supplier=supplier
    )
    return FoodInventory.objects.create(
        food_item=food,
        location=department,
        quantity=Decimal("5.0"),  # Below reorder level
        reorder_level=Decimal("10.0"),
        reorder_quantity=Decimal("30.0")
    )

