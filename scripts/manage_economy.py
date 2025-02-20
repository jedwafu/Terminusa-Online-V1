#!/usr/bin/env python3
"""Economy and marketplace management script for Terminusa Online"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import app, db
from models import (
    Currency, CurrencyType, Transaction, TokenSwap,
    Item, ItemType, ItemGrade, ShopTransaction,
    Trade, TradeItem
)

def check_currency_supply(args):
    """Check currency supply and circulation"""
    with app.app_context():
        print("Currency Supply Report")
        print("=" * 50)
        
        currencies = Currency.query.all()
        for currency in currencies:
            print(f"\n{currency.name} ({currency.symbol})")
            print("-" * 30)
            print(f"Type: {currency.type.value}")
            
            if currency.type == CurrencyType.CRYSTAL:
                print(f"Max Supply: {currency.max_supply:,}")
                print(f"Current Supply: {currency.current_supply:,}")
                print(f"Available Supply: {currency.max_supply - currency.current_supply:,}")
                
                # Get circulation stats
                total_held = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(currency_id=currency.id)\
                    .scalar() or 0
                print(f"In Circulation: {total_held:,}")
            
            elif currency.type == CurrencyType.EXON:
                if currency.contract_address:
                    print(f"Contract: {currency.contract_address}")
                # Get total transactions
                total_tx = Transaction.query.filter_by(currency_id=currency.id).count()
                print(f"Total Transactions: {total_tx:,}")
            
            # Get tax stats
            total_tax = db.session.query(db.func.sum(Transaction.fee))\
                .filter_by(currency_id=currency.id)\
                .scalar() or 0
            print(f"Total Tax Collected: {total_tax:,}")
            
            print(f"Base Tax Rate: {currency.base_tax_rate:.1%}")
            print(f"Guild Tax Rate: {currency.guild_tax_rate:.1%}")

def analyze_market(args):
    """Analyze marketplace activity"""
    with app.app_context():
        print("Market Analysis Report")
        print("=" * 50)
        
        # Time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=args.days)
        
        print(f"\nAnalyzing period: {start_date.date()} to {end_date.date()}")
        
        # Get trading volume
        trades = Trade.query\
            .filter(Trade.created_at >= start_date)\
            .filter(Trade.status == 'completed')\
            .all()
        
        print(f"\nTrading Activity:")
        print(f"Total Trades: {len(trades):,}")
        
        # Analyze by item grade
        print("\nVolume by Item Grade:")
        grade_volume = {}
        for trade in trades:
            for trade_item in trade.items:
                grade = trade_item.inventory_item.item.grade.value
                grade_volume[grade] = grade_volume.get(grade, 0) + 1
        
        for grade, volume in sorted(grade_volume.items()):
            print(f"{grade:12}: {volume:,} trades")
        
        # Analyze shop transactions
        shop_tx = ShopTransaction.query\
            .filter(ShopTransaction.created_at >= start_date)\
            .all()
        
        print(f"\nShop Activity:")
        print(f"Total Transactions: {len(shop_tx):,}")
        
        # Split by currency
        crystal_volume = sum(tx.crystal_amount for tx in shop_tx)
        exon_volume = sum(tx.exon_amount for tx in shop_tx)
        
        print(f"Crystal Volume: {crystal_volume:,}")
        print(f"Exon Volume: {exon_volume:,}")
        
        # Most traded items
        print("\nTop Traded Items:")
        item_volume = {}
        for tx in shop_tx:
            item_volume[tx.item_id] = item_volume.get(tx.item_id, 0) + tx.quantity
        
        top_items = sorted(item_volume.items(), key=lambda x: x[1], reverse=True)[:10]
        for item_id, volume in top_items:
            item = Item.query.get(item_id)
            print(f"{item.name:20}: {volume:,} units")

def adjust_prices(args):
    """Adjust shop prices based on market activity"""
    with app.app_context():
        print("Price Adjustment Analysis")
        print("=" * 50)
        
        items = Item.query.filter(
            (Item.crystal_price.isnot(None)) | 
            (Item.exon_price.isnot(None))
        ).all()
        
        for item in items:
            print(f"\n{item.name}")
            print("-" * 30)
            
            # Get recent transactions
            recent_tx = ShopTransaction.query\
                .filter_by(item_id=item.id)\
                .filter(ShopTransaction.created_at >= datetime.utcnow() - timedelta(days=7))\
                .all()
            
            volume = sum(tx.quantity for tx in recent_tx)
            print(f"Weekly Volume: {volume}")
            
            if item.crystal_price:
                print(f"Current Crystal Price: {item.crystal_price:,}")
                if not args.view_only:
                    # Adjust based on volume
                    if volume > 1000:
                        item.crystal_price = int(item.crystal_price * 1.1)
                    elif volume < 100:
                        item.crystal_price = int(item.crystal_price * 0.9)
                    print(f"New Crystal Price: {item.crystal_price:,}")
            
            if item.exon_price:
                print(f"Current Exon Price: {item.exon_price:,}")
                if not args.view_only:
                    # Adjust based on volume
                    if volume > 1000:
                        item.exon_price = int(item.exon_price * 1.1)
                    elif volume < 100:
                        item.exon_price = int(item.exon_price * 0.9)
                    print(f"New Exon Price: {item.exon_price:,}")
        
        if not args.view_only:
            db.session.commit()
            print("\nPrices adjusted!")

def export_market_data(args):
    """Export market data for analysis"""
    with app.app_context():
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'currencies': [],
            'items': [],
            'trades': [],
            'shop_transactions': []
        }
        
        # Get currency data
        currencies = Currency.query.all()
        for currency in currencies:
            currency_data = {
                'name': currency.name,
                'symbol': currency.symbol,
                'type': currency.type.value,
                'max_supply': currency.max_supply,
                'current_supply': currency.current_supply,
                'tax_rates': {
                    'base': currency.base_tax_rate,
                    'guild': currency.guild_tax_rate
                }
            }
            data['currencies'].append(currency_data)
        
        # Get item data
        items = Item.query.all()
        for item in items:
            item_data = {
                'name': item.name,
                'type': item.item_type.value,
                'grade': item.grade.value,
                'crystal_price': item.crystal_price,
                'exon_price': item.exon_price
            }
            data['items'].append(item_data)
        
        # Get recent trade data
        trades = Trade.query\
            .filter(Trade.created_at >= datetime.utcnow() - timedelta(days=7))\
            .all()
        
        for trade in trades:
            trade_data = {
                'id': trade.id,
                'status': trade.status,
                'crystal_amount': trade.crystal_amount,
                'exon_amount': trade.exon_amount,
                'created_at': trade.created_at.isoformat()
            }
            data['trades'].append(trade_data)
        
        # Get recent shop transactions
        shop_tx = ShopTransaction.query\
            .filter(ShopTransaction.created_at >= datetime.utcnow() - timedelta(days=7))\
            .all()
        
        for tx in shop_tx:
            tx_data = {
                'id': tx.id,
                'item_id': tx.item_id,
                'quantity': tx.quantity,
                'crystal_amount': tx.crystal_amount,
                'exon_amount': tx.exon_amount,
                'created_at': tx.created_at.isoformat()
            }
            data['shop_transactions'].append(tx_data)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = project_root / 'data' / 'market'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        data_file = data_dir / f'market_data_{timestamp}.json'
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Market data exported to: {data_file}")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online Economy Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Supply command
    supply_parser = subparsers.add_parser('supply', 
                                        help='Check currency supply')
    
    # Market command
    market_parser = subparsers.add_parser('market', 
                                        help='Analyze market activity')
    market_parser.add_argument('--days', type=int, default=7,
                             help='Days of history to analyze')
    
    # Prices command
    prices_parser = subparsers.add_parser('prices',
                                        help='Adjust shop prices')
    prices_parser.add_argument('--view-only', action='store_true',
                             help='Only view current prices')
    
    # Export command
    export_parser = subparsers.add_parser('export',
                                        help='Export market data')
    
    args = parser.parse_args()
    
    if args.command == 'supply':
        check_currency_supply(args)
    elif args.command == 'market':
        analyze_market(args)
    elif args.command == 'prices':
        adjust_prices(args)
    elif args.command == 'export':
        export_market_data(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
