//! Player Account System for Terminusa Online
//!
//! This module implements the expanded player account system,
//! including wallet integration, stats, leveling, job classes, and hunter ranks.

use std::fmt;
use std::error::Error;
use std::str::FromStr;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use rust_decimal::Decimal;
use sqlx::{PgPool, Row, postgres::PgRow};
use crate::currency_system::{CurrencyType, CurrencyService};
use crate::blockchain_integration::BlockchainService;

/// Represents a player account
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Player {
    /// Unique identifier for the player
    pub id: Uuid,
    /// Username
    pub username: String,
    /// Email address
    pub email: String,
    /// Whether the player is currently online
    pub is_online: bool,
    /// Whether the player has admin privileges
    pub is_admin: bool,
    /// Current session ID
    pub session_id: Option<String>,
    /// Web3 wallet address
    pub web3_wallet_address: Option<String>,
    /// When the player account was created
    pub created_at: DateTime<Utc>,
    /// When the player last logged in
    pub last_login: Option<DateTime<Utc>>,
}

/// Represents a player's profile
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerProfile {
    /// Player ID
    pub player_id: Uuid,
    /// Current map
    pub current_map: String,
    /// X coordinate
    pub position_x: i32,
    /// Y coordinate
    pub position_y: i32,
    /// Current job class
    pub job_class: JobClass,
    /// Hunter rank
    pub hunter_rank: HunterRank,
    /// Player level
    pub level: i32,
    /// Current experience points
    pub exp: i64,
    /// Experience needed for next level
    pub exp_next: i64,
    /// Available stat points
    pub stat_points: i32,
    /// Achievement points
    pub achievement_points: i32,
    /// Total gates cleared
    pub total_gates_cleared: i32,
    /// Total playtime in seconds
    pub total_playtime: i64,
    /// When the profile was created
    pub created_at: DateTime<Utc>,
    /// When the profile was last updated
    pub updated_at: DateTime<Utc>,
}

/// Represents a player's stats
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerStats {
    /// Player ID
    pub player_id: Uuid,
    /// Strength stat
    pub strength: f32,
    /// Dexterity stat
    pub dexterity: f32,
    /// Constitution stat
    pub constitution: f32,
    /// Intelligence stat
    pub intelligence: f32,
    /// Wisdom stat
    pub wisdom: f32,
    /// Charisma stat
    pub charisma: f32,
    /// Luck stat
    pub luck: f32,
    /// Current hit points
    pub current_hp: f32,
    /// Maximum hit points
    pub max_hp: f32,
    /// Current mana points
    pub current_mana: f32,
    /// Maximum mana points
    pub max_mana: f32,
    /// HP regeneration rate
    pub hp_regen: f32,
    /// Mana regeneration rate
    pub mana_regen: f32,
    /// When the stats were created
    pub created_at: DateTime<Utc>,
    /// When the stats were last updated
    pub updated_at: DateTime<Utc>,
}

/// Represents a job class
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum JobClass {
    /// Novice (starting class)
    Novice,
    /// Warrior (physical damage dealer)
    Warrior,
    /// Mage (magical damage dealer)
    Mage,
    /// Ranger (ranged damage dealer)
    Ranger,
    /// Cleric (healer)
    Cleric,
    /// Rogue (stealth and critical hits)
    Rogue,
}

impl fmt::Display for JobClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            JobClass::Novice => write!(f, "Novice"),
            JobClass::Warrior => write!(f, "Warrior"),
            JobClass::Mage => write!(f, "Mage"),
            JobClass::Ranger => write!(f, "Ranger"),
            JobClass::Cleric => write!(f, "Cleric"),
            JobClass::Rogue => write!(f, "Rogue"),
        }
    }
}

impl FromStr for JobClass {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "novice" => Ok(JobClass::Novice),
            "warrior" => Ok(JobClass::Warrior),
            "mage" => Ok(JobClass::Mage),
            "ranger" => Ok(JobClass::Ranger),
            "cleric" => Ok(JobClass::Cleric),
            "rogue" => Ok(JobClass::Rogue),
            _ => Err(format!("Unknown job class: {}", s)),
        }
    }
}

/// Represents a hunter rank
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum HunterRank {
    /// F Rank (lowest)
    F,
    /// E Rank
    E,
    /// D Rank
    D,
    /// C Rank
    C,
    /// B Rank
    B,
    /// A Rank
    A,
    /// S Rank (highest)
    S,
}

impl fmt::Display for HunterRank {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            HunterRank::F => write!(f, "F"),
            HunterRank::E => write!(f, "E"),
            HunterRank::D => write!(f, "D"),
            HunterRank::C => write!(f, "C"),
            HunterRank::B => write!(f, "B"),
            HunterRank::A => write!(f, "A"),
            HunterRank::S => write!(f, "S"),
        }
    }
}

impl FromStr for HunterRank {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_uppercase().as_str() {
            "F" => Ok(HunterRank::F),
            "E" => Ok(HunterRank::E),
            "D" => Ok(HunterRank::D),
            "C" => Ok(HunterRank::C),
            "B" => Ok(HunterRank::B),
            "A" => Ok(HunterRank::A),
            "S" => Ok(HunterRank::S),
            _ => Err(format!("Unknown hunter rank: {}", s)),
        }
    }
}

impl HunterRank {
    /// Get the next hunter rank
    pub fn next(&self) -> Option<HunterRank> {
        match self {
            HunterRank::F => Some(HunterRank::E),
            HunterRank::E => Some(HunterRank::D),
            HunterRank::D => Some(HunterRank::C),
            HunterRank::C => Some(HunterRank::B),
            HunterRank::B => Some(HunterRank::A),
            HunterRank::A => Some(HunterRank::S),
            HunterRank::S => None, // Already at highest rank
        }
    }

    /// Get the previous hunter rank
    pub fn prev(&self) -> Option<HunterRank> {
        match self {
            HunterRank::F => None, // Already at lowest rank
            HunterRank::E => Some(HunterRank::F),
            HunterRank::D => Some(HunterRank::E),
            HunterRank::C => Some(HunterRank::D),
            HunterRank::B => Some(HunterRank::C),
            HunterRank::A => Some(HunterRank::B),
            HunterRank::S => Some(HunterRank::A),
        }
    }

    /// Get the numeric value of the rank (for calculations)
    pub fn value(&self) -> i32 {
        match self {
            HunterRank::F => 1,
            HunterRank::E => 2,
            HunterRank::D => 3,
            HunterRank::C => 4,
            HunterRank::B => 5,
            HunterRank::A => 6,
            HunterRank::S => 7,
        }
    }
}

/// Represents a stat type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum StatType {
    /// Strength (physical damage)
    Strength,
    /// Dexterity (accuracy and evasion)
    Dexterity,
    /// Constitution (health and defense)
    Constitution,
    /// Intelligence (magic damage and mana)
    Intelligence,
    /// Wisdom (magic defense and mana regen)
    Wisdom,
    /// Charisma (social interactions and prices)
    Charisma,
    /// Luck (critical hits and drops)
    Luck,
}

impl fmt::Display for StatType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StatType::Strength => write!(f, "Strength"),
            StatType::Dexterity => write!(f, "Dexterity"),
            StatType::Constitution => write!(f, "Constitution"),
            StatType::Intelligence => write!(f, "Intelligence"),
            StatType::Wisdom => write!(f, "Wisdom"),
            StatType::Charisma => write!(f, "Charisma"),
            StatType::Luck => write!(f, "Luck"),
        }
    }
}

impl FromStr for StatType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "strength" | "str" => Ok(StatType::Strength),
            "dexterity" | "dex" => Ok(StatType::Dexterity),
            "constitution" | "con" => Ok(StatType::Constitution),
            "intelligence" | "int" => Ok(StatType::Intelligence),
            "wisdom" | "wis" => Ok(StatType::Wisdom),
            "charisma" | "cha" => Ok(StatType::Charisma),
            "luck" | "luk" => Ok(StatType::Luck),
            _ => Err(format!("Unknown stat type: {}", s)),
        }
    }
}

/// Error types for player account operations
#[derive(Debug)]
pub enum PlayerError {
    /// Database error
    Database(sqlx::Error),
    /// Player not found
    PlayerNotFound { id: Uuid },
    /// Username already exists
    UsernameExists { username: String },
    /// Email already exists
    EmailExists { email: String },
    /// Invalid credentials
    InvalidCredentials,
    /// Insufficient stat points
    InsufficientStatPoints { required: i32, available: i32 },
    /// Invalid stat value
    InvalidStatValue { reason: String },
    /// Unauthorized operation
    Unauthorized { reason: String },
    /// System error
    System { reason: String },
}

impl fmt::Display for PlayerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PlayerError::Database(e) => write!(f, "Database error: {}", e),
            PlayerError::PlayerNotFound { id } => write!(f, "Player not found: {}", id),
            PlayerError::UsernameExists { username } => {
                write!(f, "Username already exists: {}", username)
            }
            PlayerError::EmailExists { email } => write!(f, "Email already exists: {}", email),
            PlayerError::InvalidCredentials => write!(f, "Invalid credentials"),
            PlayerError::InsufficientStatPoints { required, available } => {
                write!(
                    f,
                    "Insufficient stat points: required {}, available {}",
                    required, available
                )
            }
            PlayerError::InvalidStatValue { reason } => write!(f, "Invalid stat value: {}", reason),
            PlayerError::Unauthorized { reason } => write!(f, "Unauthorized: {}", reason),
            PlayerError::System { reason } => write!(f, "System error: {}", reason),
        }
    }
}

impl Error for PlayerError {}

impl From<sqlx::Error> for PlayerError {
    fn from(error: sqlx::Error) -> Self {
        PlayerError::Database(error)
    }
}

/// Player account service for managing player accounts
pub struct PlayerAccountService {
    /// Database connection pool
    db_pool: PgPool,
    /// Currency service for handling currency operations
    currency_service: Option<CurrencyService>,
    /// Blockchain service for handling blockchain operations
    blockchain_service: Option<BlockchainService>,
}

impl PlayerAccountService {
    /// Create a new player account service
    pub fn new(db_pool: PgPool) -> Self {
        PlayerAccountService {
            db_pool,
            currency_service: None,
            blockchain_service: None,
        }
    }

    /// Set the currency service
    pub fn with_currency_service(mut self, currency_service: CurrencyService) -> Self {
        self.currency_service = Some(currency_service);
        self
    }

    /// Set the blockchain service
    pub fn with_blockchain_service(mut self, blockchain_service: BlockchainService) -> Self {
        self.blockchain_service = Some(blockchain_service);
        self
    }

    /// Register a new player
    pub async fn register_player(
        &self,
        username: &str,
        email: &str,
        password: &str,
    ) -> Result<Player, PlayerError> {
        // Validate inputs
        if username.len() < 3 {
            return Err(PlayerError::System {
                reason: "Username must be at least 3 characters".to_string(),
            });
        }

        if !email.contains('@') {
            return Err(PlayerError::System {
                reason: "Invalid email format".to_string(),
            });
        }

        if password.len() < 8 {
            return Err(PlayerError::System {
                reason: "Password must be at least 8 characters".to_string(),
            });
        }

        // Check if username or email already exists
        let existing_user = sqlx::query!(
            r#"
            SELECT username, email FROM auth.players
            WHERE username = $1 OR email = $2
            "#,
            username,
            email
        )
        .fetch_optional(&self.db_pool)
        .await?;

        if let Some(existing) = existing_user {
            if existing.username == username {
                return Err(PlayerError::UsernameExists {
                    username: username.to_string(),
                });
            } else {
                return Err(PlayerError::EmailExists {
                    email: email.to_string(),
                });
            }
        }

        // Hash password
        let password_hash = bcrypt::hash(password, bcrypt::DEFAULT_COST).map_err(|e| {
            PlayerError::System {
                reason: format!("Failed to hash password: {}", e),
            }
        })?;

        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Create player account
        let player = sqlx::query_as!(
            Player,
            r#"
            INSERT INTO auth.players (
                id, username, password_hash, email, 
                is_online, is_admin, created_at
            )
            VALUES (
                uuid_generate_v4(), $1, $2, $3, 
                false, false, NOW()
            )
            RETURNING 
                id, username, email, is_online, is_admin, 
                session_id, web3_wallet_address, created_at, last_login
            "#,
            username,
            password_hash,
            email
        )
        .fetch_one(&mut tx)
        .await?;

        // Create player profile
        sqlx::query!(
            r#"
            INSERT INTO game.player_profiles (
                player_id, current_map, position_x, position_y,
                job_class, hunter_rank, level, exp, exp_next,
                stat_points, achievement_points, total_gates_cleared,
                total_playtime, created_at, updated_at
            )
            VALUES (
                $1, 'Home', 0, 0,
                'Novice', 'F', 1, 0, 1000,
                0, 0, 0,
                0, NOW(), NOW()
            )
            "#,
            player.id
        )
        .execute(&mut tx)
        .await?;

        // Create player stats
        sqlx::query!(
            r#"
            INSERT INTO game.player_stats (
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            )
            VALUES (
                $1, 10, 10, 10,
                10, 10, 10, 10,
                100, 100, 50, 50,
                1, 0.5, NOW(), NOW()
            )
            "#,
            player.id
        )
        .execute(&mut tx)
        .await?;

        // Create player inventory
        sqlx::query!(
            r#"
            INSERT INTO game.inventories (
                player_id, max_slots, used_slots, last_updated
            )
            VALUES (
                $1, 20, 0, NOW()
            )
            "#,
            player.id
        )
        .execute(&mut tx)
        .await?;

        // Create player wallet if currency service is available
        if let Some(currency_service) = &self.currency_service {
            currency_service.create_wallet(player.id).await.map_err(|e| {
                PlayerError::System {
                    reason: format!("Failed to create wallet: {}", e),
                }
            })?;
        }

        // Commit transaction
        tx.commit().await?;

        Ok(player)
    }

    /// Login a player
    pub async fn login_player(
        &self,
        username: &str,
        password: &str,
    ) -> Result<(Player, String), PlayerError> {
        // Get player by username
        let player_data = sqlx::query!(
            r#"
            SELECT id, username, email, password_hash, is_online, is_admin, 
                   session_id, web3_wallet_address, created_at, last_login
            FROM auth.players
            WHERE username = $1
            "#,
            username
        )
        .fetch_optional(&self.db_pool)
        .await?;

        let player_data = match player_data {
            Some(data) => data,
            None => return Err(PlayerError::InvalidCredentials),
        };

        // Verify password
        let password_matches = bcrypt::verify(password, &player_data.password_hash).map_err(|e| {
            PlayerError::System {
                reason: format!("Failed to verify password: {}", e),
            }
        })?;

        if !password_matches {
            return Err(PlayerError::InvalidCredentials);
        }

        // Generate session token
        let session_id = Uuid::new_v4().to_string();

        // Update player session and login time
        let player = sqlx::query_as!(
            Player,
            r#"
            UPDATE auth.players
            SET 
                session_id = $2,
                last_login = NOW(),
                is_online = true
            WHERE id = $1
            RETURNING 
                id, username, email, is_online, is_admin, 
                session_id, web3_wallet_address, created_at, last_login
            "#,
            player_data.id,
            session_id
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok((player, session_id))
    }

    /// Logout a player
    pub async fn logout_player(&self, player_id: Uuid) -> Result<(), PlayerError> {
        sqlx::query!(
            r#"
            UPDATE auth.players
            SET 
                session_id = NULL,
                is_online = false
            WHERE id = $1
            "#,
            player_id
        )
        .execute(&self.db_pool)
        .await?;

        Ok(())
    }

    /// Get a player by ID
    pub async fn get_player(&self, player_id: Uuid) -> Result<Player, PlayerError> {
        let player = sqlx::query_as!(
            Player,
            r#"
            SELECT 
                id, username, email, is_online, is_admin, 
                session_id, web3_wallet_address, created_at, last_login
            FROM auth.players
            WHERE id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::PlayerNotFound { id: player_id })?;

        Ok(player)
    }

    /// Get a player by username
    pub async fn get_player_by_username(&self, username: &str) -> Result<Player, PlayerError> {
        let player = sqlx::query_as!(
            Player,
            r#"
            SELECT 
                id, username, email, is_online, is_admin, 
                session_id, web3_wallet_address, created_at, last_login
            FROM auth.players
            WHERE username = $1
            "#,
            username
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::System {
            reason: format!("Player not found: {}", username),
        })?;

        Ok(player)
    }

    /// Get a player's profile
    pub async fn get_player_profile(&self, player_id: Uuid) -> Result<PlayerProfile, PlayerError> {
        let profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            SELECT 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            FROM game.player_profiles
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::System {
            reason: format!("Player profile not found: {}", player_id),
        })?;

        Ok(profile)
    }

    /// Get a player's stats
    pub async fn get_player_stats(&self, player_id: Uuid) -> Result<PlayerStats, PlayerError> {
        let stats = sqlx::query_as!(
            PlayerStats,
            r#"
            SELECT 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            FROM game.player_stats
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::System {
            reason: format!("Player stats not found: {}", player_id),
        })?;

        Ok(stats)
    }

    /// Update a player's position
    pub async fn update_player_position(
        &self,
        player_id: Uuid,
        map: &str,
        x: i32,
        y: i32,
    ) -> Result<PlayerProfile, PlayerError> {
        let profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                current_map = $2,
                position_x = $3,
                position_y = $4,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            "#,
            player_id,
            map,
            x,
            y
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::PlayerNotFound { id: player_id })?;

        Ok(profile)
    }

    /// Update a player's job class
    pub async fn update_player_job_class(
        &self,
        player_id: Uuid,
        job_class: JobClass,
    ) -> Result<PlayerProfile, PlayerError> {
        let profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                job_class = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            "#,
            player_id,
            job_class as JobClass
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::PlayerNotFound { id: player_id })?;

        Ok(profile)
    }

    /// Update a player's hunter rank
    pub async fn update_player_hunter_rank(
        &self,
        player_id: Uuid,
        hunter_rank: HunterRank,
    ) -> Result<PlayerProfile, PlayerError> {
        let profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                hunter_rank = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            "#,
            player_id,
            hunter_rank as HunterRank
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(PlayerError::PlayerNotFound { id: player_id })?;

        Ok(profile)
    }

    /// Add experience points to a player
    pub async fn add_experience(
        &self,
        player_id: Uuid,
        exp_amount: i64,
    ) -> Result<(PlayerProfile, bool), PlayerError> {
        if exp_amount <= 0 {
            return Err(PlayerError::System {
                reason: "Experience amount must be positive".to_string(),
            });
        }

        // Get current profile
        let current_profile = self.get_player_profile(player_id).await?;

        // Calculate new experience and check for level up
        let mut new_exp = current_profile.exp + exp_amount;
        let mut new_level = current_profile.level;
        let mut new_exp_next = current_profile.exp_next;
        let mut new_stat_points = current_profile.stat_points;
        let mut leveled_up = false;

        // Check for level up
        while new_exp >= new_exp_next {
            new_exp -= new_exp_next;
            new_level += 1;
            new_stat_points += 5; // 5 stat points per level
            new_exp_next = self.calculate_exp_for_level(new_level + 1);
            leveled_up = true;
        }

        // Update profile
        let updated_profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                level = $2,
                exp = $3,
                exp_next = $4,
                stat_points = $5,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            "#,
            player_id,
            new_level,
            new_exp,
            new_exp_next,
            new_stat_points
        )
        .fetch_one(&self.db_pool)
        .await?;

        // If leveled up, update stats
        if leveled_up {
            self.update_stats_on_level_up(player_id, new_level).await?;
        }

        Ok((updated_profile, leveled_up))
    }

    /// Calculate experience required for a level
    fn calculate_exp_for_level(&self, level: i32) -> i64 {
        // Simple formula: 1000 * level^2
        1000 * (level as i64).pow(2)
    }

    /// Update stats when a player levels up
    async fn update_stats_on_level_up(
        &self,
        player_id: Uuid,
        level: i32,
    ) -> Result<PlayerStats, PlayerError> {
        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Calculate new max HP and MP based on level and constitution/intelligence
        let new_max_hp = 100.0 + (level as f32 - 1.0) * 10.0 + (current_stats.constitution - 10.0) * 5.0;
        let new_max_mana = 50.0 + (level as f32 - 1.0) * 5.0 + (current_stats.intelligence - 10.0) * 3.0;
        
        // Calculate new regen rates based on constitution/wisdom
        let new_hp_regen = 1.0 + (current_stats.constitution - 10.0) * 0.1;
        let new_mana_regen = 0.5 + (current_stats.wisdom - 10.0) * 0.1;

        // Update stats
        let updated_stats = sqlx::query_as!(
            PlayerStats,
            r#"
            UPDATE game.player_stats
            SET 
                max_hp = $2,
                current_hp = $2, -- Fully heal on level up
                max_mana = $3,
                current_mana = $3, -- Fully restore mana on level up
                hp_regen = $4,
                mana_regen = $5,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            "#,
            player_id,
            new_max_hp,
            new_max_mana,
            new_hp_regen,
            new_mana_regen
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_stats)
    }

    /// Allocate stat points to a specific stat
    pub async fn allocate_stat_points(
        &self,
        player_id: Uuid,
        stat_type: StatType,
        points: i32,
    ) -> Result<(PlayerProfile, PlayerStats), PlayerError> {
        if points <= 0 {
            return Err(PlayerError::InvalidStatValue {
                reason: "Points to allocate must be positive".to_string(),
            });
        }

        // Get current profile to check available points
        let profile = self.get_player_profile(player_id).await?;

        if profile.stat_points < points {
            return Err(PlayerError::InsufficientStatPoints {
                required: points,
                available: profile.stat_points,
            });
        }

        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Update profile to deduct stat points
        let updated_profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                stat_points = stat_points - $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
                level, exp, exp_next, stat_points, achievement_points,
                total_gates_cleared, total_playtime, created_at, updated_at
            "#,
            player_id,
            points
        )
        .fetch_one(&mut tx)
        .await?;

        // Update the specific stat
        let updated_stats = match stat_type {
            StatType::Strength => {
                let new_strength = current_stats.strength + points as f32;
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        strength = $2,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_strength
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Dexterity => {
                let new_dexterity = current_stats.dexterity + points as f32;
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        dexterity = $2,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_dexterity
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Constitution => {
                let new_constitution = current_stats.constitution + points as f32;
                // Also update max HP and regen
                let new_max_hp = 100.0 + (profile.level as f32 - 1.0) * 10.0 + (new_constitution - 10.0) * 5.0;
                let new_hp_regen = 1.0 + (new_constitution - 10.0) * 0.1;
                
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        constitution = $2,
                        max_hp = $3,
                        hp_regen = $4,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_constitution,
                    new_max_hp,
                    new_hp_regen
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Intelligence => {
                let new_intelligence = current_stats.intelligence + points as f32;
                // Also update max mana
                let new_max_mana = 50.0 + (profile.level as f32 - 1.0) * 5.0 + (new_intelligence - 10.0) * 3.0;
                
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        intelligence = $2,
                        max_mana = $3,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_intelligence,
                    new_max_mana
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Wisdom => {
                let new_wisdom = current_stats.wisdom + points as f32;
                // Also update mana regen
                let new_mana_regen = 0.5 + (new_wisdom - 10.0) * 0.1;
                
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        wisdom = $2,
                        mana_regen = $3,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_wisdom,
                    new_mana_regen
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Charisma => {
                let new_charisma = current_stats.charisma + points as f32;
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        charisma = $2,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_charisma
                )
                .fetch_one(&mut tx)
                .await?
            }
            StatType::Luck => {
                let new_luck = current_stats.luck + points as f32;
                sqlx::query_as!(
                    PlayerStats,
                    r#"
                    UPDATE game.player_stats
                    SET 
                        luck = $2,
                        updated_at = NOW()
                    WHERE player_id = $1
                    RETURNING 
                        player_id, strength, dexterity, constitution,
                        intelligence, wisdom, charisma, luck,
                        current_hp, max_hp, current_mana, max_mana,
                        hp_regen, mana_regen, created_at, updated_at
                    "#,
                    player_id,
                    new_luck
                )
                .fetch_one(&mut tx)
                .await?
            }
        };

        // Commit transaction
        tx.commit().await?;

        Ok((updated_profile, updated_stats))
    }

    /// Update player's health
    pub async fn update_health(
        &self,
        player_id: Uuid,
        new_hp: f32,
    ) -> Result<PlayerStats, PlayerError> {
        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Ensure HP is within valid range
        let clamped_hp = new_hp.max(0.0).min(current_stats.max_hp);

        // Update HP
        let updated_stats = sqlx::query_as!(
            PlayerStats,
            r#"
            UPDATE game.player_stats
            SET 
                current_hp = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            "#,
            player_id,
            clamped_hp
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_stats)
    }

    /// Update player's mana
    pub async fn update_mana(
        &self,
        player_id: Uuid,
        new_mana: f32,
    ) -> Result<PlayerStats, PlayerError> {
        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Ensure mana is within valid range
        let clamped_mana = new_mana.max(0.0).min(current_stats.max_mana);

        // Update mana
        let updated_stats = sqlx::query_as!(
            PlayerStats,
            r#"
            UPDATE game.player_stats
            SET 
                current_mana = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            "#,
            player_id,
            clamped_mana
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_stats)
    }

    /// Apply health regeneration
    pub async fn apply_health_regen(&self, player_id: Uuid) -> Result<PlayerStats, PlayerError> {
        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Skip if already at max HP
        if current_stats.current_hp >= current_stats.max_hp {
            return Ok(current_stats);
        }

        // Calculate new HP
        let new_hp = (current_stats.current_hp + current_stats.hp_regen).min(current_stats.max_hp);

        // Update HP
        let updated_stats = sqlx::query_as!(
            PlayerStats,
            r#"
            UPDATE game.player_stats
            SET 
                current_hp = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            "#,
            player_id,
            new_hp
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_stats)
    }

    /// Apply mana regeneration
    pub async fn apply_mana_regen(&self, player_id: Uuid) -> Result<PlayerStats, PlayerError> {
        // Get current stats
        let current_stats = self.get_player_stats(player_id).await?;

        // Skip if already at max mana
        if current_stats.current_mana >= current_stats.max_mana {
            return Ok(current_stats);
        }

        // Calculate new mana
        let new_mana = (current_stats.current_mana + current_stats.mana_regen).min(current_stats.max_mana);

        // Update mana
        let updated_stats = sqlx::query_as!(
            PlayerStats,
            r#"
            UPDATE game.player_stats
            SET 
                current_mana = $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, strength, dexterity, constitution,
                intelligence, wisdom, charisma, luck,
                current_hp, max_hp, current_mana, max_mana,
                hp_regen, mana_regen, created_at, updated_at
            "#,
            player_id,
            new_mana
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_stats)
    }

    /// Connect a blockchain wallet to a player account
    pub async fn connect_blockchain_wallet(
        &self,
        player_id: Uuid,
        wallet_address: &str,
    ) -> Result<Player, PlayerError> {
        // Check if blockchain service is available
        let blockchain_service = match &self.blockchain_service {
            Some(service) => service,
            None => {
                return Err(PlayerError::System {
                    reason: "Blockchain service not configured".to_string(),
                });
            }
        };

        // Connect wallet using blockchain service
        blockchain_service.connect_wallet(player_id, wallet_address).await.map_err(|e| {
            PlayerError::System {
                reason: format!("Failed to connect wallet: {}", e),
            }
        })?;

        // Update player record with wallet address
        let updated_player = sqlx::query_as!(
            Player,
            r#"
            UPDATE auth.players
            SET 
                web3_wallet_address = $2
            WHERE id = $1
            RETURNING 
                id, username, email, is_online, is_admin, 
                session_id, web3_wallet_address, created_at, last_login
            "#,
            player_id,
            wallet_address
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_player)
    }

    /// Verify a blockchain wallet connection
    pub async fn verify_blockchain_wallet(
        &self,
        player_id: Uuid,
        signature: &str,
    ) -> Result<Player, PlayerError> {
        // Check if blockchain service is available
        let blockchain_service = match &self.blockchain_service {
            Some(service) => service,
            None => {
                return Err(PlayerError::System {
                    reason: "Blockchain service not configured".to_string(),
                });
            }
        };

        // Verify wallet using blockchain service
        blockchain_service.verify_wallet(player_id, signature).await.map_err(|e| {
            PlayerError::System {
                reason: format!("Failed to verify wallet: {}", e),
            }
        })?;

        // Get updated player record
        let player = self.get_player(player_id).await?;

        Ok(player)
    }

    /// Get a player's inventory
    pub async fn get_player_inventory(&self, player_id: Uuid) -> Result<Vec<InventoryItem>, PlayerError> {
        // Query inventory items
        let items = sqlx::query_as!(
            InventoryItem,
            r#"
            SELECT 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            FROM game.inventory_items
            WHERE player_id = $1
            ORDER BY slot_index ASC
            "#,
            player_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(items)
    }

    /// Add an item to a player's inventory
    pub async fn add_inventory_item(
        &self,
        player_id: Uuid,
        item_id: Uuid,
        item_type: ItemType,
        quantity: i32,
    ) -> Result<InventoryItem, PlayerError> {
        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Check if inventory has space
        let inventory = sqlx::query!(
            r#"
            SELECT max_slots, used_slots FROM game.inventories
            WHERE player_id = $1
            FOR UPDATE
            "#,
            player_id
        )
        .fetch_one(&mut tx)
        .await?;

        if inventory.used_slots >= inventory.max_slots {
            return Err(PlayerError::System {
                reason: "Inventory is full".to_string(),
            });
        }

        // Find next available slot
        let next_slot = sqlx::query!(
            r#"
            SELECT COALESCE(MAX(slot_index) + 1, 0) as next_slot
            FROM game.inventory_items
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_one(&mut tx)
        .await?
        .next_slot;

        // Add item to inventory
        let item = sqlx::query_as!(
            InventoryItem,
            r#"
            INSERT INTO game.inventory_items (
                id, player_id, item_id, item_type, 
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            )
            VALUES (
                uuid_generate_v4(), $1, $2, $3, 
                $4, $5, false, 
                100, NOW(), NOW()
            )
            RETURNING 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            "#,
            player_id,
            item_id,
            item_type as ItemType,
            quantity,
            next_slot
        )
        .fetch_one(&mut tx)
        .await?;

        // Update inventory used slots
        sqlx::query!(
            r#"
            UPDATE game.inventories
            SET 
                used_slots = used_slots + 1,
                last_updated = NOW()
            WHERE player_id = $1
            "#,
            player_id
        )
        .execute(&mut tx)
        .await?;

        // Commit transaction
        tx.commit().await?;

        Ok(item)
    }

    /// Remove an item from a player's inventory
    pub async fn remove_inventory_item(
        &self,
        player_id: Uuid,
        inventory_item_id: Uuid,
    ) -> Result<(), PlayerError> {
        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Check if item exists and belongs to player
        let item = sqlx::query!(
            r#"
            SELECT id FROM game.inventory_items
            WHERE id = $1 AND player_id = $2
            FOR UPDATE
            "#,
            inventory_item_id,
            player_id
        )
        .fetch_optional(&mut tx)
        .await?;

        if item.is_none() {
            return Err(PlayerError::System {
                reason: "Item not found in player's inventory".to_string(),
            });
        }

        // Remove item from inventory
        sqlx::query!(
            r#"
            DELETE FROM game.inventory_items
            WHERE id = $1
            "#,
            inventory_item_id
        )
        .execute(&mut tx)
        .await?;

        // Update inventory used slots
        sqlx::query!(
            r#"
            UPDATE game.inventories
            SET 
                used_slots = used_slots - 1,
                last_updated = NOW()
            WHERE player_id = $1
            "#,
            player_id
        )
        .execute(&mut tx)
        .await?;

        // Commit transaction
        tx.commit().await?;

        Ok(())
    }

    /// Equip an item
    pub async fn equip_item(
        &self,
        player_id: Uuid,
        inventory_item_id: Uuid,
    ) -> Result<InventoryItem, PlayerError> {
        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Check if item exists and belongs to player
        let item = sqlx::query!(
            r#"
            SELECT id, item_type FROM game.inventory_items
            WHERE id = $1 AND player_id = $2
            FOR UPDATE
            "#,
            inventory_item_id,
            player_id
        )
        .fetch_optional(&mut tx)
        .await?;

        let item = match item {
            Some(i) => i,
            None => {
                return Err(PlayerError::System {
                    reason: "Item not found in player's inventory".to_string(),
                });
            }
        };

        // Unequip any currently equipped items of the same type
        sqlx::query!(
            r#"
            UPDATE game.inventory_items
            SET 
                is_equipped = false,
                updated_at = NOW()
            WHERE player_id = $1 AND item_type = $2 AND is_equipped = true
            "#,
            player_id,
            item.item_type
        )
        .execute(&mut tx)
        .await?;

        // Equip the new item
        let equipped_item = sqlx::query_as!(
            InventoryItem,
            r#"
            UPDATE game.inventory_items
            SET 
                is_equipped = true,
                updated_at = NOW()
            WHERE id = $1
            RETURNING 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            "#,
            inventory_item_id
        )
        .fetch_one(&mut tx)
        .await?;

        // Commit transaction
        tx.commit().await?;

        Ok(equipped_item)
    }

    /// Unequip an item
    pub async fn unequip_item(
        &self,
        player_id: Uuid,
        inventory_item_id: Uuid,
    ) -> Result<InventoryItem, PlayerError> {
        // Check if item exists and belongs to player
        let item = sqlx::query!(
            r#"
            SELECT id FROM game.inventory_items
            WHERE id = $1 AND player_id = $2 AND is_equipped = true
            "#,
            inventory_item_id,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        if item.is_none() {
            return Err(PlayerError::System {
                reason: "Item not found or not equipped".to_string(),
            });
        }

        // Unequip the item
        let unequipped_item = sqlx::query_as!(
            InventoryItem,
            r#"
            UPDATE game.inventory_items
            SET 
                is_equipped = false,
                updated_at = NOW()
            WHERE id = $1
            RETURNING 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            "#,
            inventory_item_id
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(unequipped_item)
    }

    /// Update item durability
    pub async fn update_item_durability(
        &self,
        player_id: Uuid,
        inventory_item_id: Uuid,
        durability_change: f32,
    ) -> Result<InventoryItem, PlayerError> {
        // Check if item exists and belongs to player
        let item = sqlx::query!(
            r#"
            SELECT id, durability FROM game.inventory_items
            WHERE id = $1 AND player_id = $2
            "#,
            inventory_item_id,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        let item = match item {
            Some(i) => i,
            None => {
                return Err(PlayerError::System {
                    reason: "Item not found in player's inventory".to_string(),
                });
            }
        };

        // Calculate new durability
        let new_durability = (item.durability + durability_change).max(0.0).min(100.0);

        // Update durability
        let updated_item = sqlx::query_as!(
            InventoryItem,
            r#"
            UPDATE game.inventory_items
            SET 
                durability = $2,
                updated_at = NOW()
            WHERE id = $1
            RETURNING 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            "#,
            inventory_item_id,
            new_durability
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(updated_item)
    }

    /// Get all equipped items for a player
    pub async fn get_equipped_items(&self, player_id: Uuid) -> Result<Vec<InventoryItem>, PlayerError> {
        // Query equipped items
        let items = sqlx::query_as!(
            InventoryItem,
            r#"
            SELECT 
                id, player_id, item_id, item_type as "item_type: ItemType",
                quantity, slot_index, is_equipped, 
                durability, created_at, updated_at
            FROM game.inventory_items
            WHERE player_id = $1 AND is_equipped = true
            "#,
            player_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(items)
    }

    /// Increase inventory capacity
    pub async fn increase_inventory_capacity(
        &self,
        player_id: Uuid,
        additional_slots: i32,
    ) -> Result<i32, PlayerError> {
        if additional_slots <= 0 {
            return Err(PlayerError::System {
                reason: "Additional slots must be positive".to_string(),
            });
        }

        // Update inventory capacity
        let new_max_slots = sqlx::query!(
            r#"
            UPDATE game.inventories
            SET 
                max_slots = max_slots + $2,
                last_updated = NOW()
            WHERE player_id = $1
            RETURNING max_slots
            "#,
            player_id,
            additional_slots
        )
        .fetch_one(&self.db_pool)
        .await?
        .max_slots;

        Ok(new_max_slots)
    }

    /// Update player's total playtime
    pub async fn update_playtime(
        &self,
        player_id: Uuid,
        additional_seconds: i64,
    ) -> Result<PlayerProfile, PlayerError> {
        if additional_seconds <= 0 {
            return Err(PlayerError::System {
                reason: "Additional playtime must be positive".to_string(),
            });
        }

        // Update playtime
        let profile = sqlx::query_as!(
            PlayerProfile,
            r#"
            UPDATE game.player_profiles
            SET 
                total_playtime = total_playtime + $2,
                updated_at = NOW()
            WHERE player_id = $1
            RETURNING 
                player_id, current_map, position_x, position_y,
                job_class as "job_class: JobClass", hunter_rank as "hunter_rank: HunterRank",
