# Terminusa Online Database Schema

This document outlines the database schema for Terminusa Online, designed to support the game's new features including blockchain integration, multiple currencies, and expanded game mechanics.

## Database Technology

We'll use a hybrid approach:
- **PostgreSQL**: For relational data (player accounts, transactions, game state)
- **Redis**: For caching and real-time data (active sessions, market prices)
- **File-based storage**: For game assets and configurations (maps, items, skills)

## Schema Design

### Core Tables

#### `players`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| username | VARCHAR(50) | Unique username |
| password_hash | VARCHAR(255) | Hashed password |
| email | VARCHAR(100) | Player's email |
| created_at | TIMESTAMP | Account creation time |
| last_login | TIMESTAMP | Last login time |
| is_online | BOOLEAN | Current online status |
| is_admin | BOOLEAN | Admin privileges |
| session_id | VARCHAR(255) | Current session ID |
| web3_wallet_address | VARCHAR(255) | Solana wallet address |

#### `player_profiles`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| current_map | VARCHAR(50) | Current map/location |
| position_x | INTEGER | X coordinate |
| position_y | INTEGER | Y coordinate |
| job_class | VARCHAR(50) | Current job class |
| hunter_rank | VARCHAR(10) | Hunter rank (F to S) |
| level | INTEGER | Player level |
| exp | BIGINT | Current experience points |
| exp_next | BIGINT | Experience needed for next level |
| stat_points | INTEGER | Available stat points |
| achievement_points | INTEGER | Achievement points earned |
| total_gates_cleared | INTEGER | Total number of gates cleared |
| total_playtime | BIGINT | Total playtime in seconds |

#### `player_stats`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| strength | FLOAT | Strength stat |
| dexterity | FLOAT | Dexterity stat |
| constitution | FLOAT | Constitution stat |
| intelligence | FLOAT | Intelligence stat |
| wisdom | FLOAT | Wisdom stat |
| charisma | FLOAT | Charisma stat |
| luck | FLOAT | Luck stat |
| current_hp | FLOAT | Current hit points |
| max_hp | FLOAT | Maximum hit points |
| current_mana | FLOAT | Current mana points |
| max_mana | FLOAT | Maximum mana points |
| hp_regen | FLOAT | HP regeneration rate |
| mana_regen | FLOAT | Mana regeneration rate |

### Currency System

#### `wallets`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| solana_balance | DECIMAL(20,9) | Solana balance |
| exons_balance | DECIMAL(20,9) | Exons balance |
| crystals_balance | DECIMAL(20,9) | Crystals balance |
| last_updated | TIMESTAMP | Last balance update |

#### `currencies`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(50) | Currency name |
| symbol | VARCHAR(10) | Currency symbol |
| is_blockchain | BOOLEAN | Is blockchain-based |
| contract_address | VARCHAR(255) | Contract address (if blockchain) |
| max_supply | DECIMAL(30,9) | Maximum supply |
| current_supply | DECIMAL(30,9) | Current supply |
| is_gate_reward | BOOLEAN | Can be earned in gates |
| created_at | TIMESTAMP | Creation timestamp |

#### `transactions`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| from_player_id | UUID | Sender (NULL if system) |
| to_player_id | UUID | Recipient (NULL if system) |
| currency_id | INTEGER | Foreign key to currencies |
| amount | DECIMAL(20,9) | Transaction amount |
| tax_amount | DECIMAL(20,9) | Tax amount |
| transaction_type | VARCHAR(50) | Type (transfer, purchase, reward, etc.) |
| reference_id | UUID | Related entity (item, gate, etc.) |
| status | VARCHAR(20) | Status (pending, completed, failed) |
| blockchain_tx_hash | VARCHAR(255) | Blockchain transaction hash |
| created_at | TIMESTAMP | Transaction timestamp |
| notes | TEXT | Additional information |

#### `tax_settings`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| currency_id | INTEGER | Foreign key to currencies |
| tax_percentage | DECIMAL(5,2) | Base tax percentage |
| guild_tax_percentage | DECIMAL(5,2) | Additional guild tax |
| admin_account | VARCHAR(255) | Admin account for tax collection |
| updated_at | TIMESTAMP | Last update timestamp |

### Inventory and Equipment

#### `inventories`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| max_slots | INTEGER | Maximum inventory slots |
| used_slots | INTEGER | Used inventory slots |
| last_updated | TIMESTAMP | Last update timestamp |

#### `items`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Item name |
| description | TEXT | Item description |
| item_type | VARCHAR(50) | Type (weapon, armor, potion, etc.) |
| rarity | VARCHAR(20) | Rarity (common, rare, etc.) |
| level_requirement | INTEGER | Required level to use |
| job_requirement | VARCHAR(50) | Required job to use |
| icon | VARCHAR(50) | Icon reference |
| is_tradable | BOOLEAN | Can be traded |
| is_droppable | BOOLEAN | Can be dropped |
| base_value_crystals | INTEGER | Base value in crystals |
| base_value_exons | DECIMAL(20,9) | Base value in exons |
| element | VARCHAR(20) | Elemental property |

#### `player_items`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| player_id | UUID | Foreign key to players |
| item_id | UUID | Foreign key to items |
| quantity | INTEGER | Item quantity |
| durability | FLOAT | Current durability (0-100) |
| level | INTEGER | Item enhancement level |
| is_equipped | BOOLEAN | Currently equipped |
| equipment_slot | VARCHAR(20) | Equipped slot |
| acquired_at | TIMESTAMP | Acquisition timestamp |
| custom_name | VARCHAR(100) | Custom name (if renamed) |

#### `equipment_stats`
| Column | Type | Description |
|--------|------|-------------|
| player_item_id | UUID | Foreign key to player_items |
| damage_min | FLOAT | Minimum damage (weapons) |
| damage_max | FLOAT | Maximum damage (weapons) |
| defense | FLOAT | Defense value (armor) |
| accuracy | FLOAT | Accuracy percentage |
| evasion | FLOAT | Evasion percentage |
| critical_chance | FLOAT | Critical hit chance |
| critical_damage | FLOAT | Critical damage multiplier |
| str_bonus | FLOAT | Strength bonus |
| dex_bonus | FLOAT | Dexterity bonus |
| con_bonus | FLOAT | Constitution bonus |
| int_bonus | FLOAT | Intelligence bonus |
| wis_bonus | FLOAT | Wisdom bonus |
| cha_bonus | FLOAT | Charisma bonus |
| luck_bonus | FLOAT | Luck bonus |
| element_bonus | FLOAT | Elemental damage/resistance bonus |

### Skills and Abilities

#### `skills`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Skill name |
| description | TEXT | Skill description |
| skill_type | VARCHAR(50) | Type (active, passive, etc.) |
| element | VARCHAR(20) | Elemental property |
| job_requirement | VARCHAR(50) | Required job |
| level_requirement | INTEGER | Required level |
| mana_cost | FLOAT | Mana cost to use |
| cooldown | INTEGER | Cooldown in seconds |
| icon | VARCHAR(50) | Icon reference |

#### `skill_effects`
| Column | Type | Description |
|--------|------|-------------|
| skill_id | UUID | Foreign key to skills |
| effect_type | VARCHAR(50) | Effect type (damage, heal, status, etc.) |
| target_type | VARCHAR(20) | Target (self, single, area, etc.) |
| base_value | FLOAT | Base effect value |
| scaling_stat | VARCHAR(20) | Stat used for scaling |
| scaling_factor | FLOAT | Scaling factor |
| duration | INTEGER | Effect duration in seconds |
| status_effect | VARCHAR(50) | Status effect applied |
| status_chance | FLOAT | Chance to apply status |

#### `player_skills`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| skill_id | UUID | Foreign key to skills |
| skill_level | INTEGER | Skill level |
| experience | FLOAT | Skill experience |
| is_equipped | BOOLEAN | Is in active skill slots |
| slot_position | INTEGER | Position in skill bar |
| last_used | TIMESTAMP | Last usage timestamp |

### Gates and Combat

#### `gates`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Gate name |
| description | TEXT | Gate description |
| difficulty_grade | VARCHAR(10) | Difficulty (E, D, C, B, A, S) |
| min_level | INTEGER | Minimum level requirement |
| min_hunter_rank | VARCHAR(10) | Minimum hunter rank |
| max_party_size | INTEGER | Maximum party size |
| map_reference | VARCHAR(50) | Reference to map file |
| crystal_reward_min | INTEGER | Minimum crystal reward |
| crystal_reward_max | INTEGER | Maximum crystal reward |
| exp_reward_base | INTEGER | Base experience reward |
| time_limit | INTEGER | Time limit in seconds |
| cooldown | INTEGER | Cooldown between entries |

#### `magic_beasts`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Beast name |
| description | TEXT | Beast description |
| beast_type | VARCHAR(50) | Type classification |
| level | INTEGER | Beast level |
| is_boss | BOOLEAN | Is a boss monster |
| is_monarch | BOOLEAN | Is a monarch-class beast |
| element | VARCHAR(20) | Elemental property |
| icon | VARCHAR(50) | Icon reference |
| exp_reward | INTEGER | Experience reward |
| crystal_drop_min | INTEGER | Minimum crystal drop |
| crystal_drop_max | INTEGER | Maximum crystal drop |
| spawn_cooldown | INTEGER | Respawn cooldown |

#### `magic_beast_stats`
| Column | Type | Description |
|--------|------|-------------|
| beast_id | UUID | Foreign key to magic_beasts |
| hp | FLOAT | Hit points |
| attack | FLOAT | Attack power |
| defense | FLOAT | Defense power |
| speed | FLOAT | Speed |
| accuracy | FLOAT | Accuracy percentage |
| evasion | FLOAT | Evasion percentage |
| critical_chance | FLOAT | Critical hit chance |
| critical_damage | FLOAT | Critical damage multiplier |

#### `gate_instances`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| gate_id | UUID | Foreign key to gates |
| created_at | TIMESTAMP | Creation timestamp |
| started_at | TIMESTAMP | Start timestamp |
| completed_at | TIMESTAMP | Completion timestamp |
| status | VARCHAR(20) | Status (pending, active, completed, failed) |
| is_solo | BOOLEAN | Solo or party instance |
| difficulty_modifier | FLOAT | Additional difficulty modifier |
| loot_quality_modifier | FLOAT | Loot quality modifier |

#### `gate_participants`
| Column | Type | Description |
|--------|------|-------------|
| gate_instance_id | UUID | Foreign key to gate_instances |
| player_id | UUID | Foreign key to players |
| role | VARCHAR(20) | Role in party |
| status | VARCHAR(20) | Status (alive, dead, shadow, etc.) |
| damage_dealt | FLOAT | Total damage dealt |
| damage_taken | FLOAT | Total damage taken |
| healing_done | FLOAT | Total healing done |
| deaths | INTEGER | Number of deaths |
| crystals_earned | INTEGER | Crystals earned |
| exp_earned | INTEGER | Experience earned |
| joined_at | TIMESTAMP | Join timestamp |
| left_at | TIMESTAMP | Leave timestamp |

### Social Systems

#### `guilds`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Guild name |
| description | TEXT | Guild description |
| leader_id | UUID | Foreign key to players (leader) |
| created_at | TIMESTAMP | Creation timestamp |
| level | INTEGER | Guild level |
| experience | BIGINT | Guild experience |
| crystal_balance | INTEGER | Guild crystal balance |
| exon_balance | DECIMAL(20,9) | Guild exon balance |
| member_capacity | INTEGER | Maximum members |
| emblem | VARCHAR(50) | Guild emblem reference |

#### `guild_members`
| Column | Type | Description |
|--------|------|-------------|
| guild_id | UUID | Foreign key to guilds |
| player_id | UUID | Foreign key to players |
| rank | VARCHAR(50) | Guild rank (member, officer, etc.) |
| joined_at | TIMESTAMP | Join timestamp |
| contribution_points | INTEGER | Contribution points |
| weekly_contribution | INTEGER | Weekly contribution |
| last_active | TIMESTAMP | Last activity timestamp |

#### `parties`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Party name |
| leader_id | UUID | Foreign key to players (leader) |
| created_at | TIMESTAMP | Creation timestamp |
| is_public | BOOLEAN | Publicly joinable |
| max_members | INTEGER | Maximum members |
| purpose | VARCHAR(50) | Party purpose (gate, quest, etc.) |
| status | VARCHAR(20) | Status (forming, active, disbanded) |

#### `party_members`
| Column | Type | Description |
|--------|------|-------------|
| party_id | UUID | Foreign key to parties |
| player_id | UUID | Foreign key to players |
| joined_at | TIMESTAMP | Join timestamp |
| role | VARCHAR(20) | Role in party |
| ready_status | BOOLEAN | Ready status |

### Marketplace and Economy

#### `marketplace_listings`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| seller_id | UUID | Foreign key to players |
| item_id | UUID | Foreign key to player_items |
| quantity | INTEGER | Quantity for sale |
| price_crystals | INTEGER | Price in crystals |
| price_exons | DECIMAL(20,9) | Price in exons |
| currency_id | INTEGER | Preferred currency |
| listed_at | TIMESTAMP | Listing timestamp |
| expires_at | TIMESTAMP | Expiration timestamp |
| status | VARCHAR(20) | Status (active, sold, cancelled) |
| is_auction | BOOLEAN | Is auction format |
| min_bid | DECIMAL(20,9) | Minimum bid (auctions) |
| buy_now_price | DECIMAL(20,9) | Buy now price (auctions) |

#### `marketplace_bids`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| listing_id | UUID | Foreign key to marketplace_listings |
| bidder_id | UUID | Foreign key to players |
| bid_amount | DECIMAL(20,9) | Bid amount |
| currency_id | INTEGER | Currency used |
| bid_time | TIMESTAMP | Bid timestamp |
| status | VARCHAR(20) | Status (active, won, outbid, cancelled) |

#### `marketplace_transactions`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| listing_id | UUID | Foreign key to marketplace_listings |
| buyer_id | UUID | Foreign key to players |
| seller_id | UUID | Foreign key to players |
| item_id | UUID | Foreign key to items |
| quantity | INTEGER | Quantity purchased |
| price | DECIMAL(20,9) | Final price |
| currency_id | INTEGER | Currency used |
| tax_amount | DECIMAL(20,9) | Tax amount |
| transaction_time | TIMESTAMP | Transaction timestamp |

### AI and Behavior Tracking

#### `player_activity_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| player_id | UUID | Foreign key to players |
| activity_type | VARCHAR(50) | Activity type |
| activity_details | JSONB | Detailed activity data |
| timestamp | TIMESTAMP | Activity timestamp |
| session_id | VARCHAR(255) | Session ID |
| location | VARCHAR(50) | Location in game |

#### `player_behavior_profiles`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| gate_hunting_score | FLOAT | Preference for gate hunting |
| gambling_score | FLOAT | Preference for gambling |
| trading_score | FLOAT | Preference for trading |
| social_score | FLOAT | Preference for social activities |
| risk_tolerance | FLOAT | Risk tolerance level |
| spending_pattern | VARCHAR(20) | Spending pattern category |
| play_style | VARCHAR(20) | Overall play style |
| active_hours | JSONB | Typical active hours |
| last_updated | TIMESTAMP | Last update timestamp |

#### `ai_decision_logs`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| player_id | UUID | Foreign key to players |
| decision_type | VARCHAR(50) | Type of decision |
| input_factors | JSONB | Factors considered |
| output_result | JSONB | Decision result |
| confidence_score | FLOAT | AI confidence level |
| timestamp | TIMESTAMP | Decision timestamp |
| applied | BOOLEAN | Whether decision was applied |

### Miscellaneous

#### `achievements`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Achievement name |
| description | TEXT | Achievement description |
| category | VARCHAR(50) | Category |
| difficulty | VARCHAR(20) | Difficulty level |
| crystal_reward | INTEGER | Crystal reward |
| stat_bonus_type | VARCHAR(20) | Stat bonus type |
| stat_bonus_value | FLOAT | Stat bonus value |
| icon | VARCHAR(50) | Icon reference |
| hidden | BOOLEAN | Is hidden until earned |

#### `player_achievements`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| achievement_id | UUID | Foreign key to achievements |
| progress | FLOAT | Progress percentage |
| completed | BOOLEAN | Completion status |
| completed_at | TIMESTAMP | Completion timestamp |
| reward_claimed | BOOLEAN | Reward claimed status |

#### `quests`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Quest name |
| description | TEXT | Quest description |
| quest_type | VARCHAR(50) | Type (main, side, daily, etc.) |
| difficulty | VARCHAR(20) | Difficulty level |
| min_level | INTEGER | Minimum level requirement |
| job_requirement | VARCHAR(50) | Job requirement |
| crystal_reward | INTEGER | Crystal reward |
| exp_reward | INTEGER | Experience reward |
| item_rewards | JSONB | Item rewards |
| prerequisite_quests | JSONB | Required previous quests |
| is_repeatable | BOOLEAN | Can be repeated |
| cooldown | INTEGER | Cooldown if repeatable |

#### `player_quests`
| Column | Type | Description |
|--------|------|-------------|
| player_id | UUID | Foreign key to players |
| quest_id | UUID | Foreign key to quests |
| status | VARCHAR(20) | Status (available, active, completed) |
| progress | JSONB | Progress on objectives |
| started_at | TIMESTAMP | Start timestamp |
| completed_at | TIMESTAMP | Completion timestamp |
| times_completed | INTEGER | Times completed if repeatable |

#### `system_settings`
| Column | Type | Description |
|--------|------|-------------|
| key | VARCHAR(100) | Setting key |
| value | TEXT | Setting value |
| description | TEXT | Setting description |
| updated_at | TIMESTAMP | Last update timestamp |
| updated_by | UUID | Foreign key to players (admin) |

## Indexes

Important indexes to optimize query performance:

1. `players` table:
   - `username` (unique)
   - `email` (unique)
   - `session_id`
   - `web3_wallet_address`

2. `transactions` table:
   - `from_player_id`
   - `to_player_id`
   - `currency_id`
   - `created_at`
   - `status`

3. `player_items` table:
   - `player_id, item_id`
   - `is_equipped`

4. `marketplace_listings` table:
   - `seller_id`
   - `status, expires_at`
   - `item_id`

5. `player_activity_logs` table:
   - `player_id, timestamp`
   - `activity_type`

## Relationships

The database schema includes numerous relationships:

- One-to-one relationships (e.g., player to wallet)
- One-to-many relationships (e.g., player to items)
- Many-to-many relationships (e.g., players to guilds via guild_members)

## Migration Strategy

To migrate from the current file-based system to this database schema:

1. Create the database structure
2. Develop data migration scripts
3. Test with sample data
4. Perform a staged migration
5. Validate data integrity
6. Switch to the new system

## Backup and Recovery

Implement regular backups:
- Full database dumps daily
- Transaction log backups hourly
- Point-in-time recovery capability
- Automated backup verification

## Security Considerations

- Encrypt sensitive data (passwords, email addresses)
- Use parameterized queries to prevent SQL injection
- Implement row-level security for admin-only data
- Audit logging for sensitive operations
- Regular security reviews
