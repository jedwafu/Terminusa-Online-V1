# Terminusa Online

A terminal-based MMORPG inspired by Solo Leveling, featuring AI-driven mechanics, a robust economy system, and Web3 integration. Play directly in your browser using a terminal interface powered by xterm.js.

## Features

- **Terminal Interface**: Browser-based terminal gameplay using xterm.js
- **Real-time Interaction**: WebSocket-based communication for instant responses

- **AI-Driven Game Mechanics**: Dynamic quest generation, adaptive difficulty, and personalized achievements
- **Multi-Currency System**: Integrated with Solana blockchain (SOL, EXON, Crystals)
- **Combat System**: Real-time combat with status effects and elemental mechanics
- **Gate System**: Procedurally generated dungeons with varying difficulties
- **Job System**: Multiple classes with unique progression paths
- **Guild System**: Guild management, quests, and guild wars
- **Party System**: Group-based activities with shared rewards
- **Equipment System**: Upgradeable gear with durability mechanics
- **Achievement System**: AI-evaluated progress tracking
- **Gacha System**: Mount and pet summoning with dynamic rates
- **Gambling System**: Coin flip game with AI-adjusted probabilities
- **Hunter Shop**: Special items and licenses

## Prerequisites

### Server Requirements
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 14+ (for Web3 features)
- Solana CLI tools (for blockchain integration)

### Client Requirements
- Modern web browser with WebSocket support
- Node.js and npm for client dependency management

## Installation

### Server Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/terminusa-online.git
cd terminusa-online
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install server dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
python init_db.py
```

### Client Setup

1. Navigate to client directory:
```bash
cd client
```

2. Install client dependencies:
```bash
npm install
```

3. Build client assets:
```bash
npm run postinstall
```

## Configuration

The application can be configured through environment variables or the `.env` file. Key configuration options:

- `FLASK_APP`: Main application file (default: app.py)
- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: PostgreSQL connection URL
- `REDIS_URL`: Redis connection URL
- `SOLANA_RPC_URL`: Solana RPC endpoint
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `ADMIN_WALLET`: Admin wallet address for system operations

See `config.py` for all configuration options.

## Running the Application

1. Start the main server:
```bash
python app.py
```

2. Start the terminal server:
```bash
python terminal_server.py
```

3. Start the client server:
```bash
cd client
npm start
```

4. Start the monitoring server (optional):
```bash
python monitoring_server.py
```

5. Access the game:
- Open https://play.terminusa.online in your browser
- Or locally: http://localhost:3000

## Development

### Project Structure

```
terminusa-online/
├── app.py              # Main application
├── config.py           # Configuration
├── game_manager.py     # Game state coordinator
├── models/            # Database models
├── game_systems/      # Game mechanics
│   ├── ai_agent.py
│   ├── combat_manager.py
│   ├── currency_system.py
│   ├── equipment_system.py
│   ├── gacha_system.py
│   ├── gambling_system.py
│   ├── gate_system.py
│   ├── guild_system.py
│   ├── hunter_shop.py
│   ├── job_system.py
│   └── party_system.py
├── static/           # Static files
└── templates/        # HTML templates
```

### Adding New Features

1. Create new system in `game_systems/`
2. Add models in `models/`
3. Register system with `GameManager`
4. Add configuration in `config.py`
5. Update documentation

### Testing

Run tests with:
```bash
pytest
```

## API Documentation

### Authentication

All game actions require JWT authentication. Get a token via:

```http
POST /api/auth/login
{
    "username": "user",
    "password": "pass"
}
```

### Game Actions

Game actions are performed through:

```http
POST /api/game/action
{
    "action": "action_name",
    "params": {
        // Action-specific parameters
    }
}
```

See API documentation for all available actions.

## Deployment

1. Set up production server:
```bash
./deploy.sh setup
```

2. Configure SSL certificates:
```bash
./deploy.sh ssl
```

3. Deploy application:
```bash
./deploy.sh deploy
```

## Monitoring

Access monitoring dashboard at:
```
https://terminusa.online/admin/monitoring
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@terminusa.online or join our Discord server.

## Acknowledgments

- Solo Leveling for inspiration
- Solana team for blockchain integration support
- Open source community for various libraries used
