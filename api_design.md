# Terminusa Online API Design

This document outlines the API architecture for Terminusa Online, facilitating communication between game clients, web interfaces, and the blockchain.

## API Architecture Overview

The Terminusa Online API follows a RESTful architecture with WebSocket support for real-time updates. The API will be organized into logical domains and versioned to ensure backward compatibility as the game evolves.

### Technology Stack

- **Framework**: Actix-web (Rust-based web framework)
- **Authentication**: JWT (JSON Web Tokens)
- **Documentation**: OpenAPI/Swagger
- **Real-time Communication**: WebSockets
- **Serialization**: JSON for REST, MessagePack for WebSockets
- **Rate Limiting**: Token bucket algorithm
- **Caching**: Redis

### Base URL Structure

```
https://api.terminusa.online/v1/{resource}
```

## Authentication and Authorization

### Authentication Methods

1. **JWT-based Authentication**
   - Used for web and client applications
   - Tokens expire after 24 hours
   - Refresh tokens with 7-day validity

2. **API Key Authentication**
   - Used for third-party integrations
   - Rate-limited based on tier

3. **Web3 Wallet Authentication**
   - Sign message to verify wallet ownership
   - Link wallet to existing account or create new account

### Authorization Levels

- **Public**: Accessible without authentication
- **Player**: Basic authenticated user access
- **Premium**: Enhanced access for premium players
- **Guild Leader**: Guild management capabilities
- **Admin**: Full administrative access

## API Endpoints

### Player Management

#### Authentication

```
POST /auth/login
POST /auth/register
POST /auth/refresh
POST /auth/logout
POST /auth/wallet-connect
```

#### Player Profile

```
GET /players/me
GET /players/{id}
GET /players/search?name={name}
PATCH /players/me
GET /players/me/stats
PATCH /players/me/stats
GET /players/leaderboard?category={category}&limit={limit}&offset={offset}
```

#### Player Inventory

```
GET /players/me/inventory
GET /players/me/inventory/items/{id}
POST /players/me/inventory/items/{id}/use
POST /players/me/inventory/items/{id}/equip
POST /players/me/inventory/items/{id}/unequip
PATCH /players/me/inventory/items/{id}/rename
```

#### Player Skills

```
GET /players/me/skills
GET /players/me/skills/{id}
POST /players/me/skills/{id}/equip
POST /players/me/skills/{id}/unequip
POST /players/me/skills/{id}/use
```

### Wallet and Transactions

#### Wallet Management

```
GET /wallet
POST /wallet/deposit
POST /wallet/withdraw
GET /wallet/transactions?currency={currency}&limit={limit}&offset={offset}
```

#### Currency Exchange

```
GET /exchange/rates
POST /exchange/swap
GET /exchange/history
```

#### Transactions

```
POST /transactions
GET /transactions/{id}
GET /transactions?type={type}&status={status}&limit={limit}&offset={offset}
```

### Game World

#### Maps and Gates

```
GET /maps
GET /maps/{id}
GET /gates
GET /gates/{id}
GET /gates/{id}/leaderboard
POST /gates/{id}/enter
```

#### Magic Beasts

```
GET /magic-beasts
GET /magic-beasts/{id}
GET /magic-beasts/spawns?map={map_id}
```

#### Combat

```
POST /combat/attack
GET /combat/status
POST /combat/use-skill
POST /combat/use-item
GET /combat/log?instance={instance_id}
```

### Social Systems

#### Guilds

```
GET /guilds
POST /guilds
GET /guilds/{id}
PATCH /guilds/{id}
GET /guilds/{id}/members
POST /guilds/{id}/members
DELETE /guilds/{id}/members/{player_id}
GET /guilds/leaderboard
```

#### Parties

```
GET /parties
POST /parties
GET /parties/{id}
PATCH /parties/{id}
POST /parties/{id}/join
POST /parties/{id}/leave
POST /parties/{id}/invite
GET /parties/{id}/members
```

#### Chat

```
GET /chat/channels
POST /chat/channels/{channel}/messages
GET /chat/channels/{channel}/messages?limit={limit}&before={message_id}
```

### Marketplace

#### Listings

```
GET /marketplace/listings?category={category}&limit={limit}&offset={offset}
POST /marketplace/listings
GET /marketplace/listings/{id}
DELETE /marketplace/listings/{id}
```

#### Transactions

```
POST /marketplace/listings/{id}/buy
POST /marketplace/listings/{id}/bid
GET /marketplace/my-listings
GET /marketplace/my-bids
```

### Game Systems

#### Quests

```
GET /quests
GET /quests/{id}
POST /quests/{id}/accept
POST /quests/{id}/complete
GET /quests/active
```

#### Achievements

```
GET /achievements
GET /achievements/{id}
GET /achievements/progress
```

#### Hunter Association

```
GET /hunter-association/ranks
POST /hunter-association/apply-promotion
GET /hunter-association/promotion-status
```

#### Gacha System

```
GET /gacha/available
POST /gacha/{id}/roll
GET /gacha/history
```

### Admin Operations

```
GET /admin/players
PATCH /admin/players/{id}
GET /admin/transactions
POST /admin/currency/mint
POST /admin/currency/burn
GET /admin/system/logs
PATCH /admin/system/settings
```

## WebSocket API

The WebSocket API provides real-time updates for game state changes.

### Connection

```
wss://api.terminusa.online/ws?token={jwt_token}
```

### Message Types

#### Server to Client

- **player_update**: Player stats, position, or inventory updates
- **combat_update**: Combat events and results
- **chat_message**: New chat messages
- **notification**: System notifications
- **market_update**: Marketplace price changes
- **gate_status**: Gate instance status changes
- **party_update**: Party member status changes

#### Client to Server

- **movement**: Player movement commands
- **action**: Player actions (use item, skill, etc.)
- **chat**: Chat messages
- **heartbeat**: Connection keep-alive

### Message Format

```json
{
  "type": "message_type",
  "timestamp": 1623456789,
  "data": {
    // Message-specific data
  }
}
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created
- **204 No Content**: Successful request with no response body
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details
    }
  }
}
```

## Rate Limiting

Rate limits are applied based on user tier:

- **Anonymous**: 30 requests per minute
- **Basic Player**: 60 requests per minute
- **Premium Player**: 120 requests per minute
- **Admin**: 300 requests per minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1623456789
```

## Pagination

List endpoints support pagination with the following query parameters:

- **limit**: Number of items per page (default: 20, max: 100)
- **offset**: Number of items to skip (default: 0)

Pagination metadata is included in the response:

```json
{
  "data": [...],
  "pagination": {
    "total": 1250,
    "limit": 20,
    "offset": 40,
    "next": "/api/v1/resource?limit=20&offset=60",
    "previous": "/api/v1/resource?limit=20&offset=20"
  }
}
```

## Filtering and Sorting

List endpoints support filtering and sorting:

- **filter[field]**: Filter by field value
- **sort**: Sort by field (prefix with - for descending order)

Example:
```
GET /api/v1/marketplace/listings?filter[category]=weapon&sort=-price
```

## Versioning

The API is versioned to ensure backward compatibility:

- Major version in URL path: `/v1/`
- Minor versions via Accept header: `Accept: application/vnd.terminusa.v1.2+json`

## Caching

Responses include appropriate cache headers:

- **ETag**: Entity tag for conditional requests
- **Cache-Control**: Caching directives
- **Last-Modified**: Last modification timestamp

## Security Considerations

### API Security Measures

1. **Transport Security**
   - HTTPS for all communications
   - HTTP Strict Transport Security (HSTS)
   - TLS 1.2+ required

2. **Input Validation**
   - Strict schema validation for all requests
   - Parameter sanitization
   - Content-Type enforcement

3. **Output Encoding**
   - Proper JSON encoding
   - XSS prevention

4. **Rate Limiting and Throttling**
   - Prevent brute force attacks
   - Mitigate DDoS attempts

5. **Sensitive Data Handling**
   - No sensitive data in URLs
   - Minimal exposure of internal IDs
   - Redaction of sensitive data in logs

6. **CORS Policy**
   - Strict origin restrictions
   - Appropriate headers for web clients

## Blockchain Integration

### Solana Wallet Operations

```
POST /blockchain/solana/verify-wallet
POST /blockchain/solana/transfer
GET /blockchain/solana/transaction/{tx_hash}
```

### Exons Token Operations

```
GET /blockchain/exons/balance
POST /blockchain/exons/transfer
GET /blockchain/exons/transaction/{tx_hash}
```

## Implementation Guidelines

### API Development Workflow

1. Define endpoint specifications
2. Implement endpoint logic
3. Write automated tests
4. Document in OpenAPI
5. Review and security audit
6. Deploy to staging
7. Integration testing
8. Deploy to production

### Monitoring and Analytics

- Request/response timing metrics
- Error rate tracking
- Endpoint usage statistics
- User activity patterns
- Performance bottlenecks

## Documentation

The API is documented using OpenAPI/Swagger:

- Interactive documentation: `https://api.terminusa.online/docs`
- OpenAPI specification: `https://api.terminusa.online/openapi.json`
- SDK generation for common languages

## Client Integration

### Game Client Integration

- Direct API calls for account management
- WebSocket for real-time game state
- Fallback mechanisms for intermittent connectivity

### Web Interface Integration

- RESTful API for all web functionality
- WebSocket for real-time updates
- Progressive enhancement for offline capabilities

## Future Considerations

- GraphQL API for complex data requirements
- Webhook support for third-party integrations
- Expanded WebSocket capabilities
- Enhanced analytics and telemetry
- Mobile-specific optimizations
