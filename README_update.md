# Terminusa Online - Currency System Update

## Overview
This update implements a comprehensive in-game economy with three currencies:
- **Solana**: Web3 cryptocurrency for real-world value transactions
- **Exons**: Game-specific token that bridges web3 and in-game economies
- **Crystals**: Primary in-game currency earned through gameplay

## Key Features

### Currency Management
- **Web3 Integration**
  - Connect Solana wallets
  - Send/receive Exons from web3 wallets
  - Secure blockchain transactions

- **Token Swapper**
  - Swap between Solana, Exons, and Crystals
  - Dynamic conversion rates
  - Automated tax processing

- **Tax System**
  - Base tax rates: 13% for all currencies
  - Additional 2% guild tax
  - Automated distribution to admin accounts

### AI-Powered Systems
- **Dynamic Quest Generation**
  - Analyzes player currency management
  - Adapts to gambling tendencies
  - Rewards based on player behavior

- **Smart Recommendations**
  - Currency management advice
  - Investment opportunities
  - Risk assessment

### Game Mechanics
- **Gate Rewards**
  - Crystal rewards scaled by gate rank
  - Bonus rewards for efficient clearing
  - Party reward distribution

- **Death Penalties**
  - 10% crystal loss on death
  - Random inventory item drops
  - Recoverable by party members

### Shop System
- **Multi-Currency Purchases**
  - Items available for different currencies
  - Strategic pricing for game balance
  - Special items for each currency type

- **License System**
  - Remote shop access (Exons)
  - Class change licenses (Exons)
  - Rename licenses (Crystals)

### Social Features
- **Guild System**
  - Shared benefits and rewards
  - Additional tax implications
  - Guild treasury management

- **Trading System**
  - Direct player-to-player trades
  - Currency and item exchanges
  - Tax-aware transactions

## Technical Implementation

### Core Components
```python
# Currency System Usage
from game_systems.currency_system import CurrencySystem

# Initialize system
currency_system = CurrencySystem()

# Perform currency swap
result = currency_system.swap_currency(
    user=current_user,
    from_currency="solana",
    to_currency="exons",
    amount=Decimal("1.0")
)

# Transfer between users
result = currency_system.transfer_currency(
    from_user=sender,
    to_user=recipient,
    currency="crystals",
    amount=Decimal("1000")
)
```

### AI Integration
```python
# AI Agent Usage
from ai_agent import AIAgent

# Initialize agent
ai_agent = AIAgent()

# Analyze player behavior
profile = ai_agent.analyze_player(user, activity_history)
print(f"Currency Balance Score: {profile['currency_balance']}")
print(f"Gambling Tendency: {profile['gambling_tendency']}")

# Generate currency-related quest
quest = ai_agent.generate_quest(user, activity_history)
```

### Configuration
```python
# Currency Settings
CRYSTAL_MAX_SUPPLY = 100_000_000
CRYSTAL_INITIAL_AMOUNT = 100

# Tax Settings
CRYSTAL_TAX_RATE = 0.13      # 13% base tax
GUILD_CRYSTAL_TAX_RATE = 0.02  # 2% guild tax

# Conversion Rates
SOLANA_TO_EXONS = 100       # 1 SOL = 100 EXON
EXONS_TO_CRYSTALS = 100     # 1 EXON = 100 CRYSTAL
```

## Database Schema Updates

### User Model
```python
class User(db.Model):
    # Currency balances
    solana_balance = db.Column(db.Numeric(precision=18, scale=8), default=0)
    exons_balance = db.Column(db.Numeric(precision=18, scale=8), default=0)
    crystals = db.Column(db.BigInteger, default=0)
```

### Transaction Model
```python
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String)  # 'swap' or 'transfer'
    currency = db.Column(db.String)
    amount = db.Column(db.Numeric(precision=18, scale=8))
    tax_amount = db.Column(db.Numeric(precision=18, scale=8))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

## Future Enhancements
1. **Real-time Price Feeds**
   - Integration with Solana price oracles
   - Dynamic conversion rate adjustments
   - Market-based pricing

2. **Advanced Trading**
   - Limit orders for currency swaps
   - Trading history analytics
   - Market trend predictions

3. **Guild Features**
   - Guild bank system
   - Group investment opportunities
   - Collective trading benefits

4. **AI Improvements**
   - Enhanced behavior analysis
   - Predictive quest generation
   - Dynamic difficulty adjustment

5. **Security Features**
   - Transaction signing
   - Rate limiting
   - Anti-fraud measures

## Installation & Setup
1. Update database schema:
   ```bash
   flask db upgrade
   ```

2. Configure environment variables:
   ```bash
   ADMIN_WALLET=FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw
   CRYSTAL_MAX_SUPPLY=100000000
   ```

3. Initialize currency system:
   ```python
   from game_systems.currency_system import CurrencySystem
   currency_system = CurrencySystem()
   ```

## Testing
Run the test suite:
```bash
pytest tests/test_currency.py
pytest tests/test_ai.py
