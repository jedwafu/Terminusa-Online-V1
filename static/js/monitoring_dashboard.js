class MonitoringDashboard {
    constructor() {
        this.charts = {};
        this.socket = null;
        this.updateInterval = 30; // seconds
        this.metrics = {};
        this.alerts = [];
        this.darkMode = true;

        // Initialize components
        this.initializeWebSocket();
        this.initializeCharts();
        this.initializeEventListeners();
        this.startUpdates();
    }

    initializeWebSocket() {
        this.socket = new WebSocket('wss://terminusa.online/ws/monitoring');
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.socket.onclose = () => {
            setTimeout(() => this.initializeWebSocket(), 5000);
        };
    }

    initializeCharts() {
        // System Resources Chart
        this.charts.system = new Chart(
            document.getElementById('systemChart').getContext('2d'),
            this.getChartConfig('system', {
                cpu: { label: 'CPU Usage', color: '#4CAF50' },
                memory: { label: 'Memory Usage', color: '#2196F3' },
                disk: { label: 'Disk Usage', color: '#FFC107' }
            })
        );

        // Network Traffic Chart
        this.charts.network = new Chart(
            document.getElementById('networkChart').getContext('2d'),
            this.getChartConfig('network', {
                incoming: { label: 'Incoming Traffic', color: '#4CAF50' },
                outgoing: { label: 'Outgoing Traffic', color: '#F44336' }
            })
        );

        // Database Performance Chart
        this.charts.database = new Chart(
            document.getElementById('databaseChart').getContext('2d'),
            this.getChartConfig('database', {
                queries: { label: 'Active Queries', color: '#2196F3' },
                connections: { label: 'Active Connections', color: '#9C27B0' }
            })
        );

        // Game Metrics Chart
        this.charts.game = new Chart(
            document.getElementById('gameChart').getContext('2d'),
            this.getChartConfig('game', {
                players: { label: 'Active Players', color: '#4CAF50' },
                wars: { label: 'Active Wars', color: '#F44336' },
                transactions: { label: 'Transactions/min', color: '#FFC107' }
            })
        );
    }

    getChartConfig(type, datasets) {
        const config = {
            type: 'line',
            data: {
                labels: [],
                datasets: Object.entries(datasets).map(([key, value]) => ({
                    label: value.label,
                    borderColor: value.color,
                    backgroundColor: this.getGradient(value.color),
                    data: [],
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: this.darkMode ? '#fff' : '#666',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: this.darkMode ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                        titleColor: this.darkMode ? '#fff' : '#000',
                        bodyColor: this.darkMode ? '#aaa' : '#666',
                        borderColor: this.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute'
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: this.darkMode ? '#aaa' : '#666'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: this.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: this.darkMode ? '#aaa' : '#666'
                        }
                    }
                }
            }
        };

        // Add specific configurations based on chart type
        switch (type) {
            case 'system':
                config.options.scales.y.max = 100;
                break;
            case 'network':
                config.options.scales.y.ticks.callback = this.formatBytes;
                break;
            case 'game':
                config.options.scales.y.beginAtZero = true;
                break;
        }

        return config;
    }

    getGradient(color) {
        return {
            backgroundColor: (context) => {
                const chart = context.chart;
                const {ctx, chartArea} = chart;
                if (!chartArea) return null;
                
                const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                gradient.addColorStop(0, this.hexToRGBA(color, 0));
                gradient.addColorStop(1, this.hexToRGBA(color, 0.2));
                return gradient;
            }
        };
    }

    hexToRGBA(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    initializeEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.fetchUpdates();
        });

        // Update interval selector
        document.getElementById('updateInterval').addEventListener('change', (e) => {
            this.updateInterval = parseInt(e.target.value);
            this.restartUpdates();
        });

        // Time range selector
        document.getElementById('timeRange').addEventListener('change', (e) => {
            this.updateTimeRange(e.target.value);
        });

        // Theme toggle
        document.getElementById('themeToggle').addEventListener('change', (e) => {
            this.darkMode = e.target.checked;
            this.updateTheme();
        });

        // Alert filters
        document.getElementById('alertSeverity').addEventListener('change', () => {
            this.filterAlerts();
        });

        // Log filters
        document.getElementById('logLevel').addEventListener('change', () => {
            this.filterLogs();
        });

        // Search functionality
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
    }

    startUpdates() {
        this.fetchUpdates();
        setInterval(() => this.fetchUpdates(), this.updateInterval * 1000);
    }

    async fetchUpdates() {
        try {
            const response = await fetch('/api/monitoring/metrics', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to fetch metrics');
            
            const data = await response.json();
            this.updateDashboard(data.metrics);
            
        } catch (error) {
            console.error('Failed to fetch updates:', error);
            this.showError('Failed to fetch monitoring data');
        }
    }

    updateDashboard(metrics) {
        this.updateCharts(metrics);
        this.updateStatusCards(metrics);
        this.updateServiceStatus(metrics.services);
        this.updateAlerts();
        this.updateLogs();
    }

    updateCharts(metrics) {
        const timestamp = new Date();

        // Update system resources chart
        this.updateChart(this.charts.system, timestamp, {
            cpu: metrics.system.cpu.total,
            memory: metrics.system.memory.percent,
            disk: metrics.system.disk.percent
        });

        // Update network traffic chart
        this.updateChart(this.charts.network, timestamp, {
            incoming: metrics.network.bytes.received / 1024 / 1024,
            outgoing: metrics.network.bytes.sent / 1024 / 1024
        });

        // Update database performance chart
        this.updateChart(this.charts.database, timestamp, {
            queries: metrics.database.performance.active_queries,
            connections: metrics.database.connections.active
        });

        // Update game metrics chart
        this.updateChart(this.charts.game, timestamp, {
            players: metrics.game.players.active,
            wars: metrics.game.wars.active,
            transactions: metrics.game.transactions_per_minute
        });
    }

    updateChart(chart, timestamp, values) {
        const maxDataPoints = 60;

        chart.data.labels.push(timestamp);
        chart.data.datasets.forEach((dataset, index) => {
            const key = Object.keys(values)[index];
            dataset.data.push(values[key]);
        });

        if (chart.data.labels.length > maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        chart.update('none');
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics':
                this.updateDashboard(data.data);
                break;
            case 'alert':
                this.handleNewAlert(data.alert);
                break;
            case 'log':
                this.handleNewLog(data.log);
                break;
        }
    }

    handleNewAlert(alert) {
        this.alerts.unshift(alert);
        this.updateAlerts();
        
        if (alert.severity === 'critical') {
            this.showNotification('Critical Alert', alert.message);
        }
    }

    handleNewLog(log) {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        const logElement = document.createElement('div');
        logElement.className = `log-entry ${log.level}`;
        logElement.innerHTML = this.formatLogEntry(log);
        
        container.insertBefore(logElement, container.firstChild);
        this.trimLogs();
    }

    formatLogEntry(log) {
        return `
            <span class="log-time">${new Date(log.timestamp).toLocaleTimeString()}</span>
            <span class="log-level ${log.level}">${log.level}</span>
            <span class="log-message">${log.message}</span>
        `;
    }

    trimLogs() {
        const container = document.getElementById('logsContainer');
        const maxLogs = 1000;
        
        while (container.children.length > maxLogs) {
            container.removeChild(container.lastChild);
        }
    }

    updateTheme() {
        document.body.classList.toggle('dark-mode', this.darkMode);
        Object.values(this.charts).forEach(chart => {
            chart.options.plugins.legend.labels.color = this.darkMode ? '#fff' : '#666';
            chart.options.scales.x.ticks.color = this.darkMode ? '#aaa' : '#666';
            chart.options.scales.y.ticks.color = this.darkMode ? '#aaa' : '#666';
            chart.options.scales.y.grid.color = this.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
            chart.update();
        });
    }
}

// Initialize dashboard when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.monitoringDashboard = new MonitoringDashboard();
});
