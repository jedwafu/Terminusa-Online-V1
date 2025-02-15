import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Any
import json
import yaml
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Language(Enum):
    """Supported languages"""
    EN = "English"
    ES = "Español"
    FR = "Français"
    DE = "Deutsch"
    IT = "Italiano"
    PT = "Português"
    RU = "Русский"
    JA = "日本語"
    KO = "한국어"
    ZH = "中文"

@dataclass
class LocaleConfig:
    """Locale configuration"""
    language: Language
    date_format: str
    time_format: str
    number_format: Dict[str, str]
    currency_format: Dict[str, str]

class LocalizationSystem:
    """Manages game localization"""
    def __init__(self, translations_dir: str = 'locales'):
        self.translations_dir = translations_dir
        self.translations: Dict[Language, Dict[str, str]] = {}
        self.fallback_language = Language.EN
        self.configs: Dict[Language, LocaleConfig] = {}
        self.load_translations()
        self.load_configs()

    def load_translations(self):
        """Load translation files"""
        for language in Language:
            file_path = os.path.join(
                self.translations_dir,
                f"{language.name.lower()}.json"
            )
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[language] = json.load(f)

    def load_configs(self):
        """Load locale configurations"""
        config_path = os.path.join(self.translations_dir, 'configs.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                configs = yaml.safe_load(f)
                for lang_code, config in configs.items():
                    language = Language[lang_code.upper()]
                    self.configs[language] = LocaleConfig(
                        language=language,
                        date_format=config['date_format'],
                        time_format=config['time_format'],
                        number_format=config['number_format'],
                        currency_format=config['currency_format']
                    )

    def get_text(
        self,
        key: str,
        language: Language,
        replacements: Optional[Dict[str, str]] = None
    ) -> str:
        """Get translated text"""
        # Get translation
        translations = self.translations.get(language)
        if not translations:
            translations = self.translations.get(self.fallback_language)
        
        text = translations.get(key)
        if not text:
            translations = self.translations.get(self.fallback_language)
            text = translations.get(key, key)
        
        # Apply replacements
        if replacements:
            for key, value in replacements.items():
                text = text.replace(f"{{{key}}}", str(value))
        
        return text

    def format_number(
        self,
        number: float,
        language: Language,
        decimal_places: int = 2
    ) -> str:
        """Format number according to locale"""
        config = self.configs.get(language)
        if not config:
            config = self.configs.get(self.fallback_language)
        
        format_str = config.number_format['decimal']
        return format_str.format(number, decimal_places)

    def format_currency(
        self,
        amount: float,
        currency: str,
        language: Language
    ) -> str:
        """Format currency according to locale"""
        config = self.configs.get(language)
        if not config:
            config = self.configs.get(self.fallback_language)
        
        format_str = config.currency_format.get(
            currency,
            config.currency_format['default']
        )
        return format_str.format(amount)

    def format_datetime(
        self,
        dt: Any,
        language: Language,
        time: bool = True
    ) -> str:
        """Format datetime according to locale"""
        config = self.configs.get(language)
        if not config:
            config = self.configs.get(self.fallback_language)
        
        if time:
            return dt.strftime(f"{config.date_format} {config.time_format}")
        return dt.strftime(config.date_format)

class TestLocalization(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create test translations
        os.makedirs('locales', exist_ok=True)
        
        # English translations
        with open('locales/en.json', 'w', encoding='utf-8') as f:
            json.dump({
                'welcome': 'Welcome, {name}!',
                'item_found': 'You found {item}!',
                'gold_amount': 'You have {amount} gold'
            }, f)
        
        # Spanish translations
        with open('locales/es.json', 'w', encoding='utf-8') as f:
            json.dump({
                'welcome': '¡Bienvenido, {name}!',
                'item_found': '¡Has encontrado {item}!',
                'gold_amount': 'Tienes {amount} de oro'
            }, f)
        
        # Locale configs
        with open('locales/configs.yaml', 'w', encoding='utf-8') as f:
            yaml.dump({
                'en': {
                    'date_format': '%Y-%m-%d',
                    'time_format': '%H:%M:%S',
                    'number_format': {
                        'decimal': '{:.{}f}',
                        'thousands': ','
                    },
                    'currency_format': {
                        'default': '${:.2f}',
                        'EUR': '€{:.2f}',
                        'GBP': '£{:.2f}'
                    }
                },
                'es': {
                    'date_format': '%d/%m/%Y',
                    'time_format': '%H:%M:%S',
                    'number_format': {
                        'decimal': '{:.{}f}',
                        'thousands': '.'
                    },
                    'currency_format': {
                        'default': '{:.2f}€',
                        'USD': '${:.2f}',
                        'GBP': '£{:.2f}'
                    }
                }
            }, f)
        
        self.l10n = LocalizationSystem('locales')

    def tearDown(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree('locales')

    def test_basic_translation(self):
        """Test basic text translation"""
        # Test English
        text = self.l10n.get_text(
            'welcome',
            Language.EN,
            {'name': 'Player'}
        )
        self.assertEqual(text, 'Welcome, Player!')
        
        # Test Spanish
        text = self.l10n.get_text(
            'welcome',
            Language.ES,
            {'name': 'Player'}
        )
        self.assertEqual(text, '¡Bienvenido, Player!')

    def test_missing_translation(self):
        """Test fallback for missing translations"""
        # Test missing key
        text = self.l10n.get_text(
            'missing_key',
            Language.EN
        )
        self.assertEqual(text, 'missing_key')
        
        # Test missing language
        text = self.l10n.get_text(
            'welcome',
            Language.FR,  # French not available
            {'name': 'Player'}
        )
        self.assertEqual(text, 'Welcome, Player!')  # Fallback to English

    def test_number_formatting(self):
        """Test number formatting"""
        # Test English format
        number = self.l10n.format_number(1234.5678, Language.EN, 2)
        self.assertEqual(number, '1234.57')
        
        # Test Spanish format
        number = self.l10n.format_number(1234.5678, Language.ES, 2)
        self.assertEqual(number, '1234,57')

    def test_currency_formatting(self):
        """Test currency formatting"""
        # Test USD in English
        amount = self.l10n.format_currency(1234.56, 'USD', Language.EN)
        self.assertEqual(amount, '$1234.56')
        
        # Test EUR in Spanish
        amount = self.l10n.format_currency(1234.56, 'EUR', Language.ES)
        self.assertEqual(amount, '1234.56€')

    def test_datetime_formatting(self):
        """Test datetime formatting"""
        from datetime import datetime
        
        dt = datetime(2024, 1, 1, 12, 30, 45)
        
        # Test English format
        formatted = self.l10n.format_datetime(dt, Language.EN)
        self.assertEqual(formatted, '2024-01-01 12:30:45')
        
        # Test Spanish format
        formatted = self.l10n.format_datetime(dt, Language.ES)
        self.assertEqual(formatted, '01/01/2024 12:30:45')

    def test_replacements(self):
        """Test text replacements"""
        # Test multiple replacements
        text = self.l10n.get_text(
            'item_found',
            Language.EN,
            {'item': 'Legendary Sword'}
        )
        self.assertEqual(text, 'You found Legendary Sword!')
        
        # Test missing replacement
        text = self.l10n.get_text(
            'welcome',
            Language.EN
            # Missing 'name' replacement
        )
        self.assertEqual(text, 'Welcome, {name}!')

    def test_number_precision(self):
        """Test number precision handling"""
        # Test different decimal places
        number = self.l10n.format_number(1234.5678, Language.EN, 0)
        self.assertEqual(number, '1235')
        
        number = self.l10n.format_number(1234.5678, Language.EN, 3)
        self.assertEqual(number, '1234.568')

    def test_currency_symbols(self):
        """Test currency symbol handling"""
        # Test different currencies
        currencies = {
            'USD': '$1234.56',
            'EUR': '€1234.56',
            'GBP': '£1234.56'
        }
        
        for currency, expected in currencies.items():
            amount = self.l10n.format_currency(1234.56, currency, Language.EN)
            self.assertEqual(amount, expected)

    def test_date_only_format(self):
        """Test date-only formatting"""
        from datetime import datetime
        
        dt = datetime(2024, 1, 1, 12, 30, 45)
        
        # Test without time
        formatted = self.l10n.format_datetime(dt, Language.EN, time=False)
        self.assertEqual(formatted, '2024-01-01')
        
        formatted = self.l10n.format_datetime(dt, Language.ES, time=False)
        self.assertEqual(formatted, '01/01/2024')

    def test_fallback_config(self):
        """Test locale config fallback"""
        # Test unsupported language
        number = self.l10n.format_number(1234.56, Language.FR)  # French not configured
        self.assertEqual(number, '1234.56')  # Should use English format

    def test_multiple_replacements(self):
        """Test multiple text replacements"""
        text = self.l10n.get_text(
            'gold_amount',
            Language.EN,
            {'amount': '1000'}
        )
        self.assertEqual(text, 'You have 1000 gold')
        
        text = self.l10n.get_text(
            'gold_amount',
            Language.ES,
            {'amount': '1000'}
        )
        self.assertEqual(text, 'Tienes 1000 de oro')

if __name__ == '__main__':
    unittest.main()
