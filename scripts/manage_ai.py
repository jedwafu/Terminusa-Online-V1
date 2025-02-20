#!/usr/bin/env python3
"""AI system management script for Terminusa Online"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import app, db
from models import (
    AIModel, AIModelType, PlayerProfile, ActivityLog,
    AIDecision, GachaSystem, GamblingSystem
)

def train_model(args):
    """Train or retrain an AI model"""
    with app.app_context():
        model = AIModel.query.filter_by(name=args.model).first()
        if not model:
            print(f"Model not found: {args.model}")
            sys.exit(1)
        
        print(f"Training model: {model.name}")
        print(f"Type: {model.model_type.value}")
        print(f"Current version: {model.version}")
        
        # Load training data
        activity_logs = ActivityLog.query.all()
        decisions = AIDecision.query.filter_by(model_id=model.id).all()
        
        print(f"\nTraining data:")
        print(f"Activity logs: {len(activity_logs)}")
        print(f"Previous decisions: {len(decisions)}")
        
        # Update model parameters
        model.training_iterations += 1
        model.last_trained = datetime.utcnow()
        
        # TODO: Implement actual training logic based on model type
        
        db.session.commit()
        print("\nTraining complete!")

def evaluate_model(args):
    """Evaluate AI model performance"""
    with app.app_context():
        model = AIModel.query.filter_by(name=args.model).first()
        if not model:
            print(f"Model not found: {args.model}")
            sys.exit(1)
        
        print(f"Evaluating model: {model.name}")
        
        # Get recent decisions
        decisions = AIDecision.query.filter_by(model_id=model.id)\
            .order_by(AIDecision.created_at.desc())\
            .limit(1000).all()
        
        if not decisions:
            print("No decisions found for evaluation")
            return
        
        # Calculate metrics
        total = len(decisions)
        successful = len([d for d in decisions if d.success])
        accuracy = successful / total if total > 0 else 0
        
        print(f"\nMetrics:")
        print(f"Total decisions: {total}")
        print(f"Successful decisions: {successful}")
        print(f"Accuracy: {accuracy:.2%}")
        
        # Update model metrics
        model.accuracy = accuracy
        model.last_evaluation = datetime.utcnow()
        
        db.session.commit()
        print("\nEvaluation complete!")

def analyze_player(args):
    """Analyze player behavior and preferences"""
    with app.app_context():
        profile = PlayerProfile.query.filter_by(character_id=args.character_id).first()
        if not profile:
            print(f"Profile not found for character: {args.character_id}")
            sys.exit(1)
        
        print(f"Analyzing player {args.character_id}:")
        print("\nActivity Preferences:")
        for activity, weight in profile.activity_preferences.items():
            print(f"  {activity}: {weight:.2%}")
        
        print("\nBehavioral Metrics:")
        print(f"Risk tolerance: {profile.risk_tolerance:.2%}")
        print(f"Social engagement: {profile.social_engagement:.2%}")
        print(f"Progression speed: {profile.progression_speed:.2%}")
        print(f"Spending behavior: {profile.spending_behavior:.2%}")
        
        print("\nSuccess Rates:")
        for activity, rate in profile.success_rate.items():
            print(f"  {activity}: {rate:.2%}")
        
        # Get recent activity
        recent_activity = ActivityLog.query\
            .filter_by(character_id=args.character_id)\
            .order_by(ActivityLog.created_at.desc())\
            .limit(10).all()
        
        print("\nRecent Activity:")
        for activity in recent_activity:
            print(f"  {activity.created_at}: {activity.activity_type.value}")
            if activity.success is not None:
                result = "Success" if activity.success else "Failure"
                print(f"    Result: {result}")

def adjust_rates(args):
    """Adjust gacha and gambling rates"""
    with app.app_context():
        if args.system == 'gacha':
            systems = GachaSystem.query.all()
            for system in systems:
                print(f"\nGacha System: {system.name}")
                print("Current rates:")
                for grade, rate in system.rates.items():
                    print(f"  {grade}: {rate:.2%}")
                
                if args.view_only:
                    continue
                
                print("\nAdjusting rates based on player activity...")
                # TODO: Implement rate adjustment logic
                
                db.session.commit()
                print("Rates adjusted!")
        
        elif args.system == 'gambling':
            systems = GamblingSystem.query.all()
            for system in systems:
                print(f"\nGambling System: {system.name}")
                print(f"Base odds: {system.base_odds:.2%}")
                print(f"Min bet: {system.min_bet}")
                print(f"Max bet: {system.max_bet}")
                
                if args.view_only:
                    continue
                
                print("\nAdjusting odds based on player activity...")
                # TODO: Implement odds adjustment logic
                
                db.session.commit()
                print("Odds adjusted!")

def export_stats(args):
    """Export AI system statistics"""
    with app.app_context():
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'models': [],
            'gacha_systems': [],
            'gambling_systems': []
        }
        
        # Get model stats
        models = AIModel.query.all()
        for model in models:
            model_stats = {
                'name': model.name,
                'type': model.model_type.value,
                'version': model.version,
                'accuracy': model.accuracy,
                'training_iterations': model.training_iterations,
                'last_trained': model.last_trained.isoformat() if model.last_trained else None,
                'last_evaluation': model.last_evaluation.isoformat() if model.last_evaluation else None
            }
            stats['models'].append(model_stats)
        
        # Get gacha stats
        gacha_systems = GachaSystem.query.all()
        for system in gacha_systems:
            gacha_stats = {
                'name': system.name,
                'rates': system.rates,
                'pity_system': system.pity_system
            }
            stats['gacha_systems'].append(gacha_stats)
        
        # Get gambling stats
        gambling_systems = GamblingSystem.query.all()
        for system in gambling_systems:
            gambling_stats = {
                'name': system.name,
                'base_odds': system.base_odds,
                'min_bet': system.min_bet,
                'max_bet': system.max_bet
            }
            stats['gambling_systems'].append(gambling_stats)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_dir = project_root / 'stats'
        stats_dir.mkdir(exist_ok=True)
        
        stats_file = stats_dir / f'ai_stats_{timestamp}.json'
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Statistics exported to: {stats_file}")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online AI Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train AI model')
    train_parser.add_argument('model', help='Model name to train')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate AI model')
    eval_parser.add_argument('model', help='Model name to evaluate')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze player')
    analyze_parser.add_argument('character_id', type=int, help='Character ID to analyze')
    
    # Adjust command
    adjust_parser = subparsers.add_parser('adjust', help='Adjust rates')
    adjust_parser.add_argument('system', choices=['gacha', 'gambling'],
                             help='System to adjust')
    adjust_parser.add_argument('--view-only', action='store_true',
                             help='Only view current rates')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export statistics')
    
    args = parser.parse_args()
    
    if args.command == 'train':
        train_model(args)
    elif args.command == 'evaluate':
        evaluate_model(args)
    elif args.command == 'analyze':
        analyze_player(args)
    elif args.command == 'adjust':
        adjust_rates(args)
    elif args.command == 'export':
        export_stats(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
