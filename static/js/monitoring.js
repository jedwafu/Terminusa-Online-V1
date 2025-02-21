class MonitoringDashboard {
    constructor() {
        this.updateInterval = 30; // seconds
        this.charts = {};
        this.updateTimer = null;
        this.socket = null;

        // Initialize components
        this.initializeCharts();
        this.initializeWebSocket();
        this.initializeEventListeners();
        this.startUpdates();
    }

    initializeCharts() {
        // System Resources Chart
        this.charts.resources = new Chart(
            document.getElementById('resourcesChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU Usage',
                            borderColor: '#4CAF50',
                            data: []
                        },
                        {
                            label: 'Memory Usage',
                            borderColor: '#2196F3',
                            data: []
                        },
                        {
                            label: 'Disk Usage',
                            borderColor: '#FFC107',
                            data: []
                        }
                    ]
                },
                options: this.getChartOptions('System Resources (%)')
            }
        );

        // Network Traffic Chart
        this.charts.network = new Chart(
            document.getElementById('networkChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Incoming Traffic',
                            borderColor: '#4CAF50',
                            data: []
                        },
                        {
                            label: 'Outgoing Traffic',
                            borderColor: '#F44336',
                            data: []
                        }
                    ]
                },
                options: this.getChartOptions('Network Traffic (MB/s)')
            }
        );

        // Database Performance Chart
        this.charts.database = new Chart(
            document.getElementById('dbChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Query Response Time',
                            borderColor: '#2196F3',
                            data: []
                        },
                        {
                            label: 'Active Connections',
                            borderColor: '#9C27B0',
                            data: []
                        }
                    ]
                },
                options: this.getChartOptions('Database Performance')
            }
        );

        // Game Metrics Chart
        this.charts.game = new Chart(
            document.getElementById('gameMetricsChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Active Players',
                            borderColor: '#4CAF50',
                            data: []
                        },
                        {
                            label: 'Active Wars',
                            borderColor: '#F44336',
                            data: []
                        },
                        {
                            label: 'Transactions/min',
                            borderColor: '#FFC107',
                            data: []
                        }
                    ]
                },
                options: this.getChartOptions('Game Metrics')
            }
        );
    }

    getChartOptions(yAxisLabel) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#aaa'
                    },
                    title: {
                        display: true,
                        text: yAxisLabel,
                        color: '#aaa'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#aaa'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fff'
                    }
                }
            }
        };
    }

    initializeWebSocket() {
        this.socket = new WebSocket('wss://terminusa.online/ws/monitoring');
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealtimeUpdate(data);
        };

        this.socket.onclose = () => {
            setTimeout(() => this.initializeWebSocket(), 5000);
        };
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

        // Log filters
        document.getElementById('logLevel').addEventListener('change', () => {
            this.filterLogs();
        });

        document.getElementById('logSearch').addEventListener('input', () => {
            this.filterLogs();
        });

        // Alert acknowledgment
        document.getElementById('acknowledgeAlert').addEventListener('click', () => {
            this.acknowledgeSelectedAlert();
        });
    }

    startUpdates() {
        this.fetchUpdates();
        this.updateTimer = setInterval(() => this.fetchUpdates(), this.updateInterval * 1000);
    }

    restartUpdates() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        this.startUpdates();
    }

    async fetchUpdates() {
        try {
            const response = await fetch('/health/detailed', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to fetch updates');
            
            const data = await response.json();
            this.updateDashboard(data);
            
        } catch (error) {
            console.error('Failed to fetch updates:', error);
            this.showError('Failed to fetch monitoring data');
        }
    }

    updateDashboard(data) {
        this.updateStatusCards(data);
        this.updateCharts(data);
        this.updateServices(data.services);
        this.updateAlerts(data.alerts);
        this.updateLogs(data.logs);
    }

    updateStatusCards(data) {
        // Update System Status
        this.updateStatusCard('systemStatus', data.system);
        this.updateStatusCard('databaseStatus', data.database);
        this.updateStatusCard('cacheStatus', data.cache);
        this.updateStatusCard('gameStatus', data.game);
    }

    updateStatusCard(cardId, data) {
        const card = document.getElementById(cardId);
        if (!card) return;

        // Update status indicator
        const indicator = card.querySelector('.status-indicator');
        indicator.className = `status-indicator ${this.getStatusClass(data.status)}`;

        // Update metrics
        Object.entries(data.metrics || {}).forEach(([key, value]) => {
            const metric = card.querySelector(`#${key}`);
            if (metric) {
                metric.textContent = this.formatMetricValue(value);
            }
        });
    }

    updateCharts(data) {
        const timestamp = new Date().toLocaleTimeString();

        // Update System Resources Chart
        this.updateChart(this.charts.resources, timestamp, [
            data.system.cpu.percent,
            data.system.memory.percent,
            data.system.disk.percent
        ]);

        // Update Network Traffic Chart
        this.updateChart(this.charts.network, timestamp, [
            data.system.network.bytes_recv / 1024 / 1024,
            data.system.network.bytes_sent / 1024 / 1024
        ]);

        // Update Database Chart
        this.updateChart(this.charts.database, timestamp, [
            data.database.performance.response_time,
            data.database.connections.active
        ]);

        // Update Game Metrics Chart
        this.updateChart(this.charts.game, timestamp, [
            data.game.active_players,
            data.game.active_wars,
            data.game.transactions_per_minute
        ]);
    }

    updateChart(chart, label, values) {
        const maxDataPoints = 20;

        chart.data.labels.push(label);
        values.forEach((value, index) => {
            chart.data.datasets[index].data.push(value);
        });

        if (chart.data.labels.length > maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        chart.update('none');
    }

    updateServices(services) {
        const grid = document.getElementById('servicesGrid');
        if (!grid) return;

        grid.innerHTML = Object.entries(services)
            .map(([name, status]) => `
                <div class="service-item">
                    <div class="service-status ${this.getStatusClass(status.running)}"></div>
                    <div class="service-name">${name}</div>
                    ${status.alert ? '<div class="service-alert">⚠️</div>' : ''}
                </div>
            `)
            .join('');
    }

    updateAlerts(alerts) {
        const list = document.getElementById('alertsList');
        if (!list) return;

        list.innerHTML = alerts
            .map(alert => `
                <div class="alert-item" data-id="${alert.id}">
                    <span class="alert-severity ${alert.severity}">${alert.severity}</span>
                    <span class="alert-message">${alert.message}</span>
                    <span class="alert-time">${this.formatTime(alert.timestamp)}</span>
                </div>
            `)
            .join('');
    }

    updateLogs(logs) {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        container.innerHTML = logs
            .map(log => `
                <div class="log-entry">
                    <span class="log-level ${log.level}">${log.level}</span>
                    <span class="log-time">${this.formatTime(log.timestamp)}</span>
                    <span class="log-message">${log.message}</span>
                </div>
            `)
            .join('');
    }

    filterLogs() {
        const level = document.getElementById('logLevel').value;
        const search = document.getElementById('logSearch').value.toLowerCase();
        const entries = document.querySelectorAll('.log-entry');

        entries.forEach(entry => {
            const matchesLevel = level === 'all' || entry.querySelector('.log-level').textContent === level;
            const matchesSearch = !search || entry.querySelector('.log-message').textContent.toLowerCase().includes(search);
            entry.style.display = matchesLevel && matchesSearch ? 'block' : 'none';
        });
    }

    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'metrics':
                this.updateDashboard(data.metrics);
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
        const list = document.getElementById('alertsList');
        if (!list) return;

        const alertElement = document.createElement('div');
        alertElement.className = 'alert-item new';
        alertElement.innerHTML = `
            <span class="alert-severity ${alert.severity}">${alert.severity}</span>
            <span class="alert-message">${alert.message}</span>
            <span class="alert-time">${this.formatTime(alert.timestamp)}</span>
        `;

        list.insertBefore(alertElement, list.firstChild);
        setTimeout(() => alertElement.classList.remove('new'), 100);

        if (alert.severity === 'critical') {
            this.showNotification('Critical Alert', alert.message);
        }
    }

    handleNewLog(log) {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        const logElement = document.createElement('div');
        logElement.className = 'log-entry new';
        logElement.innerHTML = `
            <span class="log-level ${log.level}">${log.level}</span>
            <span class="log-time">${this.formatTime(log.timestamp)}</span>
            <span class="log-message">${log.message}</span>
        `;

        container.insertBefore(logElement, container.firstChild);
        setTimeout(() => logElement.classList.remove('new'), 100);
        this.filterLogs();
    }

    acknowledgeSelectedAlert() {
        const selectedAlert = document.querySelector('.alert-item.selected');
        if (!selectedAlert) return;

        const alertId = selectedAlert.dataset.id;
        fetch(`/api/monitoring/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('adminToken')}`
            }
        })
        .then(response => {
            if (response.ok) {
                selectedAlert.remove();
                this.closeAlertModal();
            }
        })
        .catch(error => {
            console.error('Failed to acknowledge alert:', error);
            this.showError('Failed to acknowledge alert');
        });
    }

    showNotification(title, message) {
        if (Notification.permission === 'granted') {
            new Notification(title, { body: message });
        }
    }

    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    formatMetricValue(value) {
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        return value;
    }

    getStatusClass(status) {
        if (status === true || status === 'healthy') return 'healthy';
        if (status === false || status === 'critical') return 'critical';
        return 'warning';
    }
}

// Initialize dashboard when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.monitoringDashboard = new MonitoringDashboard();

    // Request notification permission
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
