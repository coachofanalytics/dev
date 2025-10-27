"""
Unit tests for Food Management models
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from finance.models import Food, FoodInventory, FoodPriceHistory


@pytest.mark.django_db
class TestFoodModel:
    """Tests for the Food model"""
    
    def test_food_creation(self, supplier):
        """Test creating a food item"""
        food = Food.objects.create(
            name="Rice",
            description="Long grain white rice",
            category="grains",
            current_unit_price=Decimal("5.00"),
            currency="USD",
            unit_of_measurement="kg",
            current_supplier=supplier,
            is_active=True
        )
        
        assert food.name == "Rice"
        assert food.current_unit_price == Decimal("5.00")
        assert food.category == "grains"
        assert food.is_active is True
    
    def test_food_string_representation(self, food_item):
        """Test __str__ method"""
        expected = f"{food_item.name} ({food_item.current_unit_price} {food_item.currency})"
        assert str(food_item) == expected
    
    def test_food_total_amount_property(self, food_item):
        """Test total_amount property returns current_unit_price"""
        assert food_item.total_amount == food_item.current_unit_price


@pytest.mark.django_db
class TestFoodInventory:
    """Tests for the FoodInventory model"""
    
    def test_inventory_creation(self, food_item, department):
        """Test creating an inventory record"""
        inventory = FoodInventory.objects.create(
            food_item=food_item,
            location=department,
            quantity=Decimal("100.0"),
            reorder_level=Decimal("20.0"),
            reorder_quantity=Decimal("50.0")
        )
        
        assert inventory.food_item == food_item
        assert inventory.location == department
        assert inventory.quantity == Decimal("100.0")
    
    def test_inventory_status_in_stock(self, inventory):
        """Test that inventory with sufficient stock is 'in_stock'"""
        inventory.quantity = Decimal("50.0")
        inventory.reorder_level = Decimal("10.0")
        inventory.update_status()
        
        assert inventory.status == 'in_stock'
    
    def test_inventory_status_low_stock(self, inventory):
        """Test that inventory below reorder level is 'low_stock'"""
        inventory.quantity = Decimal("8.0")
        inventory.reorder_level = Decimal("10.0")
        inventory.update_status()
        
        assert inventory.status == 'low_stock'
    
    def test_inventory_status_out_of_stock(self, inventory):
        """Test that inventory with zero quantity is 'out_of_stock'"""
        inventory.quantity = Decimal("0.0")
        inventory.update_status()
        
        assert inventory.status == 'out_of_stock'
    
    def test_inventory_days_until_stockout(self, inventory):
        """Test days_until_stockout calculation"""
        inventory.quantity = Decimal("30.0")
        inventory.daily_consumption_rate = Decimal("3.0")
        
        days = inventory.days_until_stockout()
        
        assert days == 10.0  # 30 / 3 = 10 days
    
    def test_inventory_days_until_stockout_no_consumption(self, inventory):
        """Test days_until_stockout when no consumption data"""
        inventory.daily_consumption_rate = None
        
        days = inventory.days_until_stockout()
        
        assert days is None


@pytest.mark.django_db
class TestFoodPriceHistory:
    """Tests for the FoodPriceHistory model"""
    
    def test_price_history_creation(self, food_item, user):
        """Test creating a price history record"""
        history = FoodPriceHistory.objects.create(
            food=food_item,
            old_price=Decimal("5.00"),
            new_price=Decimal("5.50"),
            changed_by=user
        )
        
        assert history.food == food_item
        assert history.old_price == Decimal("5.00")
        assert history.new_price == Decimal("5.50")
    
    def test_price_change_percentage_increase(self, food_item, user):
        """Test change_percentage calculation for price increase"""
        history = FoodPriceHistory.objects.create(
            food=food_item,
            old_price=Decimal("5.00"),
            new_price=Decimal("6.00"),
            changed_by=user
        )
        
        # (6.00 - 5.00) / 5.00 * 100 = 20%
        expected = Decimal("20.00")
        assert history.change_percentage == expected
    
    def test_price_change_percentage_decrease(self, food_item, user):
        """Test change_percentage calculation for price decrease"""
        history = FoodPriceHistory.objects.create(
            food=food_item,
            old_price=Decimal("5.00"),
            new_price=Decimal("4.00"),
            changed_by=user
        )
        
        # (4.00 - 5.00) / 5.00 * 100 = -20%
        expected = Decimal("-20.00")
        assert history.change_percentage == expected


