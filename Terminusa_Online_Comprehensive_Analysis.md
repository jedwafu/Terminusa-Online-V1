# Terminusa Online: Comprehensive Project Analysis

## Project Overview
Terminusa Online is a text-based MMORPG play-to-earn dungeon hunter game inspired by Solo Leveling and other dungeon hunter games. It integrates with the Solana blockchain and features multiple currencies (Solana, Exons, and Crystals). The game is playable both via a terminal client and through a web browser using xterm.js technology.

## Current State Analysis

The current codebase is organized into three main Rust crates:

1. **rustyhack_client**: Contains all client-side code
2. **rustyhack_server**: Contains all server-side code
3. **rustyhack_lib**: Contains shared code used by both client and server

Additionally, there's an **assets** directory containing game data files.

### Key Components (Current)

#### rustyhack_lib
This is the shared library containing code used by both client and server:

- **background_map**: Map representation and tile handling
- **consts**: Shared constants like default player positions, colors, etc.
- **ecs**: Entity Component System implementation
  - **components.rs**: Core component definitions (Position, DisplayDetails, Stats, etc.)
  - **player.rs**: Player entity definition
  - **monster.rs**: Monster entity definition
  - **item.rs**: Item entity definition
  - **inventory.rs**: Inventory management
- **network**: Network communication
  - **packets.rs**: Defines message types exchanged between client and server
- **utils**: Utility functions

#### rustyhack_client
The client application that players run to connect to the server:

- **client_game**: Main game loop and UI
  - **screens**: UI rendering for different game screens
  - **input**: Handles player input
    - **commands**: Implements player commands (movement, look, pickup, etc.)
  - **client_updates_handler**: Processes updates from the server
- **client_network_messages**: Network communication
  - **client_network_packet_receiver**: Receives packets from server
  - **map_downloader**: Downloads map data
  - **new_player**: Handles player creation
  - **player_logout**: Handles player logout

#### rustyhack_server
The server application that manages the game world:

- **game**: Core game logic
  - **combat**: Combat system implementation
  - **ecs**: Entity Component System for the server
    - **systems**: Game systems that operate on entities
    - **queries**: Functions to query entity data
  - **map**: Map management
    - **state**: Tracks the state of each map
    - **exits**: Handles map transitions
    - **spawns**: Manages monster spawning
  - **monsters**: Monster behavior
  - **players**: Player management
- **network_messages**: Network communication
  - **packet_receiver**: Receives packets from clients
  - **map_sender**: Sends map data to clients
  - **combat_updates**: Sends combat updates to clients

#### assets
Contains game data files:

- **maps**: ASCII map files (*.map)
- **map_exits**: JSON files defining exit points between maps
- **monsters**: JSON files defining monster types and their properties
- **spawns**: JSON files defining monster spawn locations for each map

## Future Development Requirements

### Infrastructure and Deployment

1. **Server Infrastructure**:
   - VPS with IP 46.250.228.210
   - Domains:
     - https://terminusa.online - Main website and account management
     - https://play.terminusa.online - Game play area (xterm.js)
     - https://marketplace.terminusa.online - Marketplace

2. **Deployment**:
   - AlmaLinux 8.8 with Apache (httpd) + Nginx as webserver and reverse proxy
   - Virtual environment (venv) for Python components
   - TOML configuration (not .env)
   - Database credentials: username: root | password: Jeidel123
   - Deploy.sh script for one-stop deployment and server management

3. **Client Access**:
   - Web browser client using xterm.js
   - Executable client file
   - Both clients connect to the same database
   - Single session enforcement to prevent duplicate logins

### Game Terminology Changes

- Monsters → Magic Beasts
- Dungeons → Gates

### Core Systems

1. **Currency System**:
   - **Solana**: Blockchain-based cryptocurrency for real-world value transactions
   - **Exons**: Solana blockchain-based governance token
   - **Crystals**: Off-chain in-game currency (future tokenization planned)
   - Initial supply for Crystals: 100,000,000
   - Token swapper system for currency exchanges
   - Contract address system for admin to edit Exons contract address

2. **Blockchain Integration**:
   - In-game wallet with 3 currencies
   - Web3 wallet connection
   - Token swapping between currencies

3. **AI Agent System**:
   - Learning from player behaviors:
     - Menu choices
     - In-game activities (gambling vs. gate hunting)
     - Job class preferences
     - Inventory management
     - Achievement progression
   - Powers quest generation, gate difficulty, gacha systems, etc.

4. **Tax System**:
   - 13% tax on Crystal transactions to admin account "adminbb"
   - 13% tax on Exon transactions to admin wallet FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw
   - Additional 2% tax on both currencies for Guild system
   - Tax applies to marketplace transactions and gate rewards

5. **API System**:
   - Shared database serving multiple websites
   - API endpoints for account management, inventory, achievements, etc.

### Game Features

1. **Marketplace System**:
   - Web interface at https://marketplace.terminusa.online
   - In-game trading of items for Exons and Crystals

2. **Hunter Shop System**:
   - Items purchasable with Exons and Crystals:
     - Inventory expansion (10 slots) - Crystals
     - Rename license - Crystals
     - Life potions - Crystals
     - Job reset - Exons
     - Job license - Exons
     - Hunter class upgrade license - Exons
     - Remote shop license - Exons
     - Resurrection potions - Exons

3. **Gacha System**:
   - Mounts and pets purchasable with Exons
   - Grade system: Basic, Intermediate, Excellent, Legendary, Immortal
   - AI-powered probability based on player profile

4. **Referral System**:
   - Rewards based on number of players invited (multiples of 100)
   - Invited players must reach level 50
   - Crystal rewards

5. **Loyalty System**:
   - Rewards for holding Exons and Crystals in in-game wallet
   - Monthly distribution based on percentage of blockchain holdings

6. **Gambling System**:
   - Flip coin game with 2x Crystal rewards
   - AI-powered probability based on player profile

7. **Party System**:
   - No limit on party members
   - Reward sharing decreases with more members
   - Loot quality depends on gate quality, magic beast quality, and party luck

8. **Loot System**:
   - Loot quality based on gate quality, magic beast quality, and luck
   - Currency drops on death (Solana, Exons, Crystals)
   - Surviving party members can collect dead comrades' loot
   - Unclaimed loot goes to admin account

9. **Player Leveling and Stats System**:
   - Solo Leveling anime-inspired progression
   - Stats affect all game systems (combat, gacha, gambling)

10. **Guild System**:
    - Application requires Exons and Crystals
    - Mandatory guild quests with higher rewards but higher taxes

11. **Job System**:
    - 5 basic classes: Fighter, Mage, Assassin, Archer, Healer
    - Limitless job rank progression (every 50 levels)
    - AI-powered job quests
    - Job mixing based on progression

12. **Equipment Durability System**:
    - 100% durability for new equipment
    - Decreases based on damage taken, mana used, and time spent in gates
    - Repair at shops or with remote shop license

13. **Skill System**:
    - AI-powered skill progression
    - Special skills like "Arise" for Shadow Monarch job
    - Health status effects:
      - Burn - Fire damage over time
      - Poisoned - Venom damage over time
      - Frozen - Ice damage over time
      - Feared - Negative aura effect
      - Confused - Psychic effect
      - Dismembered - Slash damage over time
      - Decapitated - Instant death effect
      - Shadow - Resurrection side effect

14. **Combat System**:
    - Automatic combat in gate raids
    - Solo and Party combat options
    - AI-powered loot rewards

15. **Hunter Class System**:
    - Classes from F to S
    - Upgrade through Hunter Association
    - AI-powered appraisal
    - Confidence level system for upgrades

16. **Element System**:
    - 7 elements: neutral, holy, fire, water, lightning, earth, shadow
    - Element dominance affects damage calculations
    - Special relationships (holy vs. shadow)

17. **Equipment Level System**:
    - Crystal-based upgrades
    - Increasing costs with higher levels
    - Max level tied to player level
    - AI-powered success rate

18. **Achievement System**:
    - Bonus stats and Crystal rewards
    - AI-powered based on player activities

## Technical Implementation Considerations

1. **Database Integration**:
   - Shared database for web and client interfaces
   - Session management to prevent duplicate logins

2. **Web Integration**:
   - xterm.js for browser-based terminal interface
   - Website updates for new features
   - Menu bar updates:
     - Home
     - Whitepaper
     - Leaderboards
     - Marketplace
     - Buy Exons
     - Manage Account

3. **Documentation**:
   - Improved README
   - CHANGELOG.md for tracking progress
   - Comprehensive documentation

4. **AI Implementation**:
   - Player behavior tracking
   - Decision-making for various game systems
   - Fairness balancing in gacha and gambling

## Development Roadmap

1. **Infrastructure Setup**:
   - Configure server environments
   - Set up database
   - Create deployment scripts

2. **Core Systems Implementation**:
   - Currency system
   - Blockchain integration
   - AI agent framework

3. **Game Features Development**:
   - Implement marketplace
   - Develop hunter shop
   - Create gate system
   - Build job and skill systems

4. **Web Integration**:
   - xterm.js implementation
   - Website updates
   - API development

5. **Testing and Deployment**:
   - Direct testing in production (current practice)
   - Continuous updates and monitoring

## Conclusion

Terminusa Online is evolving from a basic ASCII roguelike/MMO into a complex play-to-earn game with blockchain integration, AI-powered systems, and extensive game mechanics inspired by Solo Leveling. The development requires significant extensions to the current codebase to implement the new features while maintaining compatibility with both web-based and executable clients.
