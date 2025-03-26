# Terminusa Online Web Server Configuration

This document outlines the web server configuration for Terminusa Online, focusing on the xterm.js integration for browser-based gameplay.

## Server Infrastructure

### Server Specifications

- **VPS**: AlmaLinux 8.8
- **IP Address**: 46.250.228.210
- **CPU**: 4 vCPUs
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Bandwidth**: 5TB/month

### Domain Configuration

- **Main Website**: https://terminusa.online
- **Game Client**: https://play.terminusa.online
- **Marketplace**: https://marketplace.terminusa.online
- **API Endpoint**: https://api.terminusa.online

## Web Server Stack

### Web Server Architecture

```
                  ┌─────────────┐
                  │   Clients   │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  Cloudflare │ (DDoS protection, CDN)
                  └──────┬──────┘
                         │
                         ▼
┌───────────────────────────────────────────┐
│               Nginx (Reverse Proxy)        │
└───┬─────────────┬────────────┬────────────┘
    │             │            │
    ▼             ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Apache  │  │ Apache  │  │ Apache  │
│ (Main   │  │ (Play   │  │ (Market │
│ Website)│  │ Server) │  │ place)  │
└─────────┘  └────┬────┘  └─────────┘
                  │
                  ▼
             ┌─────────┐
             │ Game    │
             │ Server  │
             └─────────┘
```

### Software Components

- **Nginx**: Front-facing reverse proxy (version 1.20+)
- **Apache**: Web server for each domain (version 2.4+)
- **Node.js**: For xterm.js server (version 18 LTS)
- **Redis**: Session management and caching (version 6.2+)
- **PostgreSQL**: Primary database (version 14+)
- **Certbot**: SSL certificate management

## Nginx Configuration

### Main Configuration

```nginx
# /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data: blob:; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self' wss://play.terminusa.online wss://api.terminusa.online https://api.terminusa.online; object-src 'none'";

    # Gzip settings
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=main_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
    limit_req_zone $binary_remote_addr zone=play_limit:10m rate=5r/s;

    # Include virtual host configs
    include /etc/nginx/conf.d/*.conf;
}
```

### Virtual Host Configurations

#### Main Website (terminusa.online)

```nginx
# /etc/nginx/conf.d/terminusa.online.conf
server {
    listen 80;
    server_name terminusa.online www.terminusa.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name terminusa.online www.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminusa.online/privkey.pem;

    access_log /var/log/nginx/terminusa.online.access.log main;
    error_log /var/log/nginx/terminusa.online.error.log;

    root /var/www/html/terminusa.online;
    index index.html index.htm;

    location / {
        limit_req zone=main_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static assets caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
```

#### Game Client (play.terminusa.online)

```nginx
# /etc/nginx/conf.d/play.terminusa.online.conf
server {
    listen 80;
    server_name play.terminusa.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name play.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/play.terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/play.terminusa.online/privkey.pem;

    access_log /var/log/nginx/play.terminusa.online.access.log main;
    error_log /var/log/nginx/play.terminusa.online.error.log;

    root /var/www/html/play.terminusa.online;
    index index.html;

    # HTTP requests
    location / {
        limit_req zone=play_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket for xterm.js
    location /terminal {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # Client downloads
    location /downloads {
        alias /var/www/html/play.terminusa.online/downloads;
        autoindex off;
        default_type application/octet-stream;
        
        # Allow large file downloads
        client_max_body_size 100M;
        
        # Add appropriate headers for downloads
        if ($request_filename ~* ^.+\.(exe|zip)$) {
            add_header Content-Disposition "attachment";
        }
    }
}
```

#### Marketplace (marketplace.terminusa.online)

```nginx
# /etc/nginx/conf.d/marketplace.terminusa.online.conf
server {
    listen 80;
    server_name marketplace.terminusa.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name marketplace.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/marketplace.terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marketplace.terminusa.online/privkey.pem;

    access_log /var/log/nginx/marketplace.terminusa.online.access.log main;
    error_log /var/log/nginx/marketplace.terminusa.online.error.log;

    root /var/www/html/marketplace.terminusa.online;
    index index.html;

    location / {
        limit_req zone=main_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### API Server (api.terminusa.online)

```nginx
# /etc/nginx/conf.d/api.terminusa.online.conf
server {
    listen 80;
    server_name api.terminusa.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/api.terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.terminusa.online/privkey.pem;

    access_log /var/log/nginx/api.terminusa.online.access.log main;
    error_log /var/log/nginx/api.terminusa.online.error.log;

    # API requests
    location / {
        limit_req zone=api_limit burst=30 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket for real-time updates
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Apache Configuration

### Main Website (terminusa.online)

```apache
# /etc/httpd/conf.d/terminusa.online.conf
<VirtualHost 127.0.0.1:8080>
    ServerName terminusa.online
    ServerAlias www.terminusa.online
    DocumentRoot /var/www/html/terminusa.online

    ErrorLog logs/terminusa.online-error_log
    CustomLog logs/terminusa.online-access_log combined

    <Directory /var/www/html/terminusa.online>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # Enable HTTP/2
    Protocols h2 h2c http/1.1

    # Enable compression
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
    </IfModule>

    # Set security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</VirtualHost>
```

### Game Client (play.terminusa.online)

```apache
# /etc/httpd/conf.d/play.terminusa.online.conf
<VirtualHost 127.0.0.1:8081>
    ServerName play.terminusa.online
    DocumentRoot /var/www/html/play.terminusa.online

    ErrorLog logs/play.terminusa.online-error_log
    CustomLog logs/play.terminusa.online-access_log combined

    <Directory /var/www/html/play.terminusa.online>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # Enable HTTP/2
    Protocols h2 h2c http/1.1

    # Enable compression
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
    </IfModule>

    # Set security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"

    # Configure downloads directory
    <Directory /var/www/html/play.terminusa.online/downloads>
        Options -Indexes
        AllowOverride None
        Require all granted
        
        <FilesMatch "\.(exe|zip)$">
            Header set Content-Disposition "attachment"
        </FilesMatch>
    </Directory>
</VirtualHost>
```

### Marketplace (marketplace.terminusa.online)

```apache
# /etc/httpd/conf.d/marketplace.terminusa.online.conf
<VirtualHost 127.0.0.1:8082>
    ServerName marketplace.terminusa.online
    DocumentRoot /var/www/html/marketplace.terminusa.online

    ErrorLog logs/marketplace.terminusa.online-error_log
    CustomLog logs/marketplace.terminusa.online-access_log combined

    <Directory /var/www/html/marketplace.terminusa.online>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # Enable HTTP/2
    Protocols h2 h2c http/1.1

    # Enable compression
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
    </IfModule>

    # Set security headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</VirtualHost>
```

## xterm.js Integration

### Node.js Server for xterm.js

```javascript
// /var/www/html/play.terminusa.online/server.js
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const jwt = require('jsonwebtoken');
const redis = require('redis');
const { promisify } = require('util');

// Configuration
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const GAME_CLIENT_PATH = process.env.GAME_CLIENT_PATH || '/usr/local/bin/rustyhack_client';
const SESSION_TIMEOUT = 3600; // 1 hour in seconds

// Redis client for session management
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD || ''
});

const getAsync = promisify(redisClient.get).bind(redisClient);
const setAsync = promisify(redisClient.set).bind(redisClient);
const delAsync = promisify(redisClient.del).bind(redisClient);

// Express app setup
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ noServer: true });

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Authentication middleware
const authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1] || req.query.token;
  
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const sessionExists = await getAsync(`session:${decoded.id}`);
    
    if (!sessionExists) {
      return res.status(401).json({ error: 'Session expired' });
    }
    
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// Routes
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.post('/login', async (req, res) => {
  // This would normally validate credentials against your database
  // For now, we'll just create a token
  const { username, password } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }
  
  // Check if user is already logged in
  const existingSession = await getAsync(`user:${username}`);
  if (existingSession) {
    return res.status(409).json({ error: 'User already logged in' });
  }
  
  // Create a session token
  const user = { id: `user-${Date.now()}`, username };
  const token = jwt.sign(user, JWT_SECRET, { expiresIn: '1h' });
  
  // Store session in Redis
  await setAsync(`session:${user.id}`, JSON.stringify(user), 'EX', SESSION_TIMEOUT);
  await setAsync(`user:${username}`, user.id, 'EX', SESSION_TIMEOUT);
  
  res.status(200).json({ token });
});

app.post('/logout', authenticate, async (req, res) => {
  // Remove session from Redis
  await delAsync(`session:${req.user.id}`);
  await delAsync(`user:${req.user.username}`);
  
  res.status(200).json({ message: 'Logged out successfully' });
});

// Terminal endpoint
app.get('/terminal', authenticate, (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'terminal.html'));
});

// WebSocket handling
server.on('upgrade', async (request, socket, head) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  const token = url.searchParams.get('token');
  
  if (!token) {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
    return;
  }
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const sessionExists = await getAsync(`session:${decoded.id}`);
    
    if (!sessionExists) {
      socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
      socket.destroy();
      return;
    }
    
    request.user = decoded;
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  } catch (err) {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n');
    socket.destroy();
  }
});

wss.on('connection', (ws, request) => {
  console.log(`WebSocket connection established for user: ${request.user.username}`);
  
  // Spawn game client process
  const gameProcess = spawn(GAME_CLIENT_PATH, ['--username', request.user.username]);
  
  // Handle data from game client
  gameProcess.stdout.on('data', (data) => {
    ws.send(JSON.stringify({ type: 'output', data: data.toString() }));
  });
  
  gameProcess.stderr.on('data', (data) => {
    ws.send(JSON.stringify({ type: 'error', data: data.toString() }));
  });
  
  gameProcess.on('close', (code) => {
    ws.send(JSON.stringify({ 
      type: 'system', 
      data: `Game client process exited with code ${code}` 
    }));
    ws.close();
  });
  
  // Handle input from WebSocket
  ws.on('message', (message) => {
    try {
      const parsedMessage = JSON.parse(message);
      
      if (parsedMessage.type === 'input') {
        gameProcess.stdin.write(parsedMessage.data + '\n');
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  });
  
  // Handle WebSocket close
  ws.on('close', () => {
    console.log(`WebSocket connection closed for user: ${request.user.username}`);
    gameProcess.kill();
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### xterm.js Client Implementation

```html
<!-- /var/www/html/play.terminusa.online/public/terminal.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminusa Online</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@4.18.0/css/xterm.css">
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        #header {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 10px;
            text-align: center;
            font-family: 'Arial', sans-serif;
        }
        
        #terminal-container {
            flex: 1;
            padding: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        #terminal {
            width: 100%;
            height: 100%;
            max-width: 900px;
            border-radius: 5px;
            overflow: hidden;
        }
        
        #footer {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 5px;
            text-align: center;
            font-size: 12px;
            font-family: 'Arial', sans-serif;
        }
        
        .loading {
            color: white;
            font-family: 'Arial', sans-serif;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            #terminal {
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>Terminusa Online</h1>
    </div>
    
    <div id="terminal-container">
        <div id="terminal"></div>
    </div>
    
    <div id="footer">
        &copy; 2023 Terminusa Online - All Rights Reserved
    </div>

    <script src="https://cdn.jsdelivr.net/npm/xterm@4.18.0/lib/xterm.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.5.0/lib/xterm-addon-fit.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-web-links@0.6.0/lib/xterm-addon-web-links.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Get token from URL or localStorage
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token') || localStorage.getItem('token');
            
            if (!token) {
                window.location.href = '/login.html';
                return;
            }
            
            // Initialize terminal
            const term = new Terminal({
                cursorBlink: true,
                fontSize: 16,
                fontFamily: 'Courier New, monospace',
                theme: {
                    background: '#1e1e1e',
                    foreground: '#f0f0f0',
                    cursor: '#ffffff'
                }
            });
            
            // Add fit addon
            const fitAddon = new FitAddon.FitAddon();
            term.loadAddon(fitAddon);
            
            // Add web links addon
            term.loadAddon(new WebLinksAddon.WebLinksAddon());
            
            // Open terminal
            term.open(document.getElementById('terminal'));
            fitAddon.fit();
            
            // Handle resize
            window.addEventListener('resize', () => {
                fitAddon.fit();
            });
            
            // Connect to WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/terminal?token=${token}`;
            const socket = new WebSocket(wsUrl);
            
            // Show connecting message
            term.write('Connecting to Terminusa Online...\r\n');
            
            socket.onopen = () => {
                term.write('Connected! Starting game client...\r\n\r\n');
                
                // Handle terminal input
                term.onData(data => {
                    socket.send(JSON.stringify({ type: 'input', data }));
                });
            };
            
            socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    
                    switch (message.type) {
                        case 'output':
                            term.write(message.data);
                            break;
                        case 'error':
                            term.write(`\r\n\x1b[31mERROR: ${message.data}\x1b[0m\r\n`);
                            break;
                        case 'system':
                            term.write(`\r\n\x1b[33m${message.data}\x1b[0m\r\n`);
                            break;
                        default:
                            console.warn('Unknown message type:', message.type);
                    }
                } catch (err) {
                    console.error('Error parsing message:', err);
                    term.write(`\r\n\x1b[31mError: Could not parse server message\x1b[0m\r\n`);
                }
            };
            
            socket.onclose = () => {
                term.write('\r\n\x1b[33mConnection closed. Refresh to reconnect.\x1b[0m\r\n');
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                term.write('\r\n\x1b[31mConnection error. Please try again later.\x1b[0m\r\n');
            };
            
            // Handle page unload
            window.addEventListener('beforeunload', () => {
                socket.close();
            });
        });
    </script>
</body>
</html>
```

### Login Page

```html
<!-- /var/www/html/play.terminusa.online/public/login.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Terminusa Online</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            height: 100vh;
            display: flex;
            flex-direction: column;
            font-family: 'Arial', sans-serif;
            color: #f0f0f0;
        }
        
        #header {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 10px;
