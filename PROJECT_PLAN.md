# Terminusa Online - Project Plan

## Overview
Terminusa Online is an MMORPG play-to-earn dungeon hunter game integrated with Solana blockchain. The game features text-based gameplay accessible via web browser using xterm.js technology.

## Infrastructure

### Domains
- Main Website: https://terminusa.online
- Game Interface: https://play.terminusa.online

### Server
- VPS IP: 46.250.228.210
- Admin Wallet: FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw

## Core Systems

### 1. Currency System
- **Currencies**
  - Solana (Blockchain)
  - Exons (Token)
  - Crystals (In-game)
- **Features**
  - Token swapper system (Solana ↔ Exons)
  - Crystal exchange (Exons ↔ Crystals)
  - Initial Crystal supply: 100,000,000
  - Configurable off-chain currencies
  - Gate earnings configuration

### 2. Wallet System
- In-game wallet integration
- Web3 wallet connection
- Currency management
- Transaction history

### 3. Tax System
- **Rates**
  - 13% Crystal tax to admin
  - 13% Exon tax to admin wallet
  - +2% Crystal tax for Guild system
  - +2% Exon tax for Guild system
  - Gate rewards taxation

### 4. Combat System
- **Solo Mode**
  - Higher loot rates
  - Individual progression
- **Party Mode**
  - Shared rewards
  - Dynamic party size
  - Reward distribution based on party size

### 5. Gate System (Dungeons)
- **Features**
  - Solo/Party options
  - Grade system (F to S)
  - Magic Beast encounters
  - Equipment durability
  - Health status effects
  - Resurrection mechanics
- **AI Integration**
  - Dynamic difficulty
  - Reward scaling
  - Player adaptation

### 6. Job System
- **Base Classes**
  - Fighter
  - Mage
  - Assassin
  - Archer
  - Healer
- **Features**
  - Unlimited rank progression
  - Job mixing
  - Class-specific quests
  - Level-based advancement (50-level intervals)

### 7. Skill System
- **Features**
  - Class-based skills
  - Special abilities
  - "Arise" skill (Shadow Monarch exclusive)
- **Status Effects**
  - Burn
  - Poison
  - Frozen
  - Fear
  - Confusion
  - Dismemberment
  - Decapitation
  - Shadow state

### 8. Economy Systems

#### A. Marketplace
- Web interface
- Item trading
- Currency exchange
- Transaction history

#### B. Trading System
- Player-to-player trading
- Item ↔ Currency exchange
- Equipment trading

#### C. Hunter Shop
- **Items**
  - Inventory expansions
  - Rename licenses
  - Potions
  - Job-related items
  - Equipment repair
  - Resurrection items

#### D. Gacha System
- Mount and pet acquisition
- Grade system (Basic to Immortal)
- AI-powered probability
- Player activity influence

### 9. Social Systems

#### A. Guild System
- Member management
- Guild quests
- Resource requirements
- Tax implications

#### B. Party System
- Unlimited members
- Dynamic reward sharing
- Party formation
- Member management

### 10. Progression Systems

#### A. Player Development
- Level progression
- Stat allocation
- Equipment management
- Achievement tracking

#### B. Hunter Class System
- F to S classification
- Upgrade requirements
- AI-powered appraisal
- Confidence level system

### 11. Quest System
- AI-generated quests
- Activity-based generation
- Class-specific quests
- Progression quests

### 12. Reward Systems

#### A. Referral System
- Level 50 requirement
- 100-player milestones
- Crystal rewards
- Tracking system

#### B. Loyalty System
- Monthly rewards
- Blockchain percentage based
- Token holding incentives

#### C. Achievement System
- Stat bonuses
- Crystal rewards
- AI-powered goals
- Progress tracking

## UI/UX Requirements

### Website Design
- Inspiration:
  - Solo Leveling (https://sololeveling.netmarble.com/en)
  - Matrix (https://www.whatisthematrix.com/universe/)

### Navigation
- Home
- Whitepaper
- Leaderboards
- Marketplace
- Buy Exons
- Login/Register

### Leaderboards
- Top Hunters
- Top Guilds
- Statistics display

## Technical Implementation

### Phase 1: Core Infrastructure
- [ ] Server setup
- [ ] Domain configuration
- [ ] Database design
- [ ] Authentication system

### Phase 2: Game Systems
- [ ] Currency implementation
- [ ] Combat mechanics
- [ ] Gate system
- [ ] Job system

### Phase 3: Economy
- [ ] Marketplace
- [ ] Trading system
- [ ] Shop system
- [ ] Gacha system

### Phase 4: Social Features
- [ ] Guild system
- [ ] Party system
- [ ] Chat system
- [ ] Friend system

### Phase 5: AI Integration
- [ ] Quest generation
- [ ] Gate adaptation
- [ ] Player analysis
- [ ] Reward balancing

### Phase 6: Web Interface
- [ ] Website design
- [ ] Game interface
- [ ] Marketplace UI
- [ ] Leaderboards

### Phase 7: Testing & Deployment
- [ ] System testing
- [ ] Balance testing
- [ ] Security audit
- [ ] Launch preparation

## Monitoring & Maintenance

### System Health
- Service status
- Performance metrics
- Error tracking
- Security monitoring

### Game Balance
- Economy monitoring
- Player progression
- Quest difficulty
- Reward distribution

### Updates & Patches
- Bug fixes
- Balance adjustments
- Content updates
- Feature additions
