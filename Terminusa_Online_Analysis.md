# Terminusa Online: Project Analysis

## Project Overview
Terminusa Online (also referred to as "Rustyhack MMO" in the README) is a text-based multiplayer online game written in Rust. It's a roguelike/MMO hybrid with ASCII graphics that allows players to move around maps, fight monsters and other players, collect items, and level up characters.

## Project Structure

The project is organized into three main Rust crates:

1. **rustyhack_client**: Contains all client-side code
2. **rustyhack_server**: Contains all server-side code
3. **rustyhack_lib**: Contains shared code used by both client and server

Additionally, there's an **assets** directory containing game data files.

### Key Components

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

## Game Workflow

### Server Initialization
1. The server initializes logging and sets up panic handling
2. It binds to UDP and TCP sockets for communication
3. It loads all maps, monster definitions, and spawn locations
4. It attempts to load a saved world state or creates a new one
5. It starts the main game loop

### Server Game Loop
The server runs several update schedules at different intervals:
1. **Player updates**: Processed immediately when received
2. **Server tick updates**: Run at regular intervals (defined by SERVER_GAME_TICK)
3. **Health regeneration**: Runs every 2 server ticks
4. **Entity broadcast updates**: Sends entity positions to clients
5. **World backup**: Periodically saves the world state

### Client Initialization
1. The client initializes logging and sets up panic handling
2. It gets player setup details (server address, player name)
3. It binds to a socket for communication
4. It downloads map data from the server
5. It sends a new player request to the server
6. It initializes the console engine for rendering
7. It starts the main game loop

### Client Game Loop
1. The client waits for the target frame rate
2. It sends player movement updates to the server
3. It processes updates received from the server
4. It handles player input for commands
5. It updates and redraws the game screens
6. It checks if the player wants to quit

### Network Communication
- The client and server communicate using UDP for game state updates
- TCP is used for larger data transfers like map downloads
- Messages are serialized using bincode
- The main message types are defined in `rustyhack_lib/src/network/packets.rs`

### Entity Component System (ECS)
The game uses the Legion ECS library to manage entities:
1. **Components**: Position, DisplayDetails, Stats, Inventory, etc.
2. **Systems**: Functions that operate on entities with specific components
3. **Resources**: Shared data like maps and combat state

### Combat System
Combat is resolved based on:
1. Attacker's weapon damage and strength
2. Defender's armor
3. Accuracy based on dexterity
4. Random chance

### Map System
Maps are defined in ASCII text files:
- `#` characters represent walls
- Special characters like `>` represent exits
- Maps must be enclosed by boundary walls
- Map exits are defined in JSON files

### Monster System
Monsters are defined in JSON files with:
- Display properties (icon, color)
- Stats (HP, strength, dexterity, etc.)
- Equipment (weapon, armor)
- Spawn locations defined in separate JSON files

## Game Features
- Movement using arrow keys
- Combat by moving into enemies
- Item pickup and dropping
- Character stat improvement
- Map transitions
- Multiplayer interaction

## Technical Details
- Written in Rust
- Uses console_engine for terminal UI
- Uses laminar and message_io for networking
- Uses legion for entity component system
- Uses bincode and serde for serialization
- Uses crossbeam-channel for thread communication
