# Terminusa Online Monitoring API Reference

## Overview

Base URL: `https://terminusa.online/api/monitoring`
API Version: `v1`
Content-Type: `application/json`

## Authentication

```http
Authorization: Bearer <admin_token>
X-API-Key: <api_key>
```

## Endpoints

### System Metrics

#### Get Current Metrics
```http
GET /metrics/current
```

Response:
```json
{
    "success": true,
    "timestamp": "2024-01-20T12:00:00Z",
    "metrics": {
        "system": {
            "cpu": {
                "percent": 45.2,
                "cores": [40.1, 50.3, 45.2, 45.2]
            },
            "memory": {
                "total": 16777216,
                "used": 8388608,
                "percent": 50.0
            },
            "disk": {
                "total": 1099511627776,
                "used": 549755813888,
                "percent": 50.0
            }
        }
    }
}
```

#### Get Historical Metrics
```http
GET /metrics/history
```

Parameters:
- `start`: Start timestamp (ISO 8601)
- `end`: End timestamp (ISO 8601)
- `interval`: Aggregation interval (1m, 5m, 1h)

Response:
```json
{
    "success": true,
    "metrics": [
        {
            "timestamp": "2024-01-20T11:00:00Z",
            "data": {
                "cpu": 45.2,
                "memory": 50.0,
                "disk": 50.0
            }
        }
    ]
}
```

### Alerts

#### Get Active Alerts
```http
GET /alerts/active
```

Response:
```json
{
    "success": true,
    "alerts": [
        {
            "id": "alert_20240120120000",
            "severity": "critical",
            "title": "High CPU Usage",
            "message": "CPU usage above 80%",
            "timestamp": "2024-01-20T12:00:00Z"
        }
    ]
}
```

#### Acknowledge Alert
```http
POST /alerts/{alert_id}/acknowledge
```

Request:
```json
{
    "acknowledged_by": "admin",
    "comment": "Investigating high CPU usage"
}
```

Response:
```json
{
    "success": true,
    "message": "Alert acknowledged"
}
```

### System Health

#### Get Health Status
```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "components": {
        "database": "healthy",
        "cache": "healthy",
        "websocket": "healthy"
    },
    "timestamp": "2024-01-20T12:00:00Z"
}
```

#### Get Detailed Health
```http
GET /health/detailed
```

Response:
```json
{
    "status": "healthy",
    "components": {
        "database": {
            "status": "healthy",
            "connections": 50,
            "latency": 5
        },
        "cache": {
            "status": "healthy",
            "memory_used": "500MB",
            "hit_ratio": 0.95
        }
    }
}
```

### Configuration

#### Get Current Config
```http
GET /config
```

Response:
```json
{
    "success": true,
    "config": {
        "metrics": {
            "collection_interval": 60,
            "retention_period": 86400
        },
        "alerts": {
            "enabled": true,
            "channels": ["email", "slack"]
        }
    }
}
```

#### Update Config
```http
PUT /config
```

Request:
```json
{
    "metrics": {
        "collection_interval": 30
    },
    "alerts": {
        "channels": ["email", "slack", "webhook"]
    }
}
```

Response:
```json
{
    "success": true,
    "message": "Configuration updated"
}
```

### Backup Management

#### Create Backup
```http
POST /backups
```

Request:
```json
{
    "type": "full",
    "compress": true
}
```

Response:
```json
{
    "success": true,
    "backup_id": "backup_20240120120000",
    "path": "/var/backups/monitoring_20240120120000.tar.gz"
}
```

#### List Backups
```http
GET /backups
```

Response:
```json
{
    "success": true,
    "backups": [
        {
            "id": "backup_20240120120000",
            "type": "full",
            "size": 1048576,
            "created_at": "2024-01-20T12:00:00Z"
        }
    ]
}
```

### Performance Management

#### Get Performance Metrics
```http
GET /performance
```

Response:
```json
{
    "success": true,
    "metrics": {
        "response_time": {
            "avg": 50,
            "p95": 100,
            "p99": 200
        },
        "throughput": {
            "requests": 1000,
            "data_processed": "1GB"
        }
    }
}
```

#### Optimize Performance
```http
POST /performance/optimize
```

Request:
```json
{
    "target": "database",
    "action": "vacuum"
}
```

Response:
```json
{
    "success": true,
    "message": "Optimization completed"
}
```

### WebSocket API

#### Connect
```javascript
const ws = new WebSocket('wss://terminusa.online/ws/monitoring');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

#### Message Types

1. Metric Updates
```json
{
    "type": "metrics",
    "data": {
        "cpu": 45.2,
        "memory": 50.0,
        "disk": 50.0
    }
}
```

2. Alert Notifications
```json
{
    "type": "alert",
    "data": {
        "id": "alert_20240120120000",
        "severity": "critical",
        "message": "High CPU usage"
    }
}
```

## Error Handling

### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description"
    }
}
```

### Common Error Codes
- `AUTH_ERROR`: Authentication failed
- `INVALID_REQUEST`: Invalid request parameters
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `SERVER_ERROR`: Internal server error

## Rate Limiting

Headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705756800
```

## Pagination

Parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 100, max: 1000)

Response:
```json
{
    "success": true,
    "data": [...],
    "pagination": {
        "total": 1500,
        "pages": 15,
        "current": 1,
        "per_page": 100
    }
}
```

## Filtering

Parameters:
- `filter[field]`: Field value to filter by
- `filter[operator]`: Comparison operator (eq, gt, lt, etc.)
- `filter[value]`: Value to compare against

Example:
```http
GET /metrics/history?filter[cpu]=gt:80&filter[timestamp]=gt:2024-01-20T00:00:00Z
```

## Sorting

Parameters:
- `sort`: Field to sort by (prefix with - for descending)

Example:
```http
GET /alerts?sort=-timestamp
```

## Support

- Documentation: https://terminusa.online/docs/monitoring
- Email: api@terminusa.online
- Status: https://status.terminusa.online
