-- Terminusa Online Database Setup Script

-- Create database
CREATE DATABASE terminusa_online;

-- Connect to the database
\c terminusa_online

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS game;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS market;
CREATE SCHEMA IF NOT EXISTS social;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set search path
SET search_path TO game, auth, market, social, analytics, public;

-- =============================================
-- Authentication and Player Tables
-- =============================================

-- Players table
CREATE TABLE auth.players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP,
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    session_id VARCHAR(255),
    web3_wallet_address VARCHAR(255),
    CONSTRAINT chk_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Player profiles table
CREATE TABLE game.player_profiles (
    player_id UUID PRIMARY KEY REFERENCES auth.players(id) ON DELETE CASCADE,
    current_map VARCHAR(50) NOT NULL DEFAULT 'Home',
    position_x INTEGER NOT NULL DEFAULT 0,
    position_y INTEGER NOT NULL DEFAULT 0,
    job_class VARCHAR(50) NOT NULL DEFAULT 'Novice',
    hunter_rank VARCHAR(10) NOT NULL DEFAULT 'F',
    level INTEGER NOT NULL DEFAULT 1,
    exp BIGINT NOT NULL DEFAULT 0,
    exp_next BIGINT NOT NULL DEFAULT 1000,
    stat_points INTEGER NOT NULL DEFAULT 0,
    achievement_points INTEGER NOT NULL DEFAULT 0,
    total_gates_cleared INTEGER NOT NULL DEFAULT 0,
    total_playtime BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Player stats table
CREATE TABLE game.player_stats (
    player_id UUID PRIMARY KEY REFERENCES auth.players(id) ON DELETE CASCADE,
    strength FLOAT NOT NULL DEFAULT 10.0,
    dexterity FLOAT NOT NULL DEFAULT 10.0,
    constitution FLOAT NOT NULL DEFAULT 10.0,
    intelligence FLOAT NOT NULL DEFAULT 10.0,
    wisdom FLOAT NOT NULL DEFAULT 10.0,
    charisma FLOAT NOT NULL DEFAULT 10.0,
    luck FLOAT NOT NULL DEFAULT 10.0,
    current_hp FLOAT NOT NULL DEFAULT 100.0,
    max_hp FLOAT NOT NULL DEFAULT 100.0,
    current_mana FLOAT NOT NULL DEFAULT 50.0,
    max_mana FLOAT NOT NULL DEFAULT 50.0,
    hp_regen FLOAT NOT NULL DEFAULT 1.0,
    mana_regen FLOAT NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =============================================
-- Currency System Tables
-- =============================================

-- Currencies table
CREATE TABLE game.currencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    is_blockchain BOOLEAN NOT NULL DEFAULT FALSE,
    contract_address VARCHAR(255),
    max_supply DECIMAL(30,9),
    current_supply DECIMAL(30,9) NOT NULL DEFAULT 0,
    is_gate_reward BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_contract_address CHECK (
        (is_blockchain = FALSE) OR 
        (is_blockchain = TRUE AND contract_address IS NOT NULL)
    )
);

-- Wallets table
CREATE TABLE game.wallets (
    player_id UUID PRIMARY KEY REFERENCES auth.players(id) ON DELETE CASCADE,
    solana_balance DECIMAL(20,9) NOT NULL DEFAULT 0,
    exons_balance DECIMAL(20,9) NOT NULL DEFAULT 0,
    crystals_balance DECIMAL(20,9) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Transactions table
CREATE TABLE game.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_player_id UUID REFERENCES auth.players(id) ON DELETE SET NULL,
    to_player_id UUID REFERENCES auth.players(id) ON DELETE SET NULL,
    currency_id INTEGER NOT NULL REFERENCES game.currencies(id),
    amount DECIMAL(20,9) NOT NULL,
    tax_amount DECIMAL(20,9) NOT NULL DEFAULT 0,
    transaction_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    blockchain_tx_hash VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_tax_amount_nonnegative CHECK (tax_amount >= 0),
    CONSTRAINT chk_transaction_type CHECK (
        transaction_type IN ('transfer', 'purchase', 'reward', 'gate_reward', 'quest_reward', 'tax', 'mint', 'burn')
    ),
    CONSTRAINT chk_status CHECK (
        status IN ('pending', 'completed', 'failed', 'cancelled')
    )
);

-- Tax settings table
CREATE TABLE game.tax_settings (
    id SERIAL PRIMARY KEY,
    currency_id INTEGER NOT NULL REFERENCES game.currencies(id),
    tax_percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    guild_tax_percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    admin_account VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_tax_percentage CHECK (tax_percentage >= 0 AND tax_percentage <= 100),
    CONSTRAINT chk_guild_tax_percentage CHECK (guild_tax_percentage >= 0 AND guild_tax_percentage <= 100)
);

-- =============================================
-- Inventory and Equipment Tables
-- =============================================

-- Inventories table
CREATE TABLE game.inventories (
    player_id UUID PRIMARY KEY REFERENCES auth.players(id) ON DELETE CASCADE,
    max_slots INTEGER NOT NULL DEFAULT 20,
    used_slots INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_used_slots CHECK (used_slots >= 0 AND used_slots <= max_slots)
);

-- Items table
CREATE TABLE game.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    item_type VARCHAR(50) NOT NULL,
    rarity VARCHAR(20) NOT NULL DEFAULT 'common',
    level_requirement INTEGER NOT NULL DEFAULT 1,
    job_requirement VARCHAR(50),
    icon VARCHAR(50),
    is_tradable BOOLEAN NOT NULL DEFAULT TRUE,
    is_droppable BOOLEAN NOT NULL DEFAULT TRUE,
    base_value_crystals INTEGER NOT NULL DEFAULT 0,
    base_value_exons DECIMAL(20,9) NOT NULL DEFAULT 0,
    element VARCHAR(20) DEFAULT 'neutral',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_item_type CHECK (
        item_type IN ('weapon', 'armor', 'potion', 'material', 'quest_item', 'key_item', 'consumable')
    ),
    CONSTRAINT chk_rarity CHECK (
        rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic', 'unique')
    ),
    CONSTRAINT chk_element CHECK (
        element IN ('neutral', 'holy', 'fire', 'water', 'lightning', 'earth', 'shadow')
    )
);

-- Player items table
CREATE TABLE game.player_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES game.items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    durability FLOAT NOT NULL DEFAULT 100.0,
    level INTEGER NOT NULL DEFAULT 0,
    is_equipped BOOLEAN NOT NULL DEFAULT FALSE,
    equipment_slot VARCHAR(20),
    acquired_at TIMESTAMP NOT NULL DEFAULT NOW(),
    custom_name VARCHAR(100),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_durability CHECK (durability >= 0 AND durability <= 100),
    CONSTRAINT chk_level_nonnegative CHECK (level >= 0),
    CONSTRAINT chk_equipment_slot CHECK (
        equipment_slot IS NULL OR
        equipment_slot IN ('weapon', 'armor', 'helmet', 'gloves', 'boots', 'accessory1', 'accessory2')
    )
);

-- Equipment stats table
CREATE TABLE game.equipment_stats (
    player_item_id UUID PRIMARY KEY REFERENCES game.player_items(id) ON DELETE CASCADE,
    damage_min FLOAT DEFAULT 0,
    damage_max FLOAT DEFAULT 0,
    defense FLOAT DEFAULT 0,
    accuracy FLOAT DEFAULT 0,
    evasion FLOAT DEFAULT 0,
    critical_chance FLOAT DEFAULT 0,
    critical_damage FLOAT DEFAULT 0,
    str_bonus FLOAT DEFAULT 0,
    dex_bonus FLOAT DEFAULT 0,
    con_bonus FLOAT DEFAULT 0,
    int_bonus FLOAT DEFAULT 0,
    wis_bonus FLOAT DEFAULT 0,
    cha_bonus FLOAT DEFAULT 0,
    luck_bonus FLOAT DEFAULT 0,
    element_bonus FLOAT DEFAULT 0,
    CONSTRAINT chk_damage_range CHECK (damage_min <= damage_max),
    CONSTRAINT chk_accuracy CHECK (accuracy >= 0 AND accuracy <= 100),
    CONSTRAINT chk_evasion CHECK (evasion >= 0 AND evasion <= 100),
    CONSTRAINT chk_critical_chance CHECK (critical_chance >= 0 AND critical_chance <= 100)
);

-- =============================================
-- Skills and Abilities Tables
-- =============================================

-- Skills table
CREATE TABLE game.skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    skill_type VARCHAR(50) NOT NULL,
    element VARCHAR(20) NOT NULL DEFAULT 'neutral',
    job_requirement VARCHAR(50),
    level_requirement INTEGER NOT NULL DEFAULT 1,
    mana_cost FLOAT NOT NULL DEFAULT 0,
    cooldown INTEGER NOT NULL DEFAULT 0,
    icon VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_skill_type CHECK (
        skill_type IN ('active', 'passive', 'ultimate', 'special')
    ),
    CONSTRAINT chk_element CHECK (
        element IN ('neutral', 'holy', 'fire', 'water', 'lightning', 'earth', 'shadow')
    )
);

-- Skill effects table
CREATE TABLE game.skill_effects (
    skill_id UUID NOT NULL REFERENCES game.skills(id) ON DELETE CASCADE,
    effect_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    base_value FLOAT NOT NULL DEFAULT 0,
    scaling_stat VARCHAR(20),
    scaling_factor FLOAT,
    duration INTEGER,
    status_effect VARCHAR(50),
    status_chance FLOAT,
    CONSTRAINT pk_skill_effects PRIMARY KEY (skill_id, effect_type),
    CONSTRAINT chk_effect_type CHECK (
        effect_type IN ('damage', 'heal', 'buff', 'debuff', 'status', 'summon', 'teleport', 'resurrect')
    ),
    CONSTRAINT chk_target_type CHECK (
        target_type IN ('self', 'single', 'area', 'line', 'cone', 'all')
    ),
    CONSTRAINT chk_scaling_stat CHECK (
        scaling_stat IS NULL OR
        scaling_stat IN ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'luck')
    ),
    CONSTRAINT chk_status_chance CHECK (
        status_chance IS NULL OR
        (status_chance >= 0 AND status_chance <= 100)
    )
);

-- Player skills table
CREATE TABLE game.player_skills (
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES game.skills(id) ON DELETE CASCADE,
    skill_level INTEGER NOT NULL DEFAULT 1,
    experience FLOAT NOT NULL DEFAULT 0,
    is_equipped BOOLEAN NOT NULL DEFAULT FALSE,
    slot_position INTEGER,
    last_used TIMESTAMP,
    CONSTRAINT pk_player_skills PRIMARY KEY (player_id, skill_id),
    CONSTRAINT chk_skill_level_positive CHECK (skill_level > 0),
    CONSTRAINT chk_experience_nonnegative CHECK (experience >= 0),
    CONSTRAINT chk_slot_position CHECK (
        slot_position IS NULL OR
        (slot_position >= 1 AND slot_position <= 10)
    )
);

-- =============================================
-- Gates and Combat Tables
-- =============================================

-- Gates table
CREATE TABLE game.gates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    difficulty_grade VARCHAR(10) NOT NULL,
    min_level INTEGER NOT NULL DEFAULT 1,
    min_hunter_rank VARCHAR(10) NOT NULL DEFAULT 'F',
    max_party_size INTEGER NOT NULL DEFAULT 4,
    map_reference VARCHAR(50) NOT NULL,
    crystal_reward_min INTEGER NOT NULL DEFAULT 0,
    crystal_reward_max INTEGER NOT NULL DEFAULT 0,
    exp_reward_base INTEGER NOT NULL DEFAULT 0,
    time_limit INTEGER,
    cooldown INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_difficulty_grade CHECK (
        difficulty_grade IN ('E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS')
    ),
    CONSTRAINT chk_min_hunter_rank CHECK (
        min_hunter_rank IN ('F', 'E', 'D', 'C', 'B', 'A', 'S')
    ),
    CONSTRAINT chk_reward_range CHECK (crystal_reward_min <= crystal_reward_max)
);

-- Magic beasts table
CREATE TABLE game.magic_beasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    beast_type VARCHAR(50) NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    is_boss BOOLEAN NOT NULL DEFAULT FALSE,
    is_monarch BOOLEAN NOT NULL DEFAULT FALSE,
    element VARCHAR(20) NOT NULL DEFAULT 'neutral',
    icon VARCHAR(50),
    exp_reward INTEGER NOT NULL DEFAULT 0,
    crystal_drop_min INTEGER NOT NULL DEFAULT 0,
    crystal_drop_max INTEGER NOT NULL DEFAULT 0,
    spawn_cooldown INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_level_positive CHECK (level > 0),
    CONSTRAINT chk_element CHECK (
        element IN ('neutral', 'holy', 'fire', 'water', 'lightning', 'earth', 'shadow')
    ),
    CONSTRAINT chk_crystal_drop_range CHECK (crystal_drop_min <= crystal_drop_max)
);

-- Magic beast stats table
CREATE TABLE game.magic_beast_stats (
    beast_id UUID PRIMARY KEY REFERENCES game.magic_beasts(id) ON DELETE CASCADE,
    hp FLOAT NOT NULL DEFAULT 100.0,
    attack FLOAT NOT NULL DEFAULT 10.0,
    defense FLOAT NOT NULL DEFAULT 5.0,
    speed FLOAT NOT NULL DEFAULT 5.0,
    accuracy FLOAT NOT NULL DEFAULT 75.0,
    evasion FLOAT NOT NULL DEFAULT 10.0,
    critical_chance FLOAT NOT NULL DEFAULT 5.0,
    critical_damage FLOAT NOT NULL DEFAULT 150.0,
    CONSTRAINT chk_hp_positive CHECK (hp > 0),
    CONSTRAINT chk_accuracy CHECK (accuracy >= 0 AND accuracy <= 100),
    CONSTRAINT chk_evasion CHECK (evasion >= 0 AND evasion <= 100),
    CONSTRAINT chk_critical_chance CHECK (critical_chance >= 0 AND critical_chance <= 100)
);

-- Gate instances table
CREATE TABLE game.gate_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gate_id UUID NOT NULL REFERENCES game.gates(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_solo BOOLEAN NOT NULL,
    difficulty_modifier FLOAT NOT NULL DEFAULT 1.0,
    loot_quality_modifier FLOAT NOT NULL DEFAULT 1.0,
    CONSTRAINT chk_status CHECK (
        status IN ('pending', 'active', 'completed', 'failed')
    ),
    CONSTRAINT chk_difficulty_modifier_positive CHECK (difficulty_modifier > 0),
    CONSTRAINT chk_loot_quality_modifier_positive CHECK (loot_quality_modifier > 0)
);

-- Gate participants table
CREATE TABLE game.gate_participants (
    gate_instance_id UUID NOT NULL REFERENCES game.gate_instances(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    status VARCHAR(20) NOT NULL DEFAULT 'alive',
    damage_dealt FLOAT NOT NULL DEFAULT 0,
    damage_taken FLOAT NOT NULL DEFAULT 0,
    healing_done FLOAT NOT NULL DEFAULT 0,
    deaths INTEGER NOT NULL DEFAULT 0,
    crystals_earned INTEGER NOT NULL DEFAULT 0,
    exp_earned INTEGER NOT NULL DEFAULT 0,
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    left_at TIMESTAMP,
    CONSTRAINT pk_gate_participants PRIMARY KEY (gate_instance_id, player_id),
    CONSTRAINT chk_role CHECK (
        role IN ('leader', 'member')
    ),
    CONSTRAINT chk_status CHECK (
        status IN ('alive', 'dead', 'shadow', 'decapitated', 'disconnected')
    )
);

-- =============================================
-- Social System Tables
-- =============================================

-- Guilds table
CREATE TABLE social.guilds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    leader_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    level INTEGER NOT NULL DEFAULT 1,
    experience BIGINT NOT NULL DEFAULT 0,
    crystal_balance INTEGER NOT NULL DEFAULT 0,
    exon_balance DECIMAL(20,9) NOT NULL DEFAULT 0,
    member_capacity INTEGER NOT NULL DEFAULT 20,
    emblem VARCHAR(50),
    CONSTRAINT chk_name_length CHECK (LENGTH(name) >= 3),
    CONSTRAINT chk_level_positive CHECK (level > 0),
    CONSTRAINT chk_crystal_balance_nonnegative CHECK (crystal_balance >= 0),
    CONSTRAINT chk_exon_balance_nonnegative CHECK (exon_balance >= 0)
);

-- Guild members table
CREATE TABLE social.guild_members (
    guild_id UUID NOT NULL REFERENCES social.guilds(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    rank VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    contribution_points INTEGER NOT NULL DEFAULT 0,
    weekly_contribution INTEGER NOT NULL DEFAULT 0,
    last_active TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_guild_members PRIMARY KEY (guild_id, player_id),
    CONSTRAINT chk_rank CHECK (
        rank IN ('leader', 'officer', 'member', 'recruit')
    ),
    CONSTRAINT chk_contribution_points_nonnegative CHECK (contribution_points >= 0),
    CONSTRAINT chk_weekly_contribution_nonnegative CHECK (weekly_contribution >= 0)
);

-- Parties table
CREATE TABLE social.parties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    leader_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    max_members INTEGER NOT NULL DEFAULT 4,
    purpose VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'forming',
    CONSTRAINT chk_max_members CHECK (max_members >= 2 AND max_members <= 20),
    CONSTRAINT chk_purpose CHECK (
        purpose IS NULL OR
        purpose IN ('gate', 'quest', 'leveling', 'farming')
    ),
    CONSTRAINT chk_status CHECK (
        status IN ('forming', 'active', 'disbanded')
    )
);

-- Party members table
CREATE TABLE social.party_members (
    party_id UUID NOT NULL REFERENCES social.parties(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    role VARCHAR(20) NOT NULL DEFAULT 'dps',
    ready_status BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_party_members PRIMARY KEY (party_id, player_id),
    CONSTRAINT chk_role CHECK (
        role IN ('tank', 'healer', 'dps', 'support')
    )
);

-- =============================================
-- Marketplace and Economy Tables
-- =============================================

-- Marketplace listings table
CREATE TABLE market.marketplace_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES game.player_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_crystals INTEGER,
    price_exons DECIMAL(20,9),
    currency_id INTEGER NOT NULL REFERENCES game.currencies(id),
    listed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_auction BOOLEAN NOT NULL DEFAULT FALSE,
    min_bid DECIMAL(20,9),
    buy_now_price DECIMAL(20,9),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_price CHECK (
        (currency_id = 1 AND price_crystals IS NOT NULL AND price_crystals > 0) OR
        (currency_id = 2 AND price_exons IS NOT NULL AND price_exons > 0)
    ),
    CONSTRAINT chk_status CHECK (
        status IN ('active', 'sold', 'cancelled', 'expired')
    ),
    CONSTRAINT chk_auction_params CHECK (
        (is_auction = FALSE) OR
        (is_auction = TRUE AND min_bid IS NOT NULL AND min_bid > 0)
    )
);

-- Marketplace bids table
CREATE TABLE market.marketplace_bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES market.marketplace_listings(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    bid_amount DECIMAL(20,9) NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES game.currencies(id),
    bid_time TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    CONSTRAINT chk_bid_amount_positive CHECK (bid_amount > 0),
    CONSTRAINT chk_status CHECK (
        status IN ('active', 'won', 'outbid', 'cancelled')
    )
);

-- Marketplace transactions table
CREATE TABLE market.marketplace_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES market.marketplace_listings(id) ON DELETE CASCADE,
    buyer_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    seller_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES game.items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(20,9) NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES game.currencies(id),
    tax_amount DECIMAL(20,9) NOT NULL DEFAULT 0,
    transaction_time TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_price_positive CHECK (price > 0),
    CONSTRAINT chk_tax_amount_nonnegative CHECK (tax_amount >= 0)
);

-- =============================================
-- AI and Behavior Tracking Tables
-- =============================================

-- Player activity logs table
CREATE TABLE analytics.player_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_details JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id VARCHAR(255),
    location VARCHAR(50)
);

-- Player behavior profiles table
CREATE TABLE analytics.player_behavior_profiles (
    player_id UUID PRIMARY KEY REFERENCES auth.players(id) ON DELETE CASCADE,
    gate_hunting_score FLOAT NOT NULL DEFAULT 0,
    gambling_score FLOAT NOT NULL DEFAULT 0,
    trading_score FLOAT NOT NULL DEFAULT 0,
    social_score FLOAT NOT NULL DEFAULT 0,
    risk_tolerance FLOAT NOT NULL DEFAULT 0,
    spending_pattern VARCHAR(20) NOT NULL DEFAULT 'unknown',
    play_style VARCHAR(20) NOT NULL DEFAULT 'balanced',
    active_hours JSONB,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_scores CHECK (
        gate_hunting_score >= 0 AND gate_hunting_score <= 100 AND
        gambling_score >= 0 AND gambling_score <= 100 AND
        trading_score >= 0 AND trading_score <= 100 AND
        social_score >= 0 AND social_score <= 100 AND
        risk_tolerance >= 0 AND risk_tolerance <= 100
    ),
    CONSTRAINT chk_spending_pattern CHECK (
        spending_pattern IN ('unknown', 'f2p', 'minnow', 'dolphin', 'whale')
    ),
    CONSTRAINT chk_play_style CHECK (
        play_style IN ('balanced', 'casual', 'competitive', 'social', 'collector', 'achiever', 'explorer')
    )
);

-- AI decision logs table
CREATE TABLE analytics.ai_decision_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    decision_type VARCHAR(50) NOT NULL,
    input_factors JSONB NOT NULL,
    output_result JSONB NOT NULL,
    confidence_score FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    applied BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- =============================================
-- Miscellaneous Tables
-- =============================================

-- Achievements table
CREATE TABLE game.achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'normal',
    crystal_reward INTEGER NOT NULL DEFAULT 0,
    stat_bonus_type VARCHAR(20),
    stat_bonus_value FLOAT,
    icon VARCHAR(50),
    hidden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_category CHECK (
        category IN ('combat', 'exploration', 'social', 'collection', 'progression', 'special')
    ),
    CONSTRAINT chk_difficulty CHECK (
        difficulty IN ('easy', 'normal', 'hard', 'expert', 'master')
    ),
    CONSTRAINT chk_stat_bonus_type CHECK (
        stat_bonus_type IS NULL OR
        stat_bonus_type IN ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma', 'luck', 'all')
    )
);

-- Player achievements table
CREATE TABLE game.player_achievements (
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES game.achievements(id) ON DELETE CASCADE,
    progress FLOAT NOT NULL DEFAULT 0,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    reward_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_player_achievements PRIMARY KEY (player_id, achievement_id),
    CONSTRAINT chk_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Quests table
CREATE TABLE game.quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    quest_type VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'normal',
    min_level INTEGER NOT NULL DEFAULT 1,
    job_requirement VARCHAR(50),
    crystal_reward INTEGER NOT NULL DEFAULT 0,
    exp_reward INTEGER NOT NULL DEFAULT 0,
    item_rewards JSONB,
    prerequisite_quests JSONB,
    is_repeatable BOOLEAN NOT NULL DEFAULT FALSE,
    cooldown INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_quest_type CHECK (
        quest_type IN ('main', 'side', 'daily', 'weekly', 'guild', 'job', 'special')
    ),
    CONSTRAINT chk_difficulty CHECK (
        difficulty IN ('easy', 'normal', 'hard', 'expert', 'master')
    ),
    CONSTRAINT chk_cooldown CHECK (
        (is_repeatable = FALSE) OR
        (is_repeatable = TRUE AND cooldown IS NOT NULL AND cooldown > 0)
    )
);

-- Player quests table
CREATE TABLE game.player_quests (
    player_id UUID NOT NULL REFERENCES auth.players(id) ON DELETE CASCADE,
    quest_id UUID NOT NULL REFERENCES game.quests(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    progress JSONB NOT NULL DEFAULT '{"objectives": []}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    times_completed INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT pk_player_quests PRIMARY KEY (player_id, quest_id),
    CONSTRAINT chk_status CHECK (
        status IN ('available', 'active', 'completed', 'failed', 'cooldown')
    )
);

-- System settings table
CREATE TABLE game.system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES auth.players(id) ON DELETE SET NULL
);

-- =============================================
-- Create Indexes
-- =============================================

-- Players indexes
CREATE INDEX idx_players_username ON auth.players(username);
CREATE INDEX idx_players_email ON auth.players(email);
CREATE INDEX idx_players_session_id ON auth.players(session_
