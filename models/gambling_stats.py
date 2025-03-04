"""
Gambling Statistics model for Terminusa Online
"""
from datetime import datetime
from models import db

class GamblingStats(db.Model):
    __tablename__ = 'gambling_stats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Lifetime Stats
    total_bets = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    total_losses = db.Column(db.Integer, default=0)
    crystals_wagered = db.Column(db.BigInteger, default=0)
    crystals_won = db.Column(db.BigInteger, default=0)
    crystals_lost = db.Column(db.BigInteger, default=0)
    biggest_win = db.Column(db.BigInteger, default=0)
    biggest_loss = db.Column(db.BigInteger, default=0)
    longest_win_streak = db.Column(db.Integer, default=0)
    longest_loss_streak = db.Column(db.Integer, default=0)
    
    # Current Session Stats
    current_win_streak = db.Column(db.Integer, default=0)
    current_loss_streak = db.Column(db.Integer, default=0)
    daily_bets = db.Column(db.Integer, default=0)
    daily_crystals_wagered = db.Column(db.BigInteger, default=0)
    
    # Timestamps
    last_bet = db.Column(db.DateTime)
    last_win = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id: int):
        self.user_id = user_id

    def record_bet(self, amount: int, won: bool) -> None:
        """Record a gambling bet"""
        self.total_bets += 1
        self.daily_bets += 1
        self.crystals_wagered += amount
        self.daily_crystals_wagered += amount
        self.last_bet = datetime.utcnow()
        
        if won:
            self.total_wins += 1
            self.crystals_won += amount * 2  # Assuming 2x payout
            self.current_win_streak += 1
            self.current_loss_streak = 0
            self.last_win = datetime.utcnow()
            
            if amount * 2 > self.biggest_win:
                self.biggest_win = amount * 2
                
            if self.current_win_streak > self.longest_win_streak:
                self.longest_win_streak = self.current_win_streak
        else:
            self.total_losses += 1
            self.crystals_lost += amount
            self.current_loss_streak += 1
            self.current_win_streak = 0
            
            if amount > self.biggest_loss:
                self.biggest_loss = amount
                
            if self.current_loss_streak > self.longest_loss_streak:
                self.longest_loss_streak = self.current_loss_streak

    def reset_daily_stats(self) -> None:
        """Reset daily gambling statistics"""
        self.daily_bets = 0
        self.daily_crystals_wagered = 0

    def get_win_rate(self) -> float:
        """Get win rate percentage"""
        if self.total_bets == 0:
            return 0.0
        return (self.total_wins / self.total_bets) * 100

    def get_profit_loss(self) -> int:
        """Get total profit/loss"""
        return self.crystals_won - self.crystals_lost

    def to_dict(self) -> dict:
        """Convert gambling stats to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lifetime_stats': {
                'total_bets': self.total_bets,
                'total_wins': self.total_wins,
                'total_losses': self.total_losses,
                'crystals_wagered': self.crystals_wagered,
                'crystals_won': self.crystals_won,
                'crystals_lost': self.crystals_lost,
                'biggest_win': self.biggest_win,
                'biggest_loss': self.biggest_loss,
                'win_rate': self.get_win_rate(),
                'profit_loss': self.get_profit_loss(),
                'longest_win_streak': self.longest_win_streak,
                'longest_loss_streak': self.longest_loss_streak
            },
            'current_session': {
                'current_win_streak': self.current_win_streak,
                'current_loss_streak': self.current_loss_streak,
                'daily_bets': self.daily_bets,
                'daily_crystals_wagered': self.daily_crystals_wagered
            },
            'timestamps': {
                'last_bet': self.last_bet.isoformat() if self.last_bet else None,
                'last_win': self.last_win.isoformat() if self.last_win else None,
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat()
            }
        }
