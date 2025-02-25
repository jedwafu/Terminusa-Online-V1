# Terminusa Online
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Terminusa Online is a Teminal-based Dungeon Hunter inspired MMORPG with AI-driven mechanics and a robust economy system.

## Key Features

- **Gate System**: Dynamic dungeon system with AI-generated content and difficulty scaling
- **AI-Powered Mechanics**: Intelligent quest generation, combat predictions, and player behavior analysis
- **Web3 Integration**: Solana-based currency system with Exons token
- **Multi-Currency Economy**: Integrated Solana, Exons, and Crystals with token swapping
- **Guild System**: Comprehensive guild management with quests and rewards
- **Party System**: Flexible party system with dynamic reward sharing
- **Job System**: Advanced job progression with AI-driven class quests
- **Achievement System**: AI-tailored achievements and milestones
- **Combat System**: Automated combat with strategic elements
- **Equipment System**: Detailed equipment management with durability
- **Marketplace**: Player-driven economy with trading system

## Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- Node.js 18 or higher (for web client)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/terminusa-online.git
   cd terminusa-online
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
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
   python init_db.py
   ```

6. Run the development server:
   ```bash
   python web_app.py
   ```

1. Clone the repository:
```bash
git clone https://github.com/jedwafu/Terminusa-Online-V1.git
cd Terminusa-Online-V1
```

2. Run the development setup script:
```bash
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh
```

3. Update the .env file with your configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Start the development server:
```bash
source venv/bin/activate
python app_final.py
```

### Deployment

1. Set up SSL certificates:
```bash
sudo certbot certonly --nginx -d terminusa.online -d play.terminusa.online
```

2. Configure Nginx:
```bash
sudo cp nginx/terminusa.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

3. Set up system services:
```bash
sudo cp terminusa.service /etc/systemd/system/
sudo systemctl enable terminusa
sudo systemctl start terminusa
```

## Architecture

### Backend Services

- **Flask Application**: Main web application server
- **Terminal Server**: xterm.js-based game client server
- **Game Server**: Core game mechanics and state management
- **AI Manager**: AI model training and inference
- **Combat Manager**: Combat system processing
- **Economy Manager**: Currency and marketplace management

### Database Schema

- **User Models**: Authentication and profile management
- **Game Models**: Core game mechanics and state
- **Economy Models**: Currency and transaction handling
- **Social Models**: Guild and party management
- **AI Models**: Machine learning model management

### AI Systems

- **Quest Generation**: Dynamic quest creation based on player profile
- **Combat Prediction**: Strategic combat outcome prediction
- **Achievement Evaluation**: Player progress analysis
- **Behavior Analysis**: Player activity pattern recognition

## Development

### Directory Structure

```
Terminusa-Online/
├── app_final.py          # Main application entry point
├── models/              # Database models
├── routes/              # Route handlers
├── scripts/            # Utility scripts
├── static/             # Static assets
├── templates/          # HTML templates
├── migrations/         # Database migrations
├── tests/             # Test suite
└── docs/              # Documentation
```

### Running Tests

```bash
pytest tests/
```

### Code Style

We use Black for code formatting and Flake8 for linting:

```bash
black .
flake8
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code follows our style guidelines and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Inspired by Solo Leveling and other dungeon hunter games
- Special thanks to our early alpha testers

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- Website: [https://terminusa.online](https://terminusa.online)
- Email: [contact@terminusa.online](mailto:contact@terminusa.online)
- Discord: [Join our server](https://discord.gg/terminusa)

## Acknowledgments

- Inspired by Solo Leveling
- Built with Flask and Python
- Powered by Solana blockchain
