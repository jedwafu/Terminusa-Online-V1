![Terminusa Online Logo](https://github.com/pbellchambers/rustyhack-mmo/raw/main/assets/logo/rustyhack-logo.png "Terminusa Online Logo")

# Terminusa Online
A play-to-earn MMORPG dungeon hunter game inspired by Solo Leveling, integrated with Solana blockchain. The game features multiple currencies (Solana, Exons, and Crystals) and is playable both via a terminal client and through a web browser using xterm.js technology.

[![Build status](https://img.shields.io/github/actions/workflow/status/pbellchambers/rustyhack-mmo/main.yml?branch=main)](https://github.com/pbellchambers/rustyhack-mmo/actions)
[![Downloads](https://img.shields.io/github/downloads/pbellchambers/rustyhack-mmo/total)](https://github.com/pbellchambers/rustyhack-mmo/releases)
[![License](https://img.shields.io/github/license/pbellchambers/rustyhack-mmo)](https://github.com/pbellchambers/rustyhack-mmo/blob/main/LICENSE)



## Play Now
- **Web Browser**: Visit [play.terminusa.online](https://play.terminusa.online) to play directly in your browser
- **Desktop Client**: Download the latest client from [play.terminusa.online/downloads](https://play.terminusa.online/downloads)

## Key Features
- **Play-to-Earn**: Earn real cryptocurrency through gameplay
- **Blockchain Integration**: In-game wallet with Solana, Exons, and Crystals currencies
- **Gates System**: Battle through gates (dungeons) with varying difficulty levels
- **Magic Beasts**: Fight powerful monsters with unique abilities
- **Job System**: Choose from 5 basic classes with limitless progression
- **Guild System**: Form guilds with other players for special quests
- **Party System**: Team up with friends for cooperative gameplay
- **AI-Powered Mechanics**: Dynamic quests and rewards based on your playstyle
- **Marketplace**: Trade items with other players
- **Multi-Platform**: Play via web browser or desktop client

## Getting Started
1. Create an account at [terminusa.online](https://terminusa.online)
2. Choose your preferred platform (web or desktop client)
3. Select your starting job class
4. Begin your journey as a hunter!

## Controls
- **Movement**: ← ↑ → ↓ Arrow keys
- **Combat**: Automatic when entering gates
- **Main Commands**:
  - L - Look around you
  - P - Pick up item underneath you
  - D - Drop item
  - U - Increase stat points after level up
  - M - Change map when standing on map exit location
  - G - Guild menu
  - T - Party menu
  - S - Skills menu
  - H - Hunter shop
  - Q - Quests
- **Quit**: Ctrl-q

## Game Systems

### Currency System
- **Solana**: Blockchain-based cryptocurrency for real-world value transactions
- **Exons**: Solana blockchain-based governance token
- **Crystals**: In-game currency earned through gameplay

### Job System
- **Fighter**: Melee combat specialist
- **Mage**: Magical damage dealer
- **Assassin**: Stealth and critical strikes
- **Archer**: Ranged combat expert
- **Healer**: Support and healing abilities
- Advanced job paths unlock as you progress

### Hunter Class System
- Progress from Class F to Class S
- Higher classes unlock more powerful gates and better rewards
- Upgrade through the Hunter Association

### Gates System
- Gates replace traditional dungeons
- Various difficulty grades based on Solo Leveling anime
- Solo or party options
- Magic beasts of increasing power
- Special Master and Monarch category beasts

### Element System
- 7 elements: neutral, holy, fire, water, lightning, earth, shadow
- Elemental strengths and weaknesses affect combat
- Equipment and skills can have elemental properties

## Technical Components
- **rustyhack_client** - Contains all the client code
- **rustyhack_server** - Contains all the server code
- **rustyhack_lib** - Contains modules shared between client and server
- **assets** - Game assets (maps, monsters, items, etc.)
- **web** - Web interface components

## Assets
Game functionality is defined by files in the `assets` directory:
- **maps** - *.map plain-text* - Map definitions
- **map_exits** - *.json* - Gate exit locations
- **monsters** - *.json* - Magic beast definitions
- **spawns** - *.json* - Spawn locations
- **items** - *.json* - Item definitions
- **skills** - *.json* - Skill definitions
- **jobs** - *.json* - Job class definitions
- **quests** - *.json* - Quest definitions

## Server Deployment
The project includes a deployment script for server management:
```bash
./deploy.sh [command]
```

Available commands:
- `start` - Start the server
- `stop` - Stop the server
- `restart` - Restart the server
- `status` - Check server status
- `update` - Update from git repository
- `backup` - Create a backup
- `restore` - Restore from backup
- `logs` - View server logs
- `config` - Edit configuration
- `deploy-web` - Deploy web components
- `deploy-client` - Deploy client components
- `deploy-all` - Deploy all components

## Building from Source
1. Install latest version of [rust](https://www.rust-lang.org/) (most recently confirmed working `1.85.0`)
2. Download this repository
3. Run `cargo build` in the repository root directory
4. Copy `assets` directory into `target/debug` directory
5. Run `rustyhack_server` and `rustyhack_client` from `target/debug` directory

## Documentation
For more detailed information, see:
- [Comprehensive Analysis](./Terminusa_Online_Comprehensive_Analysis.md) - Detailed project analysis
- [Changelog](./CHANGELOG.md) - Version history and updates
- [Whitepaper](https://terminusa-online.gitbook.io/terminusa-online-whitepaper) - Game concept and tokenomics
