//! Token Swapper System for Terminusa Online
//!
//! This module implements the token swapping functionality between
//! Solana, Exons, and Crystals currencies with dynamic exchange rates.

use std::fmt;
use std::error::Error;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use rust_decimal::Decimal;
use sqlx::{PgPool, Row, postgres::PgRow};
use crate::currency_system::{CurrencyType, CurrencyError, CurrencyService};

/// Represents the different swap directions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SwapDirection {
    /// Solana to Exons
    SolanaToExons,
    /// Exons to Solana
    ExonsToSolana,
    /// Exons to Crystals
    ExonsToCrystals,
    /// Crystals to Exons
    CrystalsToExons,
}

impl fmt::Display for SwapDirection {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SwapDirection::SolanaToExons => write!(f, "Solana to Exons"),
            SwapDirection::ExonsToSolana => write!(f, "Exons to Solana"),
            SwapDirection::ExonsToCrystals => write!(f, "Exons to Crystals"),
            SwapDirection::CrystalsToExons => write!(f, "Crystals to Exons"),
        }
    }
}

/// Represents an exchange rate between two currencies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExchangeRate {
    /// Unique identifier for the exchange rate
    pub id: i32,
    /// Source currency type
    pub from_currency: CurrencyType,
    /// Target currency type
    pub to_currency: CurrencyType,
    /// Exchange rate (how much of to_currency for 1 unit of from_currency)
    pub rate: Decimal,
    /// Minimum amount that can be swapped
    pub min_amount: Decimal,
    /// Maximum amount that can be swapped
    pub max_amount: Decimal,
    /// Fee percentage for the swap
    pub fee_percentage: Decimal,
    /// Whether the rate is currently active
    pub is_active: bool,
    /// When the rate was last updated
    pub updated_at: DateTime<Utc>,
    /// Who last updated the rate
    pub updated_by: Option<Uuid>,
}

/// Represents a swap transaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwapTransaction {
    /// Unique identifier for the swap
    pub id: Uuid,
    /// Player who performed the swap
    pub player_id: Uuid,
    /// Source currency type
    pub from_currency: CurrencyType,
    /// Target currency type
    pub to_currency: CurrencyType,
    /// Amount of source currency
    pub from_amount: Decimal,
    /// Amount of target currency
    pub to_amount: Decimal,
    /// Fee amount
    pub fee_amount: Decimal,
    /// Exchange rate used
    pub rate: Decimal,
    /// Status of the swap
    pub status: SwapStatus,
    /// When the swap was created
    pub created_at: DateTime<Utc>,
    /// When the swap was completed
    pub completed_at: Option<DateTime<Utc>>,
    /// Transaction ID for the source currency
    pub from_transaction_id: Option<Uuid>,
    /// Transaction ID for the target currency
    pub to_transaction_id: Option<Uuid>,
}

/// Represents the status of a swap
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SwapStatus {
    /// Swap is pending
    Pending,
    /// Swap is completed
    Completed,
    /// Swap failed
    Failed,
    /// Swap was cancelled
    Cancelled,
}

impl fmt::Display for SwapStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SwapStatus::Pending => write!(f, "pending"),
            SwapStatus::Completed => write!(f, "completed"),
            SwapStatus::Failed => write!(f, "failed"),
            SwapStatus::Cancelled => write!(f, "cancelled"),
        }
    }
}

/// Error types for token swapper operations
#[derive(Debug)]
pub enum SwapError {
    /// Database error
    Database(sqlx::Error),
    /// Currency error
    Currency(CurrencyError),
    /// Exchange rate not found
    ExchangeRateNotFound { from: CurrencyType, to: CurrencyType },
    /// Exchange rate inactive
    ExchangeRateInactive { from: CurrencyType, to: CurrencyType },
    /// Amount too small
    AmountTooSmall { min: Decimal, provided: Decimal },
    /// Amount too large
    AmountTooLarge { max: Decimal, provided: Decimal },
    /// Swap transaction not found
    SwapNotFound { id: Uuid },
    /// Unauthorized operation
    Unauthorized { reason: String },
    /// System error
    System { reason: String },
}

impl fmt::Display for SwapError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SwapError::Database(e) => write!(f, "Database error: {}", e),
            SwapError::Currency(e) => write!(f, "Currency error: {}", e),
            SwapError::ExchangeRateNotFound { from, to } => {
                write!(f, "Exchange rate not found: {} to {}", from, to)
            }
            SwapError::ExchangeRateInactive { from, to } => {
                write!(f, "Exchange rate is inactive: {} to {}", from, to)
            }
            SwapError::AmountTooSmall { min, provided } => {
                write!(f, "Amount too small: minimum {}, provided {}", min, provided)
            }
            SwapError::AmountTooLarge { max, provided } => {
                write!(f, "Amount too large: maximum {}, provided {}", max, provided)
            }
            SwapError::SwapNotFound { id } => write!(f, "Swap transaction not found: {}", id),
            SwapError::Unauthorized { reason } => write!(f, "Unauthorized: {}", reason),
            SwapError::System { reason } => write!(f, "System error: {}", reason),
        }
    }
}

impl Error for SwapError {}

impl From<sqlx::Error> for SwapError {
    fn from(error: sqlx::Error) -> Self {
        SwapError::Database(error)
    }
}

impl From<CurrencyError> for SwapError {
    fn from(error: CurrencyError) -> Self {
        SwapError::Currency(error)
    }
}

/// Token swapper service for managing currency exchanges
pub struct TokenSwapperService {
    /// Database connection pool
    db_pool: PgPool,
    /// Currency service for handling currency operations
    currency_service: CurrencyService,
}

impl TokenSwapperService {
    /// Create a new token swapper service
    pub fn new(db_pool: PgPool, currency_service: CurrencyService) -> Self {
        TokenSwapperService {
            db_pool,
            currency_service,
        }
    }

    /// Get all exchange rates
    pub async fn get_all_exchange_rates(&self) -> Result<Vec<ExchangeRate>, SwapError> {
        let rates = sqlx::query_as!(
            ExchangeRate,
            r#"
            SELECT 
                id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                rate, min_amount, max_amount, fee_percentage,
                is_active, updated_at, updated_by
            FROM game.exchange_rates
            ORDER BY id
            "#
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(rates)
    }

    /// Get active exchange rates
    pub async fn get_active_exchange_rates(&self) -> Result<Vec<ExchangeRate>, SwapError> {
        let rates = sqlx::query_as!(
            ExchangeRate,
            r#"
            SELECT 
                id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                rate, min_amount, max_amount, fee_percentage,
                is_active, updated_at, updated_by
            FROM game.exchange_rates
            WHERE is_active = true
            ORDER BY id
            "#
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(rates)
    }

    /// Get exchange rate for a specific currency pair
    pub async fn get_exchange_rate(
        &self,
        from_currency: CurrencyType,
        to_currency: CurrencyType,
    ) -> Result<ExchangeRate, SwapError> {
        let rate = sqlx::query_as!(
            ExchangeRate,
            r#"
            SELECT 
                id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                rate, min_amount, max_amount, fee_percentage,
                is_active, updated_at, updated_by
            FROM game.exchange_rates
            WHERE from_currency = $1 AND to_currency = $2
            "#,
            from_currency as CurrencyType,
            to_currency as CurrencyType
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(SwapError::ExchangeRateNotFound {
            from: from_currency,
            to: to_currency,
        })?;

        if !rate.is_active {
            return Err(SwapError::ExchangeRateInactive {
                from: from_currency,
                to: to_currency,
            });
        }

        Ok(rate)
    }

    /// Update an exchange rate
    pub async fn update_exchange_rate(
        &self,
        from_currency: CurrencyType,
        to_currency: CurrencyType,
        rate: Decimal,
        min_amount: Decimal,
        max_amount: Decimal,
        fee_percentage: Decimal,
        is_active: bool,
        updated_by: Uuid,
    ) -> Result<ExchangeRate, SwapError> {
        // Validate inputs
        if rate <= Decimal::ZERO {
            return Err(SwapError::System {
                reason: "Rate must be positive".to_string(),
            });
        }

        if min_amount <= Decimal::ZERO {
            return Err(SwapError::System {
                reason: "Minimum amount must be positive".to_string(),
            });
        }

        if max_amount <= min_amount {
            return Err(SwapError::System {
                reason: "Maximum amount must be greater than minimum amount".to_string(),
            });
        }

        if fee_percentage < Decimal::ZERO || fee_percentage > Decimal::new(100, 0) {
            return Err(SwapError::System {
                reason: "Fee percentage must be between 0 and 100".to_string(),
            });
        }

        // Check if the exchange rate exists
        let existing_rate = sqlx::query!(
            r#"
            SELECT id FROM game.exchange_rates
            WHERE from_currency = $1 AND to_currency = $2
            "#,
            from_currency as CurrencyType,
            to_currency as CurrencyType
        )
        .fetch_optional(&self.db_pool)
        .await?;

        let updated_rate = if let Some(existing) = existing_rate {
            // Update existing rate
            sqlx::query_as!(
                ExchangeRate,
                r#"
                UPDATE game.exchange_rates
                SET 
                    rate = $3,
                    min_amount = $4,
                    max_amount = $5,
                    fee_percentage = $6,
                    is_active = $7,
                    updated_at = NOW(),
                    updated_by = $8
                WHERE from_currency = $1 AND to_currency = $2
                RETURNING 
                    id, 
                    from_currency as "from_currency: CurrencyType",
                    to_currency as "to_currency: CurrencyType",
                    rate, min_amount, max_amount, fee_percentage,
                    is_active, updated_at, updated_by
                "#,
                from_currency as CurrencyType,
                to_currency as CurrencyType,
                rate,
                min_amount,
                max_amount,
                fee_percentage,
                is_active,
                updated_by
            )
            .fetch_one(&self.db_pool)
            .await?
        } else {
            // Create new rate
            sqlx::query_as!(
                ExchangeRate,
                r#"
                INSERT INTO game.exchange_rates (
                    from_currency, to_currency, rate, 
                    min_amount, max_amount, fee_percentage,
                    is_active, updated_at, updated_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
                RETURNING 
                    id, 
                    from_currency as "from_currency: CurrencyType",
                    to_currency as "to_currency: CurrencyType",
                    rate, min_amount, max_amount, fee_percentage,
                    is_active, updated_at, updated_by
                "#,
                from_currency as CurrencyType,
                to_currency as CurrencyType,
                rate,
                min_amount,
                max_amount,
                fee_percentage,
                is_active,
                updated_by
            )
            .fetch_one(&self.db_pool)
            .await?
        };

        Ok(updated_rate)
    }

    /// Calculate the amount of target currency for a given amount of source currency
    pub async fn calculate_swap_amount(
        &self,
        from_currency: CurrencyType,
        to_currency: CurrencyType,
        from_amount: Decimal,
    ) -> Result<(Decimal, Decimal, Decimal), SwapError> {
        if from_amount <= Decimal::ZERO {
            return Err(SwapError::System {
                reason: "Amount must be positive".to_string(),
            });
        }

        let rate = self.get_exchange_rate(from_currency, to_currency).await?;

        if from_amount < rate.min_amount {
            return Err(SwapError::AmountTooSmall {
                min: rate.min_amount,
                provided: from_amount,
            });
        }

        if from_amount > rate.max_amount {
            return Err(SwapError::AmountTooLarge {
                max: rate.max_amount,
                provided: from_amount,
            });
        }

        let fee_amount = from_amount * rate.fee_percentage / Decimal::new(100, 0);
        let to_amount = (from_amount - fee_amount) * rate.rate;

        Ok((to_amount, fee_amount, rate.rate))
    }

    /// Perform a currency swap
    pub async fn swap_currency(
        &self,
        player_id: Uuid,
        from_currency: CurrencyType,
        to_currency: CurrencyType,
        from_amount: Decimal,
    ) -> Result<SwapTransaction, SwapError> {
        if from_amount <= Decimal::ZERO {
            return Err(SwapError::System {
                reason: "Amount must be positive".to_string(),
            });
        }

        // Calculate swap amounts
        let (to_amount, fee_amount, rate) = self
            .calculate_swap_amount(from_currency, to_currency, from_amount)
            .await?;

        // Begin transaction
        let mut tx = self.db_pool.begin().await?;

        // Create swap record
        let swap = sqlx::query_as!(
            SwapTransaction,
            r#"
            INSERT INTO game.swap_transactions (
                id, player_id, 
                from_currency, to_currency, 
                from_amount, to_amount, fee_amount, rate,
                status, created_at, completed_at,
                from_transaction_id, to_transaction_id
            )
            VALUES (
                uuid_generate_v4(), $1, 
                $2, $3, 
                $4, $5, $6, $7,
                'pending', NOW(), NULL,
                NULL, NULL
            )
            RETURNING 
                id, player_id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                from_amount, to_amount, fee_amount, rate,
                status as "status: SwapStatus",
                created_at, completed_at,
                from_transaction_id, to_transaction_id
            "#,
            player_id,
            from_currency as CurrencyType,
            to_currency as CurrencyType,
            from_amount,
            to_amount,
            fee_amount,
            rate
        )
        .fetch_one(&self.db_pool)
        .await?;

        // Remove source currency from player
        let from_transaction_id = match self.currency_service.remove_currency(
            player_id,
            from_currency,
            from_amount,
        ).await {
            Ok(_) => {
                // Create transaction record
                let transaction = self.currency_service.create_transaction(
                    Some(player_id),
                    None, // System
                    self.get_currency_id(from_currency).await?,
                    from_amount,
                    Decimal::ZERO,
                    crate::currency_system::TransactionType::Swap,
                    Some(swap.id),
                    Some(format!("Swap from {} to {}", from_currency, to_currency)),
                ).await?;
                
                Some(transaction.id)
            },
            Err(e) => {
                // Rollback and return error
                tx.rollback().await?;
                return Err(e.into());
            }
        };

        // Add target currency to player
        let to_transaction_id = match self.currency_service.add_currency(
            player_id,
            to_currency,
            to_amount,
        ).await {
            Ok(_) => {
                // Create transaction record
                let transaction = self.currency_service.create_transaction(
                    None, // System
                    Some(player_id),
                    self.get_currency_id(to_currency).await?,
                    to_amount,
                    Decimal::ZERO,
                    crate::currency_system::TransactionType::Swap,
                    Some(swap.id),
                    Some(format!("Swap from {} to {}", from_currency, to_currency)),
                ).await?;
                
                Some(transaction.id)
            },
            Err(e) => {
                // Rollback and return error
                tx.rollback().await?;
                return Err(e.into());
            }
        };

        // Update swap record with transaction IDs and status
        let updated_swap = sqlx::query_as!(
            SwapTransaction,
            r#"
            UPDATE game.swap_transactions
            SET 
                status = 'completed',
                completed_at = NOW(),
                from_transaction_id = $2,
                to_transaction_id = $3
            WHERE id = $1
            RETURNING 
                id, player_id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                from_amount, to_amount, fee_amount, rate,
                status as "status: SwapStatus",
                created_at, completed_at,
                from_transaction_id, to_transaction_id
            "#,
            swap.id,
            from_transaction_id,
            to_transaction_id
        )
        .fetch_one(&self.db_pool)
        .await?;

        // Commit transaction
        tx.commit().await?;

        Ok(updated_swap)
    }

    /// Get a swap transaction by ID
    pub async fn get_swap_transaction(&self, id: Uuid) -> Result<SwapTransaction, SwapError> {
        let swap = sqlx::query_as!(
            SwapTransaction,
            r#"
            SELECT 
                id, player_id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                from_amount, to_amount, fee_amount, rate,
                status as "status: SwapStatus",
                created_at, completed_at,
                from_transaction_id, to_transaction_id
            FROM game.swap_transactions
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or(SwapError::SwapNotFound { id })?;

        Ok(swap)
    }

    /// Get swap transactions for a player
    pub async fn get_player_swap_transactions(
        &self,
        player_id: Uuid,
        limit: i64,
        offset: i64,
    ) -> Result<Vec<SwapTransaction>, SwapError> {
        let swaps = sqlx::query_as!(
            SwapTransaction,
            r#"
            SELECT 
                id, player_id, 
                from_currency as "from_currency: CurrencyType",
                to_currency as "to_currency: CurrencyType",
                from_amount, to_amount, fee_amount, rate,
                status as "status: SwapStatus",
                created_at, completed_at,
                from_transaction_id, to_transaction_id
            FROM game.swap_transactions
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

        Ok(swaps)
    }

    /// Get currency ID from currency type
    async fn get_currency_id(&self, currency_type: CurrencyType) -> Result<i32, SwapError> {
        let currency = self.currency_service.get_currency_by_type(currency_type).await?;
        Ok(currency.id)
    }

    /// Update exchange rates based on market conditions
    pub async fn update_market_rates(&self, admin_id: Uuid) -> Result<(), SwapError> {
        // This would typically involve:
        // 1. Fetching current market rates from external sources
        // 2. Applying business logic to determine new rates
        // 3. Updating the rates in the database
        
        // For now, we'll implement a simplified version that adjusts rates
        // based on some basic supply/demand simulation
        
        // Get current supply of each currency
        let solana_currency = self.currency_service.get_currency_by_type(CurrencyType::Solana).await?;
        let exons_currency = self.currency_service.get_currency_by_type(CurrencyType::Exons).await?;
        let crystals_currency = self.currency_service.get_currency_by_type(CurrencyType::Crystals).await?;
        
        // Calculate new rates based on supply
        // This is a simplified model - real implementation would be more complex
        
        // Solana to Exons rate (higher Exons supply = more Exons per Solana)
        let sol_to_exon_rate = Decimal::new(1000, 0) * 
            (Decimal::new(1, 0) + (exons_currency.current_supply / Decimal::new(1000000, 0)));
        
        // Exons to Crystals rate (higher Crystal supply = more Crystals per Exon)
        let exon_to_crystal_rate = Decimal::new(100, 0) * 
            (Decimal::new(1, 0) + (crystals_currency.current_supply / Decimal::new(10000000, 0)));
        
        // Update the rates
        self.update_exchange_rate(
            CurrencyType::Solana,
            CurrencyType::Exons,
            sol_to_exon_rate,
            Decimal::new(1, 2), // 0.01 SOL min
            Decimal::new(100, 0), // 100 SOL max
            Decimal::new(2, 0), // 2% fee
            true,
            admin_id,
        ).await?;
        
        self.update_exchange_rate(
            CurrencyType::Exons,
            CurrencyType::Solana,
            Decimal::new(1, 0) / sol_to_exon_rate,
            Decimal::new(10, 0), // 10 EXON min
            Decimal::new(100000, 0), // 100,000 EXON max
            Decimal::new(2, 0), // 2% fee
            true,
            admin_id,
        ).await?;
        
        self.update_exchange_rate(
            CurrencyType::Exons,
            CurrencyType::Crystals,
            exon_to_crystal_rate,
            Decimal::new(1, 0), // 1 EXON min
            Decimal::new(1000, 0), // 1,000 EXON max
            Decimal::new(13, 0), // 13% fee (tax)
            true,
            admin_id,
        ).await?;
        
        self.update_exchange_rate(
            CurrencyType::Crystals,
            CurrencyType::Exons,
            Decimal::new(1, 0) / exon_to_crystal_rate,
            Decimal::new(100, 0), // 100 CRYSTAL min
            Decimal::new(100000, 0), // 100,000 CRYSTAL max
            Decimal::new(13, 0), // 13% fee (tax)
            true,
            admin_id,
        ).await?;
        
        Ok(())
    }
}

/// Create the exchange_rates table in the database
pub async fn create_exchange_rates_table(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS game.exchange_rates (
            id SERIAL PRIMARY KEY,
            from_currency VARCHAR(20) NOT NULL,
            to_currency VARCHAR(20) NOT NULL,
            rate DECIMAL(20,9) NOT NULL,
            min_amount DECIMAL(20,9) NOT NULL,
            max_amount DECIMAL(20,9) NOT NULL,
            fee_percentage DECIMAL(5,2) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_by UUID REFERENCES auth.players(id),
            CONSTRAINT unique_currency_pair UNIQUE (from_currency, to_currency),
            CONSTRAINT chk_rate_positive CHECK (rate > 0),
            CONSTRAINT chk_min_amount_positive CHECK (min_amount > 0),
            CONSTRAINT chk_max_amount_gt_min CHECK (max_amount > min_amount),
            CONSTRAINT chk_fee_percentage CHECK (fee_percentage >= 0 AND fee_percentage <= 100)
        );
        "#,
    )
    .execute(pool)
    .await?;

    Ok(())
}

/// Create the swap_transactions table in the database
pub async fn create_swap_transactions_table(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS game.swap_transactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            player_id UUID NOT NULL REFERENCES auth.players(id),
            from_currency VARCHAR(20) NOT NULL,
            to_currency VARCHAR(20) NOT NULL,
            from_amount DECIMAL(20,9) NOT NULL,
            to_amount DECIMAL(20,9) NOT NULL,
            fee_amount DECIMAL(20,9) NOT NULL,
            rate DECIMAL(20,9) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP,
            from_transaction_id UUID REFERENCES game.transactions(id),
            to_transaction_id UUID REFERENCES game.transactions(id),
            CONSTRAINT chk_from_amount_positive CHECK (from_amount > 0),
            CONSTRAINT chk_to_amount_positive CHECK (to_amount > 0),
            CONSTRAINT chk_fee_amount_nonnegative CHECK (fee_amount >= 0),
            CONSTRAINT chk_rate_positive CHECK (rate > 0),
            CONSTRAINT chk_status CHECK (
                status IN ('pending', 'completed', 'failed', 'cancelled')
            )
        );
        "#,
    )
    .execute(pool)
    .await?;

    // Create index for faster queries
    sqlx::query(
        r#"
        CREATE INDEX IF NOT EXISTS idx_swap_transactions_player_id ON game.swap_transactions(player_id);
        "#,
    )
    .execute(pool)
    .await?;

    Ok(())
}
