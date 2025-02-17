# Terminusa Online Client

A command-line interface client for Terminusa Online, featuring a Matrix/Solo Leveling-inspired design.

![Terminusa Client](https://raw.githubusercontent.com/terminusa/client/main/docs/images/client-preview.png)

## Features

- Matrix/Solo Leveling-inspired interface
- Real-time gate exploration
- Inventory management
- Character progression
- Party system
- Marketplace integration

## Requirements

- Python 3.10 or later
- Internet connection to connect to the Terminusa Online server (46.250.228.210)
- Terminal with ANSI color support

## Quick Start

### Windows

1. Download and extract the client
2. Double-click `setup.bat`
3. Once setup is complete, run:
```batch
venv\Scripts\activate
python client.py
```

### Linux/Mac

1. Download and extract the client
2. Open terminal in the client directory
3. Run:
```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
./client.py
```

## Available Commands

### Account Management
- `login` - Enter the System
- `register` - Join as a New Hunter
- `logout` - Exit current session

### Character
- `status` - View your Hunter status
- `inventory` - Check your inventory
- `skills` - View acquired skills
- `equip <item_id>` - Equip an item
- `unequip <slot>` - Unequip an item

### Gates
- `gates` - View available gates
- `enter <gate_id>` - Enter a specific gate
- `leave` - Leave current gate
- `explore` - Explore current gate

### Party System
- `party create` - Create a new party
- `party invite <username>` - Invite player to party
- `party accept` - Accept party invitation
- `party leave` - Leave current party

### Marketplace
- `market list` - View marketplace listings
- `market buy <item_id>` - Purchase an item
- `market sell <item_id> <price>` - List item for sale

### System
- `help` - View all available commands
- `quit` - Exit the System

## Troubleshooting

### Connection Issues
If you can't connect to the server:
1. Verify your internet connection
2. Check if the server (46.250.228.210) is accessible:
   ```bash
   ping 46.250.228.210
   ```
3. Ensure your firewall isn't blocking the connection
4. Try using a VPN if the server is blocked in your region

### Client Issues
If the client crashes or behaves unexpectedly:
1. Ensure you're using Python 3.10 or later
2. Try reinstalling dependencies:
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```
3. Check your .env file configuration
4. Look for error messages in the terminal output

### Visual Issues
If the interface doesn't display correctly:
1. Ensure your terminal supports ANSI colors
2. Try using a different terminal emulator
3. Adjust your terminal font (recommended: Consolas, DejaVu Sans Mono)

## Support

For issues and support:
- Create an issue on GitHub
- Contact support at support@terminusa.online
- Join our Discord server for community help

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
