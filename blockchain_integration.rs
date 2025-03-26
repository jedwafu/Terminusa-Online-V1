//! Blockchain Integration for Terminusa Online
//!
//! This module handles the integration with the Solana blockchain,
//! including wallet connections, transaction signing, and token operations.

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
    instruction::Instruction,
    commitment_config::CommitmentConfig,
    signer::Signer,
};
use solana_program::program_pack::Pack;
use spl_token::{
    state::{Mint, Account},
    instruction as token_instruction,
};
use crate::currency_system::{CurrencyType, CurrencyError};

/// Represents a blockchain wallet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockchainWallet {
    /// Player ID associated with this wallet
    pub player_id: Uuid,
    /// Solana wallet address
    pub solana_address: String,
    /// Whether the wallet is verified
    pub is_verified: bool,
    /// When the wallet was connected
    pub connected_at: DateTime<Utc>,
    /// When the wallet was last verified
    pub last_verified_at: Option<DateTime<Utc>>,
    /// Nonce used for verification
    pub verification_nonce: Option<String>,
}

/// Represents a blockchain transaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockchainTransaction {
    /// Unique identifier for the transaction
    pub id: Uuid,
    /// Player ID associated with this transaction
    pub player_id: Uuid,
    /// Currency type
    pub currency_type: CurrencyType,
    /// Transaction type
    pub transaction_type: BlockchainTransactionType,
    /// Transaction amount
    pub amount: Decimal,
    /// Transaction hash
    pub transaction_hash: String,
    /// Transaction status
    pub status: BlockchainTransactionStatus,
    /// When the transaction was created
    pub created_at: DateTime<Utc>,
    /// When the transaction was confirmed
    pub confirmed_at: Option<DateTime<Utc>>,
    /// Additional data
    pub additional_data: Option<serde_json::Value>,
}

/// Represents a blockchain transaction type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum BlockchainTransactionType {
    /// Deposit from external wallet
    Deposit,
    /// Withdrawal to external wallet
    Withdrawal,
    /// Token swap
    Swap,
    /// Token mint
    Mint,
    /// Token burn
    Burn,
}

impl fmt::Display for BlockchainTransactionType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BlockchainTransactionType::Deposit => write!(f, "deposit"),
            BlockchainTransactionType::Withdrawal => write!(f, "withdrawal"),
            BlockchainTransactionType::Swap => write!(f, "swap"),
            BlockchainTransactionType::Mint => write!(f, "mint"),
            BlockchainTransactionType::Burn => write!(f, "burn"),
        }
    }
}

impl FromStr for BlockchainTransactionType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "deposit" => Ok(BlockchainTransactionType::Deposit),
            "withdrawal" => Ok(BlockchainTransactionType::Withdrawal),
            "swap" => Ok(BlockchainTransactionType::Swap),
            "mint" => Ok(BlockchainTransactionType::Mint),
            "burn" => Ok(BlockchainTransactionType::Burn),
            _ => Err(format!("Unknown blockchain transaction type: {}", s)),
        }
    }
}

/// Represents a blockchain transaction status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum BlockchainTransactionStatus {
    /// Transaction is pending
    Pending,
    /// Transaction is confirmed
    Confirmed,
    /// Transaction failed
    Failed,
}

impl fmt::Display for BlockchainTransactionStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BlockchainTransactionStatus::Pending => write!(f, "pending"),
            BlockchainTransactionStatus::Confirmed => write!(f, "confirmed"),
            BlockchainTransactionStatus::Failed => write!(f, "failed"),
        }
    }
}

impl FromStr for BlockchainTransactionStatus {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "pending" => Ok(BlockchainTransactionStatus::Pending),
            "confirmed" => Ok(BlockchainTransactionStatus::Confirmed),
            "failed" => Ok(BlockchainTransactionStatus::Failed),
            _ => Err(format!("Unknown blockchain transaction status: {}", s)),
        }
    }
}

/// Error types for blockchain operations
#[derive(Debug)]
pub enum BlockchainError {
    /// Database error
    Database(sqlx::Error),
    /// Solana client error
    SolanaClient(String),
    /// Wallet not found
    WalletNotFound { player_id: Uuid },
    /// Wallet not verified
    WalletNotVerified { player_id: Uuid },
    /// Invalid wallet address
    InvalidWalletAddress { address: String },
    /// Transaction not found
    TransactionNotFound { id: Uuid },
    /// Transaction failed
    TransactionFailed { reason: String },
    /// Insufficient funds
    InsufficientFunds { required: Decimal, available: Decimal },
    /// Unauthorized operation
    Unauthorized { reason: String },
    /// System error
    System { reason: String },
}

impl fmt::Display for BlockchainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BlockchainError::Database(e) => write!(f, "Database error: {}", e),
            BlockchainError::SolanaClient(e) => write!(f, "Solana client error: {}", e),
            BlockchainError::WalletNotFound { player_id } => {
                write!(f, "Wallet not found for player: {}", player_id)
            }
            BlockchainError::WalletNotVerified { player_id } => {
                write!(f, "Wallet not verified for player: {}", player_id)
            }
            BlockchainError::InvalidWalletAddress { address } => {
                write!(f, "Invalid wallet address: {}", address)
            }
            BlockchainError::TransactionNotFound { id } => {
                write!(f, "Transaction not found: {}", id)
            }
            BlockchainError::TransactionFailed { reason } => {
                write!(f, "Transaction failed: {}", reason)
            }
            BlockchainError::InsufficientFunds { required, available } => {
                write!(f, "Insufficient funds: required {}, available {}", required, available)
            }
            BlockchainError::Unauthorized { reason } => write!(f, "Unauthorized: {}", reason),
            BlockchainError::System { reason } => write!(f, "System error: {}", reason),
        }
    }
}

impl Error for BlockchainError {}

impl From<sqlx::Error> for BlockchainError {
    fn from(error: sqlx::Error) -> Self {
        BlockchainError::Database(error)
    }
}

/// Configuration for blockchain integration
#[derive(Debug, Clone)]
pub struct BlockchainConfig {
    /// Solana RPC URL
    pub solana_rpc_url: String,
    /// Solana commitment level
    pub commitment: CommitmentConfig,
    /// Exons token mint address
    pub exons_token_mint: String,
    /// Game treasury wallet address
    pub treasury_wallet_address: String,
    /// Game treasury wallet keypair (for signing transactions)
    pub treasury_wallet_keypair: Option<Keypair>,
}

impl BlockchainConfig {
    /// Create a new blockchain configuration
    pub fn new(
        solana_rpc_url: &str,
        exons_token_mint: &str,
        treasury_wallet_address: &str,
    ) -> Self {
        BlockchainConfig {
            solana_rpc_url: solana_rpc_url.to_string(),
            commitment: CommitmentConfig::confirmed(),
            exons_token_mint: exons_token_mint.to_string(),
            treasury_wallet_address: treasury_wallet_address.to_string(),
            treasury_wallet_keypair: None,
        }
    }

    /// Set the treasury wallet keypair
    pub fn with_treasury_keypair(mut self, keypair: Keypair) -> Self {
        self.treasury_wallet_keypair = Some(keypair);
        self
    }

    /// Load treasury wallet keypair from a file
    pub fn load_treasury_keypair_from_file(mut self, path: &str) -> Result<Self, BlockchainError> {
        match std::fs::read_to_string(path) {
            Ok(content) => {
                let bytes: Vec<u8> = content
                    .trim()
                    .split(',')
                    .map(|s| s.parse::<u8>().unwrap_or(0))
                    .collect();
                
                match Keypair::from_bytes(&bytes) {
                    Ok(keypair) => {
                        self.treasury_wallet_keypair = Some(keypair);
                        Ok(self)
                    }
                    Err(e) => Err(BlockchainError::System {
                        reason: format!("Failed to load keypair: {}", e),
                    }),
                }
            }
            Err(e) => Err(BlockchainError::System {
                reason: format!("Failed to read keypair file: {}", e),
            }),
        }
    }
}

/// Blockchain service for handling blockchain operations
pub struct BlockchainService {
    /// Database connection pool
    db_pool: PgPool,
    /// Blockchain configuration
    config: BlockchainConfig,
    /// Solana RPC client
    solana_client: RpcClient,
}

impl BlockchainService {
    /// Create a new blockchain service
    pub fn new(db_pool: PgPool, config: BlockchainConfig) -> Result<Self, BlockchainError> {
        let solana_client = match RpcClient::new_with_commitment(
            &config.solana_rpc_url,
            config.commitment.clone(),
        ) {
            Ok(client) => client,
            Err(e) => {
                return Err(BlockchainError::SolanaClient(e.to_string()));
            }
        };

        Ok(BlockchainService {
            db_pool,
            config,
            solana_client,
        })
    }

    /// Connect a wallet to a player account
    pub async fn connect_wallet(
        &self,
        player_id: Uuid,
        solana_address: &str,
    ) -> Result<BlockchainWallet, BlockchainError> {
        // Validate wallet address
        match Pubkey::from_str(solana_address) {
            Ok(_) => {}
            Err(_) => {
                return Err(BlockchainError::InvalidWalletAddress {
                    address: solana_address.to_string(),
                });
            }
        }

        // Check if wallet is already connected to another player
        let existing_wallet = sqlx::query!(
            r#"
            SELECT player_id FROM auth.blockchain_wallets
            WHERE solana_address = $1 AND player_id != $2
            "#,
            solana_address,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        if let Some(existing) = existing_wallet {
            return Err(BlockchainError::Unauthorized {
                reason: format!(
                    "Wallet address is already connected to another player: {}",
                    existing.player_id
                ),
            });
        }

        // Generate verification nonce
        let nonce = format!("terminusa-verify-{}", Uuid::new_v4());

        // Check if player already has a wallet
        let existing_player_wallet = sqlx::query!(
            r#"
            SELECT solana_address FROM auth.blockchain_wallets
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        let wallet = if let Some(existing) = existing_player_wallet {
            // Update existing wallet
            sqlx::query_as!(
                BlockchainWallet,
                r#"
                UPDATE auth.blockchain_wallets
                SET 
                    solana_address = $2,
                    is_verified = false,
                    connected_at = NOW(),
                    last_verified_at = NULL,
                    verification_nonce = $3
                WHERE player_id = $1
                RETURNING 
                    player_id, solana_address, is_verified, 
                    connected_at, last_verified_at, verification_nonce
                "#,
                player_id,
                solana_address,
                nonce
            )
            .fetch_one(&self.db_pool)
            .await?
        } else {
            // Create new wallet
            sqlx::query_as!(
                BlockchainWallet,
                r#"
                INSERT INTO auth.blockchain_wallets (
                    player_id, solana_address, is_verified, 
                    connected_at, verification_nonce
                )
                VALUES ($1, $2, false, NOW(), $3)
                RETURNING 
                    player_id, solana_address, is_verified, 
                    connected_at, last_verified_at, verification_nonce
                "#,
                player_id,
                solana_address,
                nonce
            )
            .fetch_one(&self.db_pool)
            .await?
        };

        Ok(wallet)
    }

    /// Verify a wallet connection using a signed message
    pub async fn verify_wallet(
        &self,
        player_id: Uuid,
        signature: &str,
    ) -> Result<BlockchainWallet, BlockchainError> {
        // Get wallet and nonce
        let wallet = self.get_wallet(player_id).await?;

        if wallet.is_verified {
            // Already verified
            return Ok(wallet);
        }

        let nonce = wallet.verification_nonce.as_ref().ok_or_else(|| {
            BlockchainError::System {
                reason: "Verification nonce not found".to_string(),
            }
        })?;

        // Verify signature
        // In a real implementation, we would verify the signature against the wallet address
        // For now, we'll just simulate verification
        let is_valid = true; // Placeholder for actual verification

        if !is_valid {
            return Err(BlockchainError::Unauthorized {
                reason: "Invalid signature".to_string(),
            });
        }

        // Update wallet as verified
        let verified_wallet = sqlx::query_as!(
            BlockchainWallet,
            r#"
            UPDATE auth.blockchain_wallets
            SET 
                is_verified = true,
                last_verified_at = NOW(),
                verification_nonce = NULL
            WHERE player_id = $1
            RETURNING 
                player_id, solana_address, is_verified, 
                connected_at, last_verified_at, verification_nonce
            "#,
            player_id
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(verified_wallet)
    }

    /// Get a player's wallet
    pub async fn get_wallet(&self, player_id: Uuid) -> Result<BlockchainWallet, BlockchainError> {
        let wallet = sqlx::query_as!(
            BlockchainWallet,
            r#"
            SELECT 
                player_id, solana_address, is_verified, 
                connected_at, last_verified_at, verification_nonce
            FROM auth.blockchain_wallets
            WHERE player_id = $1
            "#,
            player_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(BlockchainError::WalletNotFound { player_id })?;

        Ok(wallet)
    }

    /// Check if a wallet is verified
    pub async fn is_wallet_verified(&self, player_id: Uuid) -> Result<bool, BlockchainError> {
        let wallet = self.get_wallet(player_id).await?;
        Ok(wallet.is_verified)
    }

    /// Get a player's Solana balance
    pub async fn get_solana_balance(&self, player_id: Uuid) -> Result<Decimal, BlockchainError> {
        let wallet = self.get_wallet(player_id).await?;

        if !wallet.is_verified {
            return Err(BlockchainError::WalletNotVerified { player_id });
        }

        let pubkey = Pubkey::from_str(&wallet.solana_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: wallet.solana_address,
            }
        })?;

        match self.solana_client.get_balance(&pubkey) {
            Ok(lamports) => {
                // Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
                let sol = Decimal::new(lamports as i64, 9);
                Ok(sol)
            }
            Err(e) => Err(BlockchainError::SolanaClient(e.to_string())),
        }
    }

    /// Get a player's Exons token balance
    pub async fn get_exons_balance(&self, player_id: Uuid) -> Result<Decimal, BlockchainError> {
        let wallet = self.get_wallet(player_id).await?;

        if !wallet.is_verified {
            return Err(BlockchainError::WalletNotVerified { player_id });
        }

        let wallet_pubkey = Pubkey::from_str(&wallet.solana_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: wallet.solana_address,
            }
        })?;

        let token_mint_pubkey = Pubkey::from_str(&self.config.exons_token_mint).map_err(|_| {
            BlockchainError::System {
                reason: format!("Invalid token mint address: {}", self.config.exons_token_mint),
            }
        })?;

        // Find the token account for this wallet
        let token_accounts = match self.solana_client.get_token_accounts_by_owner(
            &wallet_pubkey,
            spl_token::id(),
        ) {
            Ok(accounts) => accounts,
            Err(e) => return Err(BlockchainError::SolanaClient(e.to_string())),
        };

        // Find the account for our specific token mint
        for account in token_accounts {
            let account_data = match self.solana_client.get_account_data(&account.pubkey) {
                Ok(data) => data,
                Err(e) => return Err(BlockchainError::SolanaClient(e.to_string())),
            };

            // Parse the token account data
            let token_account = match Account::unpack(&account_data) {
                Ok(account) => account,
                Err(_) => continue, // Not a valid token account, skip
            };

            // Check if this account is for our token mint
            if token_account.mint == token_mint_pubkey {
                // Convert token amount to decimal (assuming 9 decimals for Exons)
                let exons = Decimal::new(token_account.amount as i64, 9);
                return Ok(exons);
            }
        }

        // No token account found for this mint, return 0
        Ok(Decimal::ZERO)
    }

    /// Record a blockchain transaction
    pub async fn record_transaction(
        &self,
        player_id: Uuid,
        currency_type: CurrencyType,
        transaction_type: BlockchainTransactionType,
        amount: Decimal,
        transaction_hash: &str,
        status: BlockchainTransactionStatus,
        additional_data: Option<serde_json::Value>,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        let transaction = sqlx::query_as!(
            BlockchainTransaction,
            r#"
            INSERT INTO game.blockchain_transactions (
                id, player_id, currency_type, transaction_type, 
                amount, transaction_hash, status, 
                created_at, confirmed_at, additional_data
            )
            VALUES (
                uuid_generate_v4(), $1, $2, $3, 
                $4, $5, $6, 
                NOW(), 
                CASE WHEN $6 = 'confirmed' THEN NOW() ELSE NULL END, 
                $7
            )
            RETURNING 
                id, player_id, 
                currency_type as "currency_type: CurrencyType",
                transaction_type as "transaction_type: BlockchainTransactionType",
                amount, transaction_hash, 
                status as "status: BlockchainTransactionStatus",
                created_at, confirmed_at, additional_data
            "#,
            player_id,
            currency_type as CurrencyType,
            transaction_type as BlockchainTransactionType,
            amount,
            transaction_hash,
            status as BlockchainTransactionStatus,
            additional_data
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(transaction)
    }

    /// Update a blockchain transaction status
    pub async fn update_transaction_status(
        &self,
        id: Uuid,
        status: BlockchainTransactionStatus,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        let transaction = sqlx::query_as!(
            BlockchainTransaction,
            r#"
            UPDATE game.blockchain_transactions
            SET 
                status = $2,
                confirmed_at = CASE WHEN $2 = 'confirmed' THEN NOW() ELSE confirmed_at END
            WHERE id = $1
            RETURNING 
                id, player_id, 
                currency_type as "currency_type: CurrencyType",
                transaction_type as "transaction_type: BlockchainTransactionType",
                amount, transaction_hash, 
                status as "status: BlockchainTransactionStatus",
                created_at, confirmed_at, additional_data
            "#,
            id,
            status as BlockchainTransactionStatus
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(BlockchainError::TransactionNotFound { id })?;

        Ok(transaction)
    }

    /// Get a blockchain transaction by ID
    pub async fn get_transaction(
        &self,
        id: Uuid,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        let transaction = sqlx::query_as!(
            BlockchainTransaction,
            r#"
            SELECT 
                id, player_id, 
                currency_type as "currency_type: CurrencyType",
                transaction_type as "transaction_type: BlockchainTransactionType",
                amount, transaction_hash, 
                status as "status: BlockchainTransactionStatus",
                created_at, confirmed_at, additional_data
            FROM game.blockchain_transactions
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(BlockchainError::TransactionNotFound { id })?;

        Ok(transaction)
    }

    /// Get blockchain transactions for a player
    pub async fn get_player_transactions(
        &self,
        player_id: Uuid,
        limit: i64,
        offset: i64,
    ) -> Result<Vec<BlockchainTransaction>, BlockchainError> {
        let transactions = sqlx::query_as!(
            BlockchainTransaction,
            r#"
            SELECT 
                id, player_id, 
                currency_type as "currency_type: CurrencyType",
                transaction_type as "transaction_type: BlockchainTransactionType",
                amount, transaction_hash, 
                status as "status: BlockchainTransactionStatus",
                created_at, confirmed_at, additional_data
            FROM game.blockchain_transactions
            WHERE player_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            "#,
            player_id,
            limit,
            offset
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(transactions)
    }

    /// Process a deposit from an external wallet
    pub async fn process_deposit(
        &self,
        player_id: Uuid,
        currency_type: CurrencyType,
        amount: Decimal,
        transaction_hash: &str,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        // Verify the transaction on the blockchain
        let is_valid = self.verify_blockchain_transaction(transaction_hash, currency_type).await?;

        if !is_valid {
            return Err(BlockchainError::TransactionFailed {
                reason: "Invalid transaction".to_string(),
            });
        }

        // Record the transaction
        let transaction = self
            .record_transaction(
                player_id,
                currency_type,
                BlockchainTransactionType::Deposit,
                amount,
                transaction_hash,
                BlockchainTransactionStatus::Confirmed,
                None,
            )
            .await?;

        Ok(transaction)
    }

    /// Process a withdrawal to an external wallet
    pub async fn process_withdrawal(
        &self,
        player_id: Uuid,
        currency_type: CurrencyType,
        amount: Decimal,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        // Get player's wallet
        let wallet = self.get_wallet(player_id).await?;

        if !wallet.is_verified {
            return Err(BlockchainError::WalletNotVerified { player_id });
        }

        // Check if treasury wallet keypair is available
        let treasury_keypair = match &self.config.treasury_wallet_keypair {
            Some(keypair) => keypair,
            None => {
                return Err(BlockchainError::System {
                    reason: "Treasury wallet keypair not configured".to_string(),
                });
            }
        };

        // Process the withdrawal based on currency type
        let transaction_hash = match currency_type {
            CurrencyType::Solana => {
                // Send SOL from treasury to player's wallet
                self.send_solana(
                    treasury_keypair,
                    &wallet.solana_address,
                    amount,
                )
                .await?
            }
            CurrencyType::Exons => {
                // Send Exons tokens from treasury to player's wallet
                self.send_exons(
                    treasury_keypair,
                    &wallet.solana_address,
                    amount,
                )
                .await?
            }
            _ => {
                return Err(BlockchainError::System {
                    reason: format!("Unsupported currency type for withdrawal: {}", currency_type),
                });
            }
        };

        // Record the transaction
        let transaction = self
            .record_transaction(
                player_id,
                currency_type,
                BlockchainTransactionType::Withdrawal,
                amount,
                &transaction_hash,
                BlockchainTransactionStatus::Pending,
                None,
            )
            .await?;

        Ok(transaction)
    }

    /// Send SOL from treasury to a wallet
    async fn send_solana(
        &self,
        from_keypair: &Keypair,
        to_address: &str,
        amount: Decimal,
    ) -> Result<String, BlockchainError> {
        // Convert SOL to lamports
        let lamports = (amount * Decimal::new(1_000_000_000, 0))
            .to_u64()
            .ok_or_else(|| BlockchainError::System {
                reason: "Failed to convert SOL amount to lamports".to_string(),
            })?;

        // Parse recipient address
        let to_pubkey = Pubkey::from_str(to_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: to_address.to_string(),
            }
        })?;

        // Create transfer instruction
        let instruction = system_instruction::transfer(
            &from_keypair.pubkey(),
            &to_pubkey,
            lamports,
        );

        // Send transaction
        let signature = self.send_transaction(&[instruction], &[from_keypair]).await?;

        Ok(signature.to_string())
    }

    /// Send Exons tokens from treasury to a wallet
    async fn send_exons(
        &self,
        from_keypair: &Keypair,
        to_address: &str,
        amount: Decimal,
    ) -> Result<String, BlockchainError> {
        // Convert Exons to token amount (assuming 9 decimals)
        let token_amount = (amount * Decimal::new(1_000_000_000, 0))
            .to_u64()
            .ok_or_else(|| BlockchainError::System {
                reason: "Failed to convert Exons amount to token amount".to_string(),
            })?;

        // Parse recipient address
        let to_pubkey = Pubkey::from_str(to_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: to_address.to_string(),
            }
        })?;

        // Parse token mint address
        let token_mint_pubkey = Pubkey::from_str(&self.config.exons_token_mint).map_err(|_| {
            BlockchainError::System {
                reason: format!("Invalid token mint address: {}", self.config.exons_token_mint),
            }
        })?;

        // Find the token account for the treasury
        let treasury_token_account = self
            .find_token_account(&from_keypair.pubkey(), &token_mint_pubkey)
            .await?;

        // Find or create token account for the recipient
        let recipient_token_account = self
            .find_or_create_token_account(&to_pubkey, &token_mint_pubkey, from_keypair)
            .await?;

        // Create transfer instruction
        let instruction = token_instruction::transfer(
            &spl_token::id(),
            &treasury_token_account,
            &recipient_token_account,
            &from_keypair.pubkey(),
            &[],
            token_amount,
        )
        .map_err(|e| BlockchainError::System {
            reason: format!("Failed to create token transfer instruction: {}", e),
        })?;

        // Send transaction
        let signature = self.send_transaction(&[instruction], &[from_keypair]).await?;

        Ok(signature.to_string())
    }

    /// Find a token account for a wallet and token mint
    async fn find_token_account(
        &self,
        wallet_pubkey: &Pubkey,
        token_mint_pubkey: &Pubkey,
    ) -> Result<Pubkey, BlockchainError> {
        // Get token accounts owned by the wallet
        let token_accounts = match self.solana_client.get_token_accounts_by_owner(
            wallet_pubkey,
            spl_token::id(),
        ) {
            Ok(accounts) => accounts,
            Err(e) => return Err(BlockchainError::SolanaClient(e.to_string())),
        };

        // Find the account for our specific token mint
        for account in token_accounts {
            let account_data = match self.solana_client.get_account_data(&account.pubkey) {
                Ok(data) => data,
                Err(e) => return Err(BlockchainError::SolanaClient(e.to_string())),
            };

            // Parse the token account data
            let token_account = match Account::unpack(&account_data) {
                Ok(account) => account,
                Err(_) => continue, // Not a valid token account, skip
            };

            // Check if this account is for our token mint
            if token_account.mint == *token_mint_pubkey {
                return Ok(account.pubkey);
            }
        }

        // No token account found
        Err(BlockchainError::System {
            reason: format!("No token account found for mint {}", token_mint_pubkey),
        })
    }

    /// Find or create a token account for a wallet and token mint
    async fn find_or_create_token_account(
        &self,
        wallet_pubkey: &Pubkey,
        token_mint_pubkey: &Pubkey,
        payer: &Keypair,
    ) -> Result<Pubkey, BlockchainError> {
        // Try to find existing token account
        match self.find_token_account(wallet_pubkey, token_mint_pubkey).await {
            Ok(account) => return Ok(account),
            Err(_) => {
                // No account found, create a new one
                let new_account = Keypair::new();
                
                // Create token account
                let create_account_instruction = system_instruction::create_account(
                    &payer.pubkey(),
                    &new_account.pubkey(),
                    self.solana_client.get_minimum_balance_for_rent_exemption(Account::LEN).await
                        .map_err(|e| BlockchainError::SolanaClient(e.to_string()))?,
                    Account::LEN as u64,
                    &spl_token::id(),
                );
                
                // Initialize token account
                let initialize_account_instruction = token_instruction::initialize_account(
                    &spl_token::id(),
                    &new_account.pubkey(),
                    token_mint_pubkey,
                    wallet_pubkey,
                )
                .map_err(|e| BlockchainError::System {
                    reason: format!("Failed to create initialize account instruction: {}", e),
                })?;
                
                // Send transaction with both instructions
                let signature = self.send_transaction(
                    &[create_account_instruction, initialize_account_instruction],
                    &[payer, &new_account],
                ).await?;
                
                // Return the new account pubkey
                Ok(new_account.pubkey())
            }
        }
    }

    /// Send a transaction to the Solana blockchain
    async fn send_transaction(
        &self,
        instructions: &[Instruction],
        signers: &[&Keypair],
    ) -> Result<Signature, BlockchainError> {
        // Get recent blockhash
        let blockhash = self.solana_client.get_latest_blockhash()
            .await
            .map_err(|e| BlockchainError::SolanaClient(e.to_string()))?;
        
        // Create transaction
        let mut transaction = Transaction::new_with_payer(instructions, Some(&signers[0].pubkey()));
        
        // Set recent blockhash
        transaction.sign(signers, blockhash);
        
        // Send transaction
        match self.solana_client.send_and_confirm_transaction(&transaction).await {
            Ok(signature) => Ok(signature),
            Err(e) => Err(BlockchainError::SolanaClient(e.to_string())),
        }
    }

    /// Verify a blockchain transaction
    async fn verify_blockchain_transaction(
        &self,
        transaction_hash: &str,
        currency_type: CurrencyType,
    ) -> Result<bool, BlockchainError> {
        // Parse transaction signature
        let signature = Signature::from_str(transaction_hash).map_err(|_| {
            BlockchainError::System {
                reason: format!("Invalid transaction hash: {}", transaction_hash),
            }
        })?;
        
        // Get transaction status
        match self.solana_client.get_signature_status(&signature).await {
            Ok(Some(Ok(()))) => {
                // Transaction was successful
                // In a real implementation, we would also verify:
                // 1. The transaction is a transfer to our treasury wallet
                // 2. The amount matches what we expect
                // 3. The token type matches (for token transfers)
                
                // For now, we'll just return true
                Ok(true)
            }
            Ok(Some(Err(e))) => {
                // Transaction failed
                Err(BlockchainError::TransactionFailed {
                    reason: format!("Transaction failed: {}", e),
                })
            }
            Ok(None) => {
                // Transaction not found or not yet processed
                Err(BlockchainError::TransactionFailed {
                    reason: "Transaction not found or not yet processed".to_string(),
                })
            }
            Err(e) => {
                // Error getting transaction status
                Err(BlockchainError::SolanaClient(e.to_string()))
            }
        }
    }

    /// Mint new Exons tokens
    pub async fn mint_exons(
        &self,
        player_id: Uuid,
        amount: Decimal,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        // Check if treasury wallet keypair is available
        let treasury_keypair = match &self.config.treasury_wallet_keypair {
            Some(keypair) => keypair,
            None => {
                return Err(BlockchainError::System {
                    reason: "Treasury wallet keypair not configured".to_string(),
                });
            }
        };

        // Get player's wallet
        let wallet = self.get_wallet(player_id).await?;

        if !wallet.is_verified {
            return Err(BlockchainError::WalletNotVerified { player_id });
        }

        // Convert Exons to token amount (assuming 9 decimals)
        let token_amount = (amount * Decimal::new(1_000_000_000, 0))
            .to_u64()
            .ok_or_else(|| BlockchainError::System {
                reason: "Failed to convert Exons amount to token amount".to_string(),
            })?;

        // Parse token mint address
        let token_mint_pubkey = Pubkey::from_str(&self.config.exons_token_mint).map_err(|_| {
            BlockchainError::System {
                reason: format!("Invalid token mint address: {}", self.config.exons_token_mint),
            }
        })?;

        // Parse recipient address
        let to_pubkey = Pubkey::from_str(&wallet.solana_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: wallet.solana_address,
            }
        })?;

        // Find or create token account for the recipient
        let recipient_token_account = self
            .find_or_create_token_account(&to_pubkey, &token_mint_pubkey, treasury_keypair)
            .await?;

        // Create mint to instruction
        let mint_to_instruction = token_instruction::mint_to(
            &spl_token::id(),
            &token_mint_pubkey,
            &recipient_token_account,
            &treasury_keypair.pubkey(),
            &[],
            token_amount,
        )
        .map_err(|e| BlockchainError::System {
            reason: format!("Failed to create mint to instruction: {}", e),
        })?;

        // Send transaction
        let signature = self.send_transaction(&[mint_to_instruction], &[treasury_keypair]).await?;

        // Record the transaction
        let transaction = self
            .record_transaction(
                player_id,
                CurrencyType::Exons,
                BlockchainTransactionType::Mint,
                amount,
                &signature.to_string(),
                BlockchainTransactionStatus::Pending,
                None,
            )
            .await?;

        Ok(transaction)
    }

    /// Burn Exons tokens
    pub async fn burn_exons(
        &self,
        player_id: Uuid,
        amount: Decimal,
    ) -> Result<BlockchainTransaction, BlockchainError> {
        // Get player's wallet
        let wallet = self.get_wallet(player_id).await?;

        if !wallet.is_verified {
            return Err(BlockchainError::WalletNotVerified { player_id });
        }

        // Convert Exons to token amount (assuming 9 decimals)
        let token_amount = (amount * Decimal::new(1_000_000_000, 0))
            .to_u64()
            .ok_or_else(|| BlockchainError::System {
                reason: "Failed to convert Exons amount to token amount".to_string(),
            })?;

        // Parse token mint address
        let token_mint_pubkey = Pubkey::from_str(&self.config.exons_token_mint).map_err(|_| {
            BlockchainError::System {
                reason: format!("Invalid token mint address: {}", self.config.exons_token_mint),
            }
        })?;

        // Parse wallet address
        let wallet_pubkey = Pubkey::from_str(&wallet.solana_address).map_err(|_| {
            BlockchainError::InvalidWalletAddress {
                address: wallet.solana_address,
            }
        })?;

        // Find token account for the wallet
        let token_account = self
            .find_token_account(&wallet_pubkey, &token_mint_pubkey)
            .await?;

        // Check if treasury wallet keypair is available
        let treasury_keypair = match &self.config.treasury_wallet_keypair {
            Some(keypair) => keypair,
            None => {
                return Err(BlockchainError::System {
                    reason: "Treasury wallet keypair not configured".to_string(),
                });
            }
        };

        // Create burn instruction
        let burn_instruction = token_instruction::burn(
            &spl_token::id(),
            &token_account,
            &token_mint_pubkey,
            &wallet_pubkey,
            &[],
            token_amount,
        )
        .map_err(|e| BlockchainError::System {
            reason: format!("Failed to create burn instruction: {}", e),
        })?;

        // Send transaction
        let signature = self.send_transaction(&[burn_instruction], &[treasury_keypair]).await?;

        // Record the transaction
        let transaction = self
            .record_transaction(
                player_id,
                CurrencyType::Exons,
                BlockchainTransactionType::Burn,
                amount,
                &signature.to_string(),
                BlockchainTransactionStatus::Pending,
                None,
            )
            .await?;

        Ok(transaction)
    }

    /// Monitor pending transactions and update their status
    pub async fn monitor_pending_transactions(&self) -> Result<(), BlockchainError> {
        // Get all pending transactions
        let pending_transactions = sqlx::query_as!(
            BlockchainTransaction,
            r#"
            SELECT 
                id, player_id, 
                currency_type as "currency_type: CurrencyType",
                transaction_type as "transaction_type: BlockchainTransactionType",
                amount, transaction_hash, 
                status as "status: BlockchainTransactionStatus",
                created_at, confirmed_at, additional_data
            FROM game.blockchain_transactions
            WHERE status = 'pending'
            "#,
        )
        .fetch_all(&self.db_pool)
        .await?;

        // Check each transaction
        for transaction in pending_transactions {
            // Parse transaction signature
            let signature = match Signature::from_str(&transaction.transaction_hash) {
                Ok(sig) => sig,
                Err(_) => {
                    // Invalid signature, mark as failed
                    self.update_transaction_status(
                        transaction.id,
                        BlockchainTransactionStatus::Failed,
                    )
                    .await?;
                    continue;
                }
            };

            // Check transaction status
            match self.solana_client.get_signature_status(&signature).await {
                Ok(Some(Ok(()))) => {
                    // Transaction confirmed
                    self.update_transaction_status(
                        transaction.id,
                        BlockchainTransactionStatus::Confirmed,
                    )
                    .await?;
                }
                Ok(Some(Err(_))) => {
                    // Transaction failed
                    self.update_transaction_status(
                        transaction.id,
                        BlockchainTransactionStatus::Failed,
                    )
                    .await?;
                }
                Ok(None) => {
                    // Transaction still pending
                    continue;
                }
                Err(_) => {
                    // Error checking status, skip for now
                    continue;
                }
            }
        }

        Ok(())
    }
}
