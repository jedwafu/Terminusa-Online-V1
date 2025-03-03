"""
Gambling System for Terminusa Online
"""
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import random
import logging
from models import db, User, Transaction, GamblingStats
from game_systems.ai_agent import AIAgent
from game_config import GAMBLING_CONFIG

logger = logging.getLogger(__name__)

class GamblingSystem:
    """Handles gambling activities with AI-driven probabilities"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self._daily_bets = {}  # Track daily bets per user

    def flip_coin(self, user: User, bet_amount: int) -> Dict:
        """Play coin flip game with crystals"""
        try:
            # Validate bet amount
            if bet_amount < GAMBLING_CONFIG['min_bet']:
                return {
                    "success": False,
                    "message": f"Minimum bet is {GAMBLING_CONFIG['min_bet']} crystals"
                }
            
            if bet_amount > GAMBLING_CONFIG['max_bet']:
                return {
                    "success": False,
                    "message": f"Maximum bet is {GAMBLING_CONFIG['max_bet']} crystals"
                }

            # Check user balance
            if user.crystals < bet_amount:
                return {
                    "success": False,
                    "message": "Insufficient crystals"
                }

            # Check daily bet limit
            if not self._check_daily_limit(user):
                return {
                    "success": False,
                    "message": f"Daily bet limit of {GAMBLING_CONFIG['max_daily_bets']} reached"
                }

            # Get AI-adjusted win probability
            win_probability = self._calculate_win_probability(user)
            
            # Determine outcome
            won = random.random() < win_probability
            
            # Process bet
            if won:
                winnings = int(bet_amount * GAMBLING_CONFIG['win_multiplier'])
                user.crystals += (winnings - bet_amount)  # Add net winnings
                result_message = f"Won {winnings} crystals!"
            else:
                user.crystals -= bet_amount
                result_message = f"Lost {bet_amount} crystals"

            # Record transaction and stats
            self._record_gambling_activity(user, bet_amount, won, winnings if won else 0)

            db.session.commit()

            return {
                "success": True,
                "message": result_message,
                "won": won,
                "amount": winnings if won else -bet_amount,
                "new_balance": user.crystals
            }

        except Exception as e:
            logger.error(f"Failed to process coin flip: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to process bet"
            }

    def get_gambling_stats(self, user: User) -> Dict:
        """Get user's gambling statistics"""
        try:
            stats = GamblingStats.query.filter_by(user_id=user.id).first()
            if not stats:
                return {
                    "success": True,
                    "stats": {
                        "total_bets": 0,
                        "total_won": 0,
                        "total_lost": 0,
                        "biggest_win": 0,
                        "win_streak": 0,
                        "best_win_streak": 0
                    }
                }

            return {
                "success": True,
                "stats": {
                    "total_bets": stats.total_bets,
                    "total_won": stats.total_won,
                    "total_lost": stats.total_lost,
                    "biggest_win": stats.biggest_win,
                    "win_streak": stats.current_streak,
                    "best_win_streak": stats.best_streak,
                    "win_rate": (
                        stats.total_won / stats.total_bets
                        if stats.total_bets > 0 else 0
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get gambling stats: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get gambling stats"
            }

    def _check_daily_limit(self, user: User) -> bool:
        """Check if user has reached daily bet limit"""
        try:
            today = datetime.utcnow().date()
            
            # Clear old data
            if user.id in self._daily_bets:
                last_bet_date = self._daily_bets[user.id]['date']
                if last_bet_date < today:
                    self._daily_bets[user.id] = {
                        'date': today,
                        'count': 0
                    }
            else:
                self._daily_bets[user.id] = {
                    'date': today,
                    'count': 0
                }
            
            # Check limit
            if self._daily_bets[user.id]['count'] >= GAMBLING_CONFIG['max_daily_bets']:
                return False
            
            # Increment count
            self._daily_bets[user.id]['count'] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to check daily limit: {str(e)}")
            return False

    def _calculate_win_probability(self, user: User) -> float:
        """Calculate AI-adjusted win probability"""
        try:
            # Get base probability
            base_prob = GAMBLING_CONFIG['base_win_chance']
            
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return base_prob

            # Adjust based on player behavior
            adjustments = {
                # Reward consistent players
                'loyalty': self._calculate_loyalty_adjustment(profile),
                
                # Balance for unlucky players
                'luck': self._calculate_luck_adjustment(user),
                
                # Risk-based adjustment
                'risk': self._calculate_risk_adjustment(profile),
                
                # Activity-based adjustment
                'activity': self._calculate_activity_adjustment(profile)
            }
            
            # Apply adjustments
            final_prob = base_prob + sum(adjustments.values())
            
            # Ensure probability stays within reasonable bounds
            return max(0.40, min(0.55, final_prob))

        except Exception as e:
            logger.error(f"Failed to calculate win probability: {str(e)}")
            return GAMBLING_CONFIG['base_win_chance']

    def _calculate_loyalty_adjustment(self, profile: Dict) -> float:
        """Calculate loyalty-based probability adjustment"""
        try:
            # Check player's progression and consistency
            progression_score = profile['progression_rate']['progression_score']
            
            # Small boost for loyal players
            if progression_score > 0.8:
                return 0.02  # +2%
            elif progression_score > 0.6:
                return 0.01  # +1%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_luck_adjustment(self, user: User) -> float:
        """Calculate luck-based probability adjustment"""
        try:
            stats = GamblingStats.query.filter_by(user_id=user.id).first()
            if not stats or stats.total_bets < 10:
                return 0.0

            # Calculate recent win rate
            recent_transactions = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type == 'gamble',
                Transaction.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).all()

            if not recent_transactions:
                return 0.0

            recent_wins = sum(
                1 for t in recent_transactions
                if t.metadata.get('won', False)
            )
            recent_win_rate = recent_wins / len(recent_transactions)

            # Adjust probability for unlucky players
            if recent_win_rate < 0.3:  # Very unlucky
                return 0.03  # +3%
            elif recent_win_rate < 0.4:  # Somewhat unlucky
                return 0.02  # +2%
            elif recent_win_rate > 0.6:  # Lucky
                return -0.02  # -2%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_risk_adjustment(self, profile: Dict) -> float:
        """Calculate risk-based probability adjustment"""
        try:
            risk_score = profile['risk_profile']['risk_tolerance_score']
            
            # Reward moderate risk-takers
            if 0.4 <= risk_score <= 0.6:
                return 0.01  # +1%
            elif risk_score > 0.8:  # High risk takers
                return -0.01  # -1%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_activity_adjustment(self, profile: Dict) -> float:
        """Calculate activity-based probability adjustment"""
        try:
            # Check if player is actively participating in other activities
            activities = profile['activity_patterns']['distribution']
            gambling_ratio = activities.get('gambling', 0)
            
            # Encourage balanced gameplay
            if gambling_ratio > 0.5:  # Too focused on gambling
                return -0.02  # -2%
            elif gambling_ratio < 0.2:  # Balanced player
                return 0.01  # +1%
            return 0.0

        except Exception:
            return 0.0

    def _record_gambling_activity(self, user: User, bet_amount: int, won: bool, winnings: int) -> None:
        """Record gambling activity and update stats"""
        try:
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='gamble',
                currency='crystals',
                amount=bet_amount,
                metadata={
                    'won': won,
                    'winnings': winnings
                }
            )
            db.session.add(transaction)

            # Update or create stats
            stats = GamblingStats.query.filter_by(user_id=user.id).first()
            if not stats:
                stats = GamblingStats(user_id=user.id)
                db.session.add(stats)

            stats.total_bets += 1
            if won:
                stats.total_won += 1
                stats.current_streak += 1
                stats.best_streak = max(stats.best_streak, stats.current_streak)
                stats.biggest_win = max(stats.biggest_win, winnings)
            else:
                stats.total_lost += 1
                stats.current_streak = 0

            stats.last_bet_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to record gambling activity: {str(e)}")
            raise

    def get_leaderboard(self) -> Dict:
        """Get gambling leaderboard"""
        try:
            # Get top winners by total winnings
            top_winners = db.session.query(
                Transaction.user_id,
                db.func.sum(Transaction.amount).label('total_winnings')
            ).filter(
                Transaction.type == 'gamble',
                Transaction.metadata['won'].as_boolean() == True
            ).group_by(
                Transaction.user_id
            ).order_by(
                db.desc('total_winnings')
            ).limit(10).all()

            # Get top streaks
            top_streaks = GamblingStats.query.order_by(
                db.desc(GamblingStats.best_streak)
            ).limit(10).all()

            return {
                "success": True,
                "leaderboard": {
                    "top_winners": [
                        {
                            "user_id": winner.user_id,
                            "username": User.query.get(winner.user_id).username,
                            "total_winnings": winner.total_winnings
                        }
                        for winner in top_winners
                    ],
                    "top_streaks": [
                        {
                            "user_id": streak.user_id,
                            "username": User.query.get(streak.user_id).username,
                            "best_streak": streak.best_streak
                        }
                        for streak in top_streaks
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Failed to get leaderboard: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get leaderboard"
            }
