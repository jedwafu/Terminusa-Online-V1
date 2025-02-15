import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import re
import json
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ValidationType(Enum):
    """Types of validation"""
    STRING = auto()
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    EMAIL = auto()
    USERNAME = auto()
    PASSWORD = auto()
    JSON = auto()
    UUID = auto()
    DATETIME = auto()
    CURRENCY = auto()
    COORDINATES = auto()

@dataclass
class ValidationRule:
    """Validation rule definition"""
    type: ValidationType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None

class ValidationError(Exception):
    """Validation error"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class ValidationSystem:
    """Input validation system"""
    def __init__(self):
        self.rules: Dict[str, Dict[str, ValidationRule]] = {}
        self._setup_default_patterns()

    def _setup_default_patterns(self):
        """Set up default validation patterns"""
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'username': r'^[a-zA-Z0-9_-]{3,16}$',
            'password': r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            'datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',
            'currency': r'^\d+(\.\d{1,2})?$',
            'coordinates': r'^\-?\d+(\.\d+)?,\-?\d+(\.\d+)?$'
        }

    def register_rules(self, schema_name: str, rules: Dict[str, ValidationRule]):
        """Register validation rules for a schema"""
        self.rules[schema_name] = rules

    def validate(self, schema_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema"""
        if schema_name not in self.rules:
            raise ValueError(f"Unknown schema: {schema_name}")
        
        rules = self.rules[schema_name]
        validated_data = {}
        
        # Check required fields
        for field, rule in rules.items():
            if rule.required and field not in data:
                raise ValidationError(field, "Field is required")
        
        # Validate fields
        for field, value in data.items():
            if field not in rules:
                continue
            
            rule = rules[field]
            
            if value is None:
                if rule.required:
                    raise ValidationError(field, "Field cannot be null")
                continue
            
            # Validate type
            validated_value = self._validate_type(field, value, rule)
            
            # Validate constraints
            self._validate_constraints(field, validated_value, rule)
            
            # Custom validation
            if rule.custom_validator:
                try:
                    validated_value = rule.custom_validator(validated_value)
                except Exception as e:
                    raise ValidationError(field, str(e))
            
            validated_data[field] = validated_value
        
        return validated_data

    def _validate_type(self, field: str, value: Any, rule: ValidationRule) -> Any:
        """Validate and convert value type"""
        try:
            if rule.type == ValidationType.STRING:
                return str(value)
            elif rule.type == ValidationType.INTEGER:
                return int(value)
            elif rule.type == ValidationType.FLOAT:
                return float(value)
            elif rule.type == ValidationType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes')
                return bool(value)
            elif rule.type == ValidationType.JSON:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            else:
                return value
        except Exception:
            raise ValidationError(field, f"Invalid type for {rule.type.name}")

    def _validate_constraints(self, field: str, value: Any, rule: ValidationRule):
        """Validate value constraints"""
        # Length constraints
        if isinstance(value, (str, list, dict)):
            if rule.min_length is not None and len(value) < rule.min_length:
                raise ValidationError(
                    field,
                    f"Minimum length is {rule.min_length}"
                )
            if rule.max_length is not None and len(value) > rule.max_length:
                raise ValidationError(
                    field,
                    f"Maximum length is {rule.max_length}"
                )
        
        # Value range constraints
        if isinstance(value, (int, float)):
            if rule.min_value is not None and value < rule.min_value:
                raise ValidationError(
                    field,
                    f"Minimum value is {rule.min_value}"
                )
            if rule.max_value is not None and value > rule.max_value:
                raise ValidationError(
                    field,
                    f"Maximum value is {rule.max_value}"
                )
        
        # Pattern matching
        if rule.type in (ValidationType.EMAIL, ValidationType.USERNAME,
                        ValidationType.PASSWORD, ValidationType.UUID,
                        ValidationType.DATETIME, ValidationType.CURRENCY,
                        ValidationType.COORDINATES):
            pattern = rule.pattern or self.patterns.get(rule.type.name.lower())
            if pattern and not re.match(pattern, str(value)):
                raise ValidationError(field, f"Invalid {rule.type.name.lower()} format")
        
        # Allowed values
        if rule.allowed_values is not None and value not in rule.allowed_values:
            raise ValidationError(
                field,
                f"Value must be one of: {rule.allowed_values}"
            )

class TestValidation(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.validation = ValidationSystem()
        
        # Register test schemas
        self.validation.register_rules('user', {
            'username': ValidationRule(
                type=ValidationType.USERNAME,
                min_length=3,
                max_length=16
            ),
            'email': ValidationRule(
                type=ValidationType.EMAIL
            ),
            'password': ValidationRule(
                type=ValidationType.PASSWORD
            ),
            'age': ValidationRule(
                type=ValidationType.INTEGER,
                min_value=13,
                max_value=120,
                required=False
            )
        })
        
        self.validation.register_rules('payment', {
            'amount': ValidationRule(
                type=ValidationType.CURRENCY,
                min_value=0.01
            ),
            'currency': ValidationRule(
                type=ValidationType.STRING,
                allowed_values=['USD', 'EUR', 'GBP']
            )
        })

    def test_basic_validation(self):
        """Test basic validation functionality"""
        # Valid data
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!'
        }
        
        validated = self.validation.validate('user', data)
        self.assertEqual(validated['username'], 'testuser')
        self.assertEqual(validated['email'], 'test@example.com')

    def test_type_validation(self):
        """Test type validation"""
        # Test integer validation
        data = {
            'amount': '100',
            'currency': 'USD'
        }
        
        validated = self.validation.validate('payment', data)
        self.assertIsInstance(validated['amount'], float)
        
        # Test invalid type
        data['amount'] = 'invalid'
        with self.assertRaises(ValidationError):
            self.validation.validate('payment', data)

    def test_constraint_validation(self):
        """Test constraint validation"""
        # Test length constraints
        data = {
            'username': 'ab',  # Too short
            'email': 'test@example.com',
            'password': 'Password123!'
        }
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('user', data)
        self.assertIn('length', str(context.exception))
        
        # Test value constraints
        data = {
            'amount': 0,  # Too low
            'currency': 'USD'
        }
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('payment', data)
        self.assertIn('Minimum value', str(context.exception))

    def test_pattern_validation(self):
        """Test pattern validation"""
        # Test email pattern
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'Password123!'
        }
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('user', data)
        self.assertIn('email', str(context.exception))
        
        # Test password pattern
        data['email'] = 'test@example.com'
        data['password'] = 'weak'  # Invalid password
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('user', data)
        self.assertIn('password', str(context.exception))

    def test_required_fields(self):
        """Test required field validation"""
        # Missing required field
        data = {
            'username': 'testuser',
            'password': 'Password123!'
            # Missing email
        }
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('user', data)
        self.assertIn('required', str(context.exception))
        
        # Optional field
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!'
            # Age is optional
        }
        
        validated = self.validation.validate('user', data)
        self.assertNotIn('age', validated)

    def test_allowed_values(self):
        """Test allowed values validation"""
        # Valid currency
        data = {
            'amount': 100,
            'currency': 'USD'
        }
        
        validated = self.validation.validate('payment', data)
        self.assertEqual(validated['currency'], 'USD')
        
        # Invalid currency
        data['currency'] = 'INVALID'
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('payment', data)
        self.assertIn('must be one of', str(context.exception))

    def test_custom_validation(self):
        """Test custom validation rules"""
        def validate_even(value):
            if value % 2 != 0:
                raise ValueError("Value must be even")
            return value
        
        # Register schema with custom validator
        self.validation.register_rules('custom', {
            'even_number': ValidationRule(
                type=ValidationType.INTEGER,
                custom_validator=validate_even
            )
        })
        
        # Test valid value
        data = {'even_number': 2}
        validated = self.validation.validate('custom', data)
        self.assertEqual(validated['even_number'], 2)
        
        # Test invalid value
        data = {'even_number': 3}
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('custom', data)
        self.assertIn('must be even', str(context.exception))

    def test_nested_validation(self):
        """Test validation of nested structures"""
        # Register schema with nested data
        self.validation.register_rules('nested', {
            'config': ValidationRule(
                type=ValidationType.JSON,
                required=True
            )
        })
        
        # Test valid nested data
        data = {
            'config': json.dumps({
                'setting1': True,
                'setting2': 42
            })
        }
        
        validated = self.validation.validate('nested', data)
        self.assertIsInstance(validated['config'], dict)
        self.assertEqual(validated['config']['setting2'], 42)
        
        # Test invalid JSON
        data['config'] = 'invalid json'
        with self.assertRaises(ValidationError):
            self.validation.validate('nested', data)

    def test_multiple_errors(self):
        """Test handling of multiple validation errors"""
        # Multiple invalid fields
        data = {
            'username': 'a',  # Too short
            'email': 'invalid',  # Invalid format
            'password': 'weak'  # Invalid format
        }
        
        with self.assertRaises(ValidationError) as context:
            self.validation.validate('user', data)
        
        # First error should be caught
        self.assertIn('length', str(context.exception))

if __name__ == '__main__':
    unittest.main()
