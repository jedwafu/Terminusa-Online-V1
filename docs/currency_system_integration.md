# Currency System Integration Plan

## Overview
This document outlines the steps to integrate the currency systems of `Terminusa Online`, `terminusaRR`, and `terminusaJet` to support Solana, Exons, and Crystals across all three games.

---

## 1. Unified Currency System

### 1.1 Currency Types
- **Solana**: Blockchain-based cryptocurrency for real-world value transactions.
- **Exons**: Solana blockchain-based governance token.
- **Crystals**: Off-chain in-game currency (soon to be tokenized as first utility token of the game).


### 1.2 Token Swapper System
- Enable swaps between Solana and Exons (and vice-versa) in the token swapper system.
- Add a teaser for future Crystal swaps (Crystals ↔ Exons).
- Add tax calculations for all swaps and transactions.


---

## 2. Database Adjustments

### 2.1 New Tables
- **user_wallets**: Stores Solana addresses and balances for all currencies.
- **currency_transactions**: Tracks all currency transactions, including taxes.
- **token_swaps**: Handles token swaps between Solana, Exons, and Crystals.

### 2.2 Example SQL for New Tables
```sql
-- Web3 Wallet Table
CREATE TABLE user_wallets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    solana_address VARCHAR(64),
    solana_balance DECIMAL(20,8),
    exons_balance DECIMAL(20,8),
    crystals_balance DECIMAL(20,8),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Currency Transactions Table
CREATE TABLE currency_transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    transaction_type VARCHAR(32),
    currency_type VARCHAR(16),
    amount DECIMAL(20,8),
    tax_amount DECIMAL(20,8),
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Token Swaps Table
CREATE TABLE token_swaps (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    from_currency VARCHAR(16),
    to_currency VARCHAR(16),
    from_amount DECIMAL(20,8),
    to_amount DECIMAL(20,8),
    tax_amount DECIMAL(20,8),
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 3. API Integration

### 3.1 Wallet Management API
- **GET /wallets**: Retrieve wallet balances.
- **POST /wallets/deposit**: Deposit Solana, Exons, or Crystals.
- **POST /wallets/withdraw**: Withdraw Solana, Exons, or Crystals.

### 3.2 Token Swapper API
- **POST /swaps**: Perform token swaps between currencies.
- **GET /swaps/history**: Retrieve swap history for a user.

---

## 4. Testing and Validation

### 4.1 Unit Tests
- Test wallet management and token swap functionality.
- Validate tax calculations for transactions.

### 4.2 Integration Tests
- Test interactions between the currency system and other game systems.
- Validate cross-game currency compatibility.

---

## 5. Deployment

### 5.1 Environment Setup
- Set up Solana blockchain integration.
- Configure API endpoints for wallet and swap operations.

### 5.2 Deployment Process
- Deploy the currency system to the production server.
- Monitor system performance and transaction accuracy.

---

## 6. Documentation

### 6.1 API Documentation
- Generate API documentation using tools like Swagger.
- Include examples for all endpoints.

### 6.2 User Documentation
- Create a guide for managing wallets and performing swaps.
- Include FAQs and troubleshooting tips.

---

## Next Steps
1. Review and approve this integration plan.
2. Implement the database changes and APIs.
3. Test and validate the currency system.
4. Deploy to production and monitor performance.
