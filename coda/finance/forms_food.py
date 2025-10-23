"""
Food Management Forms

Forms for daily consumption logging, purchase recording, and inventory management.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from finance.models import (
    Food, FoodInventory, FoodPurchaseTransaction,
    FoodConsumptionLog, FoodRestockRequest, Supplier
)


# =============================================================================
# CONSUMPTION LOGGING FORMS
# =============================================================================

class DailyConsumptionLogForm(forms.Form):
    """
    Form for logging daily food consumption
    
    Used by staff to record what was consumed each day.
    """
    inventory = forms.ModelChoiceField(
        queryset=FoodInventory.objects.select_related('food_item', 'location').filter(
            status__in=['in_stock', 'low_stock']
        ),
        label='Food Item',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_inventory'
        })
    )
    
    quantity_consumed = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Quantity Consumed',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_quantity_consumed',
            'step': '0.01',
            'placeholder': 'Enter quantity'
        })
    )
    
    consumption_type = forms.ChoiceField(
        choices=[
            ('normal', 'Normal Usage'),
            ('event', 'Special Event'),
            ('waste', 'Waste/Spoilage'),
            ('donation', 'Donation'),
        ],
        initial='normal',
        label='Type',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_consumption_type'
        })
    )
    
    consumption_date = forms.DateField(
        initial=timezone.now,
        label='Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'id_consumption_date',
            'type': 'date'
        })
    )
    
    notes = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'id_notes',
            'rows': 3,
            'placeholder': 'Optional notes (e.g., event details, reason for waste)'
        })
    )
    
    def __init__(self, *args, location=None, **kwargs):
        """Initialize form, optionally filtering by location"""
        super().__init__(*args, **kwargs)
        
        if location:
            self.fields['inventory'].queryset = self.fields['inventory'].queryset.filter(
                location=location
            )
    
    def clean(self):
        cleaned_data = super().clean()
        inventory = cleaned_data.get('inventory')
        quantity = cleaned_data.get('quantity_consumed')
        
        if inventory and quantity:
            # Check if quantity exceeds available stock
            if quantity > inventory.quantity:
                raise ValidationError(
                    f"Cannot consume {quantity} - only {inventory.quantity} "
                    f"{inventory.food_item.unit_of_measurement} available in stock"
                )
        
        return cleaned_data


class BulkConsumptionLogForm(forms.Form):
    """
    Form for logging multiple consumption entries at once
    
    Used for end-of-day logging where multiple items were consumed.
    """
    location = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label='Location',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_location'
        })
    )
    
    consumption_date = forms.DateField(
        initial=timezone.now,
        label='Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'id_consumption_date',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular import
        from main.models import Department
        self.fields['location'].queryset = Department.objects.filter(is_active=True)


# =============================================================================
# PURCHASE RECORDING FORMS
# =============================================================================

class FoodPurchaseForm(forms.ModelForm):
    """
    Form for recording food purchases
    
    Used when staff purchases food items. Will automatically:
    - Create Transaction record
    - Update Budget
    - Update Inventory
    - Update Food price
    """
    
    class Meta:
        model = FoodPurchaseTransaction
        fields = [
            'food_item', 'inventory', 'quantity', 'unit_price', 'currency',
            'supplier', 'payment_method', 'receipt_number', 'purchase_date', 'notes'
        ]
        widgets = {
            'food_item': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_food_item'
            }),
            'inventory': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_inventory',
                'required': False
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_quantity',
                'step': '0.01',
                'placeholder': 'Quantity purchased'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_unit_price',
                'step': '0.01',
                'placeholder': 'Price per unit'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_currency'
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_supplier'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_payment_method'
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_receipt_number',
                'placeholder': 'Receipt or invoice number'
            }),
            'purchase_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'id': 'id_purchase_date',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_notes',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make inventory optional (can purchase without linking to specific inventory)
        self.fields['inventory'].required = False
        
        # Set initial values
        if 'initial' not in kwargs:
            self.fields['purchase_date'].initial = timezone.now()
        
        # Filter active suppliers
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        # Validate positive values
        if quantity and quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than 0'})
        
        if unit_price and unit_price <= 0:
            raise ValidationError({'unit_price': 'Unit price must be greater than 0'})
        
        return cleaned_data


class RestockRequestForm(forms.ModelForm):
    """
    Form for manually creating restock requests
    
    Usually auto-created by signals, but staff can also create manually.
    """
    
    class Meta:
        model = FoodRestockRequest
        fields = ['inventory', 'requested_quantity', 'notes']
        widgets = {
            'inventory': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_inventory'
            }),
            'requested_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_requested_quantity',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_notes',
                'rows': 3,
                'placeholder': 'Reason for restock request'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show inventories that need restocking or are low
        self.fields['inventory'].queryset = FoodInventory.objects.filter(
            status__in=['low_stock', 'out_of_stock']
        ).select_related('food_item', 'location')


# =============================================================================
# INVENTORY MANAGEMENT FORMS
# =============================================================================

class FoodInventoryForm(forms.ModelForm):
    """
    Form for creating/updating food inventory records
    """
    
    class Meta:
        model = FoodInventory
        fields = [
            'food_item', 'location', 'quantity',
            'reorder_level', 'reorder_quantity'
        ]
        widgets = {
            'food_item': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_food_item'
            }),
            'location': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_location'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_quantity',
                'step': '0.01'
            }),
            'reorder_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_reorder_level',
                'step': '0.01',
                'help_text': 'Trigger reorder when stock falls below this level'
            }),
            'reorder_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_reorder_quantity',
                'step': '0.01',
                'help_text': 'Amount to order when restocking'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        reorder_level = cleaned_data.get('reorder_level')
        reorder_quantity = cleaned_data.get('reorder_quantity')
        
        # Validate positive values
        if quantity is not None and quantity < 0:
            raise ValidationError({'quantity': 'Quantity cannot be negative'})
        
        if reorder_level and reorder_level < 0:
            raise ValidationError({'reorder_level': 'Reorder level cannot be negative'})
        
        if reorder_quantity and reorder_quantity <= 0:
            raise ValidationError({'reorder_quantity': 'Reorder quantity must be greater than 0'})
        
        return cleaned_data


class FoodItemForm(forms.ModelForm):
    """
    Form for creating/updating food items in the catalog
    """
    
    class Meta:
        model = Food
        fields = [
            'name', 'description', 'category', 'current_unit_price',
            'currency', 'unit_of_measurement', 'current_supplier', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_description',
                'rows': 3
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
            'current_unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_current_unit_price',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_currency'
            }),
            'unit_of_measurement': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_unit_of_measurement',
                'placeholder': 'e.g., kg, liters, pieces'
            }),
            'current_supplier': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_current_supplier'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_active'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active suppliers
        self.fields['current_supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['current_supplier'].required = False


# =============================================================================
# QUICK LOG FORMS (AJAX)
# =============================================================================

class QuickConsumptionForm(forms.Form):
    """
    Simplified form for quick AJAX consumption logging
    """
    inventory_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    notes = forms.CharField(required=False, max_length=500)

