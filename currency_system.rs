//! Currency System Implementation for Terminusa Online
//!
//! This module implements the three-currency system (Solana, Exons, Crystals)
//! and provides functionality for currency management, transfers, and blockchain integration.

use std::fmt;
use std::error::Error;
use std::str::FromStr;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use rust_decimal::Decimal;
use sqlx::{PgPool, Row, postgres::PgRow};
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    signature::{Keypair, Signature},
    pubkey::Pubkey,
    transaction::Transaction,
    system_instruction,
};

/// Represents the different types of currencies in the game
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CurrencyType {
    /// Solana blockchain-based cryptocurrency
    Solana,
    /// Exons governance token (blockchain-based)
    Exons,
    /// In-game currency (off-chain)
    Crystals,
}

impl fmt::Display for CurrencyType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CurrencyType::Solana => write!(f, "Solana"),
            CurrencyType::Exons => write!(f, "Exons"),
            CurrencyType::Crystals => write!(f, "Crystals"),
        }
    }
}

impl FromStr for CurrencyType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "solana" => Ok(CurrencyType::Solana),
            "exons" => Ok(CurrencyType::Exons),
            "crystals" => Ok(CurrencyType::Crystals),
            _ => Err(format!("Unknown currency type: {}", s)),
        }
    }
}

/// Represents a currency in the game
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Currency {
    /// Unique identifier for the currency
    pub id: i32,
    /// Name of the currency
    pub name: String,
    /// Symbol of the currency
    pub symbol: String,
    /// Whether the currency is blockchain-based
    pub is_blockchain: bool,
    /// Contract address for blockchain-based currencies
    pub contract_address: Option<String>,
    /// Maximum supply of the currency
    pub max_supply: Option<Decimal>,
    /// Current supply of the currency
    pub current_supply: Decimal,
    /// Whether the currency can be earned in gates
    pub is_gate_reward: bool,
    /// When the currency was created
    pub created_at: DateTime<Utc>,
    /// When the currency was last updated
    pub updated_at: DateTime<Utc>,
}

/// Represents a player's wallet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wallet {
    /// Player ID associated with this wallet
    pub player_id: Uuid,
    /// Solana balance
    pub solana_balance: Decimal,
    /// Exons balance
    pub exons_balance: Decimal,
    /// Crystals balance
    pub crystals_balance: Decimal,
    /// When the wallet was last updated
    pub last_updated: DateTime<Utc>,
}

/// Represents a transaction type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TransactionType {
    /// Player-to-player transfer
    Transfer,
    /// Purchase of an item
    Purchase,
    /// Reward from a game activity
    Reward,
    /// Reward from completing a gate
    GateReward,
    /// Reward from completing a quest
    QuestReward,
    /// Tax payment
    Tax,
    /// Currency minting (admin only)
    Mint,
    /// Currency burning (admin only)
    Burn,
}

impl fmt::Display for TransactionType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TransactionType::Transfer => write!(f, "transfer"),
            TransactionType::Purchase => write!(f, "purchase"),
            TransactionType::Reward => write!(f, "reward"),
            TransactionType::GateReward => write!(f, "gate_reward"),
            TransactionType::QuestReward => write!(f, "quest_reward"),
            TransactionType::Tax => write!(f, "tax"),
            TransactionType::Mint => write!(f, "mint"),
            TransactionType::Burn => write!(f, "burn"),
        }
    }
}

impl FromStr for TransactionType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "transfer" => Ok(TransactionType::Transfer),
            "purchase" => Ok(TransactionType::Purchase),
            "reward" => Ok(TransactionType::Reward),
            "gate_reward" => Ok(TransactionType::GateReward),
            "quest_reward" => Ok(TransactionType::QuestReward),
            "tax" => Ok(TransactionType::Tax),
            "mint" => Ok(TransactionType::Mint),
            "burn" => Ok(TransactionType::Burn),
            _ => Err(format!("Unknown transaction type: {}", s)),
        }
    }
}

/// Represents a transaction status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TransactionStatus {
    /// Transaction is pending
    Pending,
    /// Transaction is completed
    Completed,
    /// Transaction failed
    Failed,
    /// Transaction was cancelled
    Cancelled,
}

impl fmt::Display for TransactionStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TransactionStatus::Pending => write!(f, "pending"),
            TransactionStatus::Completed => write!(f, "completed"),
            TransactionStatus::Failed => write!(f, "failed"),
            TransactionStatus::Cancelled => write!(f, "cancelled"),
        }
    }
}

impl FromStr for TransactionStatus {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "pending" => Ok(TransactionStatus::Pending),
            "completed" => Ok(TransactionStatus::Completed),
            "failed" => Ok(TransactionStatus::Failed),
            "cancelled" => Ok(TransactionStatus::Cancelled),
            _ => Err(format!("Unknown transaction status: {}", s)),
        }
    }
}

/// Represents a currency transaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    /// Unique identifier for the transaction
    pub id: Uuid,
    /// Sender player ID (None if system)
    pub from_player_id: Option<Uuid>,
    /// Recipient player ID (None if system)
    pub to_player_id: Option<Uuid>,
    /// Currency ID
    pub currency_id: i32,
    /// Transaction amount
    pub amount: Decimal,
    /// Tax amount
    pub tax_amount: Decimal,
    /// Transaction type
    pub transaction_type: TransactionType,
    /// Reference ID (e.g., item ID, gate ID)
    pub reference_id: Option<Uuid>,
    /// Transaction status
    pub status: TransactionStatus,
    /// Blockchain transaction hash
    pub blockchain_tx_hash: Option<String>,
    /// When the transaction was created
    pub created_at: DateTime<Utc>,
    /// Additional notes
    pub notes: Option<String>,
}

/// Represents tax settings for a currency
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaxSettings {
    /// Unique identifier for the tax settings
    pub id: i32,
    /// Currency ID
    pub currency_id: i32,
    /// Base tax percentage
    pub tax_percentage: Decimal,
    /// Additional guild tax percentage
    pub guild_tax_percentage: Decimal,
    /// Admin account for tax collection
    pub admin_account: String,
    /// When the tax settings were last updated
    pub updated_at: DateTime<Utc>,
}

/// Error types for currency operations
#[derive(Debug)]
pub enum CurrencyError {
    /// Database error
    Database(sqlx::Error),
    /// Insufficient funds
    InsufficientFunds { currency: CurrencyType, required: Decimal, available: Decimal },
    /// Invalid amount
    InvalidAmount { reason: String },
    /// Blockchain error
    Blockchain { reason: String },
    /// Currency not found
    CurrencyNotFound { id: i32 },
    /// Wallet not found
    WalletNotFound { player_id: Uuid },
    /// Transaction not found
    TransactionNotFound { id: Uuid },
    /// Unauthorized operation
    Unauthorized { reason: String },
    /// System error
    System { reason: String },
}

impl fmt::Display for CurrencyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CurrencyError::Database(e) => write!(f, "Database error: {}", e),
            CurrencyError::InsufficientFunds { currency, required, available } => {
                write!(f, "Insufficient {} funds: required {}, available {}", currency, required, available)
            }
            CurrencyError::InvalidAmount { reason } => write!(f, "Invalid amount: {}", reason),
            CurrencyError::Blockchain { reason } => write!(f, "Blockchain error: {}", reason),
            CurrencyError::CurrencyNotFound { id } => write!(f, "Currency not found: ID {}", id),
            CurrencyError::WalletNotFound { player_id } => write!(f, "Wallet not found for player: {}", player_id),
            CurrencyError::TransactionNotFound { id } => write!(f, "Transaction not found: {}", id),
            CurrencyError::Unauthorized { reason } => write!(f, "Unauthorized: {}", reason),
            CurrencyError::System { reason } => write!(f, "System error: {}", reason),
        }
    }
}

impl Error for CurrencyError {}

impl From<sqlx::Error> for CurrencyError {
    fn from(error: sqlx::Error) -> Self {
        CurrencyError::Database(error)
    }
}

/// Currency service for managing currencies and transactions
pub struct CurrencyService {
    /// Database connection pool
    db_pool: PgPool,
    /// Solana RPC client for blockchain operations
    solana_client: Option<RpcClient>,
    /// Admin wallet for tax collection
    admin_wallet: Option<String>,
}

impl CurrencyService {
    /// Create a new currency service
    pub fn new(db_pool: PgPool) -> Self {
        CurrencyService {
            db_pool,
            solana_client: None,
            admin_wallet: None,
        }
    }

    /// Configure Solana blockchain integration
    pub fn with_solana(mut self, rpc_url: &str, admin_wallet: &str) -> Result<Self, CurrencyError> {
        match RpcClient::new(rpc_url) {
            Ok(client) => {
                self.solana_client = Some(client);
                self.admin_wallet = Some(admin_wallet.to_string());
                Ok(self)
            }
            Err(e) => Err(CurrencyError::Blockchain { reason: e.to_string() }),
        }
    }

    /// Get all currencies
    pub async fn get_all_currencies(&self) -> Result<Vec<Currency>, CurrencyError> {
        let currencies = sqlx::query_as!(
            Currency,
            r#"
            SELECT 
                id, name, symbol, is_blockchain, contract_address, 
                max_supply, current_supply, is_gate_reward, 
                created_at, updated_at
            FROM game.currencies
            ORDER BY id
            "#
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(currencies)
    }

    /// Get a currency by ID
    pub async fn get_currency_by_id(&self, id: i32) -> Result<Currency, CurrencyError> {
        let currency = sqlx::query_as!(
            Currency,
            r#"
            SELECT 
                id, name, symbol, is_blockchain, contract_address, 
                max_supply, current_supply, is_gate_reward, 
                created_at, updated_at
            FROM game.currencies
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(CurrencyError::CurrencyNotFound { id })?;

        Ok(currency)
    }

    /// Get a currency by type
    pub async fn get_currency_by_type(&self, currency_type: CurrencyType) -> Result<Currency, CurrencyError> {
        let name = currency_type.to_string();
        
        let currency = sqlx::query_as!(
            Currency,
            r#"
            SELECT 
                id, name, symbol, is_blockchain, contract_address, 
                max_supply, current_supply, is_gate_reward, 
                created_at, updated_at
            FROM game.currencies
            WHERE name = $1
            "#,
            name
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(CurrencyError::CurrencyNotFound { id: 0 })?;

        Ok(currency)
    }

    /// Get a player's wallet
    pub async fn get_wallet(&self, player_id: Uuid) -> Result<Wallet, CurrencyError> {
        let wallet = sqlx::query_as!(
            Wallet,
            r#"
            SELECT 
                player_id, solana_balance, exons_balance, 
                crystals_balance, last_updated
            FROM game.wallets
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(CurrencyError::WalletNotFound { player_id })?;

        Ok(wallet)
    }

    /// Create a wallet for a player
    pub async fn create_wallet(&self, player_id: Uuid) -> Result<Wallet, CurrencyError> {
        // Check if wallet already exists
        let existing_wallet = sqlx::query!(
            r#"
            SELECT player_id FROM game.wallets
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        if existing_wallet.is_some() {
            return self.get_wallet(player_id);
        }

        // Create new wallet
        let wallet = sqlx::query_as!(
            Wallet,
            r#"
            INSERT INTO game.wallets (
                player_id, solana_balance, exons_balance, 
                crystals_balance, last_updated
            )
            VALUES ($1, 0, 0, 0, NOW())
            RETURNING player_id, solana_balance, exons_balance, 
                     crystals_balance, last_updated
            "#,
            player_id
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(wallet)
    }

    /// Get a player's balance for a specific currency
    pub async fn get_balance(&self, player_id: Uuid, currency_type: CurrencyType) -> Result<Decimal, CurrencyError> {
        let wallet = self.get_wallet(player_id).await?;
        
        let balance = match currency_type {
            CurrencyType::Solana => wallet.solana_balance,
            CurrencyType::Exons => wallet.exons_balance,
            CurrencyType::Crystals => wallet.crystals_balance,
        };
        
        Ok(balance)
    }

    /// Update a player's balance for a specific currency
    async fn update_balance(
        &self, 
        player_id: Uuid, 
        currency_type: CurrencyType, 
        amount: Decimal
    ) -> Result<Decimal, CurrencyError> {
        let column_name = match currency_type {
            CurrencyType::Solana => "solana_balance",
            CurrencyType::Exons => "exons_balance",
            CurrencyType::Crystals => "crystals_balance",
        };
        
        let query = format!(
            r#"
            UPDATE game.wallets
            SET {} = {}, last_updated = NOW()
            WHERE player_id = $1
            RETURNING {}
            "#,
            column_name, column_name, column_name
        );
        
        let row = sqlx::query(&query)
            .bind(player_id)
            .bind(amount)
            .fetch_one(&self.db_pool)
            .await?;
            
        let new_balance: Decimal = row.get(0);
        
        Ok(new_balance)
    }

    /// Add currency to a player's wallet
    pub async fn add_currency(
        &self, 
        player_id: Uuid, 
        currency_type: CurrencyType, 
        amount: Decimal
    ) -> Result<Decimal, CurrencyError> {
        if amount <= Decimal::ZERO {
            return Err(CurrencyError::InvalidAmount { 
                reason: "Amount must be positive".to_string() 
            });
        }
        
        let wallet = self.get_wallet(player_id).await?;
        
        let new_balance = match currency_type {
            CurrencyType::Solana => wallet.solana_balance + amount,
            CurrencyType::Exons => wallet.exons_balance + amount,
            CurrencyType::Crystals => wallet.crystals_balance + amount,
        };
        
        self.update_balance(player_id, currency_type, new_balance).await
    }

    /// Remove currency from a player's wallet
    pub async fn remove_currency(
        &self, 
        player_id: Uuid, 
        currency_type: CurrencyType, 
        amount: Decimal
    ) -> Result<Decimal, CurrencyError> {
        if amount <= Decimal::ZERO {
            return Err(CurrencyError::InvalidAmount { 
                reason: "Amount must be positive".to_string() 
            });
        }
        
        let wallet = self.get_wallet(player_id).await?;
        
        let current_balance = match currency_type {
            CurrencyType::Solana => wallet.solana_balance,
            CurrencyType::Exons => wallet.exons_balance,
            CurrencyType::Crystals => wallet.crystals_balance,
        };
        
        if current_balance < amount {
            return Err(CurrencyError::InsufficientFunds { 
                currency: currency_type,
                required: amount,
                available: current_balance,
            });
        }
        
        let new_balance = current_balance - amount;
        
        self.update_balance(player_id, currency_type, new_balance).await
    }

    /// Get tax settings for a currency
    pub async fn get_tax_settings(&self, currency_id: i32) -> Result<TaxSettings, CurrencyError> {
        let tax_settings = sqlx::query_as!(
            TaxSettings,
            r#"
            SELECT 
                id, currency_id, tax_percentage, guild_tax_percentage, 
                admin_account, updated_at
            FROM game.tax_settings
            WHERE currency_id = $1
            "#,
            currency_id
        )
        .fetch_optional(&self.db_pool)
        .await?;
        
        match tax_settings {
            Some(settings) => Ok(settings),
            None => {
                // Return default tax settings if none found
                Ok(TaxSettings {
                    id: 0,
                    currency_id,
                    tax_percentage: Decimal::new(0, 0),
                    guild_tax_percentage: Decimal::new(0, 0),
                    admin_account: self.admin_wallet.clone().unwrap_or_else(|| "adminbb".to_string()),
                    updated_at: Utc::now(),
                })
            }
        }
    }

    /// Calculate tax for a transaction
    pub async fn calculate_tax(
        &self, 
        amount: Decimal, 
        currency_id: i32,
        is_guild_transaction: bool
    ) -> Result<Decimal, CurrencyError> {
        let tax_settings = self.get_tax_settings(currency_id).await?;
        
        let mut tax_rate = tax_settings.tax_percentage / Decimal::new(100, 0);
        
        if is_guild_transaction {
            tax_rate += tax_settings.guild_tax_percentage / Decimal::new(100, 0);
        }
        
        let tax_amount = amount * tax_rate;
        
        Ok(tax_amount)
    }

    /// Create a new transaction
    pub async fn create_transaction(
        &self,
        from_player_id: Option<Uuid>,
        to_player_id: Option<Uuid>,
        currency_id: i32,
        amount: Decimal,
        tax_amount: Decimal,
        transaction_type: TransactionType,
        reference_id: Option<Uuid>,
        notes: Option<String>,
    ) -> Result<Transaction, CurrencyError> {
        if amount <= Decimal::ZERO {
            return Err(CurrencyError::InvalidAmount { 
                reason: "Amount must be positive".to_string() 
            });
        }
        
        let transaction = sqlx::query_as!(
            Transaction,
            r#"
            INSERT INTO game.transactions (
                id, from_player_id, to_player_id, currency_id, 
                amount, tax_amount, transaction_type, reference_id, 
                status, blockchain_tx_hash, created_at, notes
            )
            VALUES (
                uuid_generate_v4(), $1, $2, $3, 
                $4, $5, $6, $7, 
                'pending', NULL, NOW(), $8
            )
            RETURNING 
                id, from_player_id, to_player_id, currency_id, 
                amount, tax_amount, 
                transaction_type as "transaction_type: TransactionType", 
                reference_id, 
                status as "status: TransactionStatus", 
                blockchain_tx_hash, created_at, notes
            "#,
            from_player_id,
            to_player_id,
            currency_id,
            amount,
            tax_amount,
            transaction_type.to_string(),
            reference_id,
            notes
        )
        .fetch_one(&self.db_pool)
        .await?;
        
        Ok(transaction)
    }

    /// Get a transaction by ID
    pub async fn get_transaction(&self, id: Uuid) -> Result<Transaction, CurrencyError> {
        let transaction = sqlx::query_as!(
            Transaction,
            r#"
            SELECT 
                id, from_player_id, to_player_id, currency_id, 
                amount, tax_amount, 
                transaction_type as "transaction_type: TransactionType", 
                reference_id, 
                status as "status: TransactionStatus", 
                blockchain_tx_hash, created_at, notes
            FROM game.transactions
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(CurrencyError::TransactionNotFound { id })?;
        
        Ok(transaction)
    }

    /// Update a transaction's status
    pub async fn update_transaction_status(
        &self,
        id: Uuid,
        status: TransactionStatus,
        blockchain_tx_hash: Option<String>,
    ) -> Result<Transaction, CurrencyError> {
        let transaction = sqlx::query_as!(
            Transaction,
            r#"
            UPDATE game.transactions
            SET 
                status = $2,
                blockchain_tx_hash = $3
            WHERE id = $1
            RETURNING 
                id, from_player_id, to_player_id, currency_id, 
                amount, tax_amount, 
                transaction_type as "transaction_type: TransactionType", 
                reference_id, 
                status as "status: TransactionStatus", 
                blockchain_tx_hash, created_at, notes
            "#,
            id,
            status.to_string(),
            blockchain_tx_hash
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(CurrencyError::TransactionNotFound { id })?;
        
        Ok(transaction)
    }

    /// Transfer currency between players
    pub async fn transfer_currency(
        &self,
        from_player_id: Uuid,
        to_player_id: Uuid,
        currency_type: CurrencyType,
        amount: Decimal,
        is_guild_transaction: bool,
        notes: Option<String>,
    ) -> Result<Transaction, CurrencyError> {
        if amount <= Decimal::ZERO {
            return Err(CurrencyError::InvalidAmount { 
                reason: "Amount must be positive".to_string() 
            });
        }
        
        // Get currency
        let currency = self.get_currency_by_type(currency_type).await?;
        
        // Calculate tax
        let tax_amount = self.calculate_tax(amount, currency.id, is_guild_transaction).await?;
        
        // Begin transaction
        let mut tx = self.db_pool.begin().await?;
        
        // Check if sender has enough funds (amount + tax)
        let sender_balance = self.get_balance(from_player_id, currency_type).await?;
        let total_amount = amount + tax_amount;
        
        if sender_balance < total_amount {
            return Err(CurrencyError::InsufficientFunds { 
                currency: currency_type,
                required: total_amount,
                available: sender_balance,
            });
        }
        
        // Create transaction record
        let transaction = self.create_transaction(
            Some(from_player_id),
            Some(to_player_id),
            currency.id,
            amount,
            tax_amount,
            TransactionType::Transfer,
            None,
            notes,
        ).await?;
        
        // Handle blockchain transactions if applicable
        if currency.is_blockchain {
            match currency_type {
                CurrencyType::Solana => {
                    // Implement Solana transfer logic
                    if let Some(client) = &self.solana_client {
                        // This is a simplified example - real implementation would need proper key management
                        let result = self.handle_solana_transfer(
                            from_player_id, 
                            to_player_id, 
                            amount, 
                            tax_amount
                        ).await;
                        
                        match result {
                            Ok(signature) => {
                                // Update transaction with blockchain hash
                                self.update_transaction_status(
                                    transaction.id,
                                    TransactionStatus::Completed,
                                    Some(signature),
                                ).await?;
                            }
                            Err(e) => {
                                // Rollback and return error
                                tx.rollback().await?;
                                return Err(e);
                            }
                        }
                    } else {
                        tx.rollback().await?;
                        return Err(CurrencyError::System { 
                            reason: "Solana client not configured".to_string() 
                        });
                    }
                }
                CurrencyType::Exons => {
                    // Implement Exons token transfer logic
                    // Similar to Solana but would use token program
                    // For now, we'll just simulate it
                }
                _ => {
                    // Non-blockchain currencies don't need special handling
                }
            }
        }
        
        // Update balances
        self.remove_currency(from_player_id, currency_type, total_amount).await?;
        self.add_currency(to_player_id, currency_type, amount).await?;
        
        // Handle tax transfer to admin account
        if tax_amount > Decimal::ZERO {
            let tax_settings = self.get_tax_settings(currency.id).await?;
            
            // Find admin player ID from username
            let admin_player = sqlx::query!(
                r#"
                SELECT id FROM auth.players
                WHERE username = $1
                "#,
                tax_settings.admin_account
            )
            .fetch_optional(&self.db_pool)
            .await?;
            
            if let Some(admin) = admin_player {
                // Add tax to admin account
                self.add_currency(admin.id, currency_type, tax_amount).await?;
                
                // Create tax transaction record
                self.create_transaction(
                    Some(from_player_id),
                    Some(admin.id),
                    currency.id,
                    tax_amount,
                    Decimal::ZERO,
                    TransactionType::Tax,
                    Some(transaction.id),
                    Some(format!("Tax for transaction {}", transaction.id)),
                ).await?;
            }
        }
        
        // Update transaction status if not already updated by blockchain logic
        if transaction.status == TransactionStatus::Pending {
            self.update_transaction_status(
                transaction.id,
                TransactionStatus::Completed,
                None,
            ).await?;
        }
        
        // Commit transaction
        tx.commit().await?;
        
        // Return the updated transaction
        self.get_transaction(transaction.id).await
    }

    /// Handle Solana transfer (simplified example)
    async fn handle_solana_transfer(
        &self,
        from_player_id: Uuid,
        to_player_id: Uuid,
        amount: Decimal,
        tax_amount: Decimal,
    ) -> Result<String, CurrencyError> {
        // This is a simplified example - real implementation would need proper key management
        // and would interact with the Solana blockchain
        
        // In a real implementation, we would:
        // 1. Get the sender's wallet keypair
        // 2. Get the recipient's wallet address
        // 3. Create and sign a transaction
        // 4. Send the transaction to the Solana network
        // 5. Return the transaction signature
        
        // For now, we'll just return a mock signature
        Ok(format!("mock_signature_{}", Uuid::new_v4()))
    }

    /// Reward currency to a player (e.g., from gate completion)
    pub async fn reward_currency(
        &self,
        player_id: Uuid,
        currency_type: CurrencyType,
        amount: Decimal,
        transaction_type: TransactionType,
        reference_id: Option<Uuid>,
        notes: Option<String>,
    ) -> Result<Transaction, CurrencyError> {
        if amount <= Decimal::ZERO {
            return Err(CurrencyError::InvalidAmount { 
                reason: "Amount must be positive".to_string() 
            });
        }
        
        // Get currency
        let currency = self.get_currency_by_type(currency_type).await?;
        
        // Begin transaction
        let mut tx = self.db_pool.begin().await?;
        
        // Create transaction record
        let transaction = self.create_transaction(
            None, // System reward
            Some(player_id),
            currency.id,
            amount,
            Decimal::ZERO, // No tax on rewards
            transaction_type,
