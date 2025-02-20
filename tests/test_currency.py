"""
Tests for the currency system.
"""

import pytest
from decimal import Decimal
from typing import Dict, Any
from datetime import datetime

def test_currency_creation(test_user: Dict[str, Any], db_session):
    """Test currency creation."""
    from models import Currency, CurrencyType
    
    # Create a new currency
    currency = Currency(
        user_id=test_user['id'],
        type=CurrencyType.EXONS,
        amount=1000.0,
        max_supply=None,
        is_gate_reward=False,
        base_tax_rate=0.13,
        guild_tax_rate=0.02,
        admin_wallet="FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw",
        admin_username="adminbb",
        created_at=datetime.utcnow()
    )
    
    db_session.add(currency)
    db_session.commit()
    
    # Verify currency was created
    assert currency.id is not None
    assert currency.amount == 1000.0
    assert currency.type == CurrencyType.EXONS

def test_currency_tax_calculation(test_currencies: Dict[str, Any], db_session):
    """Test currency tax calculation."""
    from models import Currency
    
    currency = Currency.query.get(test_currencies['EXONS']['id'])
    
    # Calculate base tax
    amount = 1000.0
    base_tax = currency.calculate_tax(amount, include_guild_tax=False)
    assert base_tax == amount * 0.13  # 13% base tax
    
    # Calculate total tax (base + guild)
    total_tax = currency.calculate_tax(amount, include_guild_tax=True)
    assert total_tax == amount * 0.15  # 13% base + 2% guild tax

def test_currency_transaction(test_user: Dict[str, Any], test_currencies: Dict[str, Any], db_session):
    """Test currency transaction creation."""
    from models import Transaction, TransactionType, Currency
    
    currency = Currency.query.get(test_currencies['EXONS']['id'])
    initial_amount = currency.amount
    
    # Create a transaction
    transaction = Transaction(
        currency_id=currency.id,
        user_id=test_user['id'],
        type=TransactionType.EARN,
        amount=100.0,
        description="Test transaction",
        created_at=datetime.utcnow()
    )
    
    db_session.add(transaction)
    db_session.commit()
    
    # Verify transaction was created
    assert transaction.id is not None
    assert transaction.amount == 100.0
    assert transaction.type == TransactionType.EARN

def test_token_swap(test_user: Dict[str, Any], test_currencies: Dict[str, Any], db_session):
    """Test token swap functionality."""
    from models import TokenSwap, CurrencyType, Currency
    
    # Create a token swap
    swap = TokenSwap(
        user_id=test_user['id'],
        currency_id=test_currencies['EXONS']['id'],
        from_currency=CurrencyType.SOLANA,
        to_currency=CurrencyType.EXONS,
        from_amount=1.0,
        to_amount=100.0,
        rate=100.0,
        status='pending',
        created_at=datetime.utcnow()
    )
    
    db_session.add(swap)
    db_session.commit()
    
    # Verify swap was created
    assert swap.id is not None
    assert swap.from_amount == 1.0
    assert swap.to_amount == 100.0
    assert swap.status == 'pending'

@pytest.mark.parametrize('amount,expected_result', [
    (100.0, True),
    (1000000.0, False)
])
def test_currency_can_afford(test_currencies: Dict[str, Any], amount: float, expected_result: bool, db_session):
    """Test currency can_afford check."""
    from models import Currency
    
    currency = Currency.query.get(test_currencies['EXONS']['id'])
    assert currency.can_afford(amount) == expected_result

def test_crystal_max_supply(test_user: Dict[str, Any], db_session):
    """Test crystal max supply limit."""
    from models import Currency, CurrencyType
    
    # Create crystal currency with max supply
    currency = Currency(
        user_id=test_user['id'],
        type=CurrencyType.CRYSTALS,
        amount=0.0,
        max_supply=100_000_000,  # 100M initial supply
        is_gate_reward=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(currency)
    db_session.commit()
    
    assert currency.max_supply == 100_000_000

def test_currency_precision(test_currencies: Dict[str, Any], db_session):
    """Test currency precision handling."""
    from models import Currency
    
    currency = Currency.query.get(test_currencies['SOLANA']['id'])
    
    # Test high precision amount
    currency.amount = Decimal('1.123456789123456789')
    db_session.commit()
    
    # Reload from database
    db_session.refresh(currency)
    
    # Should maintain precision up to 18 decimal places
    assert str(currency.amount) == '1.123456789123456789'

def test_gate_reward_currency(test_currencies: Dict[str, Any], db_session):
    """Test gate reward currency flag."""
    from models import Currency
    
    crystal_currency = Currency.query.get(test_currencies['CRYSTALS']['id'])
    assert crystal_currency.is_gate_reward is True
    
    exon_currency = Currency.query.get(test_currencies['EXONS']['id'])
    assert exon_currency.is_gate_reward is False

def test_admin_wallet_validation(test_user: Dict[str, Any], db_session):
    """Test admin wallet validation."""
    from models import Currency, CurrencyType
    
    # Create currency with invalid admin wallet
    with pytest.raises(ValueError):
        currency = Currency(
            user_id=test_user['id'],
            type=CurrencyType.EXONS,
            amount=1000.0,
            admin_wallet="invalid_wallet",
            admin_username="adminbb",
            created_at=datetime.utcnow()
        )
        
        db_session.add(currency)
        db_session.commit()

def test_currency_type_validation(test_user: Dict[str, Any], db_session):
    """Test currency type validation."""
    from models import Currency
    
    # Try to create currency with invalid type
    with pytest.raises(ValueError):
        currency = Currency(
            user_id=test_user['id'],
            type='INVALID_TYPE',
            amount=1000.0,
            created_at=datetime.utcnow()
        )
        
        db_session.add(currency)
        db_session.commit()
