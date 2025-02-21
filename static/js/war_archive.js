class WarArchive {
    constructor() {
        this.currentFilters = {
            timePeriod: 'all',
            opponent: 'all',
            result: 'all'
        };
        this.currentPage = 1;
        this.warDetailsCache = new Map();
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Filter change handlers
        document.getElementById('time-period')?.addEventListener('change', (e) => {
            this.currentFilters.timePeriod = e.target.value;
            this.currentPage = 1;
            this.updateArchive();
        });

        document.getElementById('opponent')?.addEventListener('change', (e) => {
            this.currentFilters.opponent = e.target.value;
            this.currentPage = 1;
            this.updateArchive();
        });

        document.getElementById('result')?.addEventListener('change', (e) => {
            this.currentFilters.result = e.target.value;
            this.currentPage = 1;
            this.updateArchive();
        });

        // Pagination handlers
        document.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page !== this.currentPage) {
                    this.currentPage = page;
                    this.updateArchive();
                }
            });
        });
    }

    async updateArchive() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                time_period: this.currentFilters.timePeriod,
                opponent: this.currentFilters.opponent,
                result: this.currentFilters.result
            });

            const response = await fetch(`/api/guild/war-history?${params}`);
            const data = await response.json();

            if (data.success) {
                this.updateWarList(data.wars);
                this.updatePagination(data.page, data.total_pages);
                this.updateStats(data.stats);
            } else {
                showError(data.message);
            }

        } catch (error) {
            console.error('Failed to update archive:', error);
            showError('Failed to update war archive');
        }
    }

    updateWarList(wars) {
        const warList = document.querySelector('.war-list');
        if (!warList) return;

        warList.innerHTML = wars.map(war => this.createWarCard(war)).join('');
    }

    createWarCard(war) {
        const isVictory = war.winner_id === guildId;
        return `
            <div class="war-card" onclick="warArchive.showWarDetails('${war.id}')">
                <div class="war-header">
                    <div class="war-guilds">
                        <div class="guild challenger ${war.challenger_id === guildId ? 'friendly' : 'enemy'}">
                            <img src="/static/images/guilds/${war.challenger_emblem}" alt="${war.challenger_name}">
                            <span>${war.challenger_name}</span>
                        </div>
                        <div class="vs">VS</div>
                        <div class="guild defender ${war.target_id === guildId ? 'friendly' : 'enemy'}">
                            <img src="/static/images/guilds/${war.target_emblem}" alt="${war.target_name}">
                            <span>${war.target_name}</span>
                        </div>
                    </div>
                    <div class="war-result ${isVictory ? 'victory' : 'defeat'}">
                        ${isVictory ? 'Victory' : 'Defeat'}
                    </div>
                </div>
                <div class="war-details">
                    <div class="war-score">
                        <span class="score">${war.scores[guildId]}</span>
                        <span class="separator">-</span>
                        <span class="score">${war.scores[war.opponent_id]}</span>
                    </div>
                    <div class="war-date">
                        ${this.formatDate(war.end_time)}
                    </div>
                </div>
                <div class="war-stats">
                    ${this.createWarStats(war)}
                </div>
            </div>
        `;
    }

    createWarStats(war) {
        return `
            <div class="stat">
                <span class="label">Territories Controlled</span>
                <span class="value">${war.statistics.territory_control[guildId]}/${war.statistics.total_territories}</span>
            </div>
            <div class="stat">
                <span class="label">Participants</span>
                <span class="value">${war.statistics.total_participants}</span>
            </div>
            <div class="stat">
                <span class="label">Duration</span>
                <span class="value">${this.formatDuration(war.statistics.duration)}</span>
            </div>
        `;
    }

    async showWarDetails(warId) {
        try {
            let warDetails;
            if (this.warDetailsCache.has(warId)) {
                warDetails = this.warDetailsCache.get(warId);
            } else {
                const response = await fetch(`/api/war/archive/${warId}`);
                const data = await response.json();
                if (!data.success) throw new Error(data.message);
                warDetails = data.archive;
                this.warDetailsCache.set(warId, warDetails);
            }

            const modal = document.getElementById('war-details-modal');
            const content = document.getElementById('war-details-content');
            
            content.innerHTML = this.createWarDetailsContent(warDetails);
            modal.style.display = 'block';

            // Initialize any charts or interactive elements
            this.initializeWarDetailsCharts(warDetails);

        } catch (error) {
            console.error('Failed to load war details:', error);
            showError('Failed to load war details');
        }
    }

    createWarDetailsContent(war) {
        return `
            <div class="war-timeline">
                ${this.createWarTimeline(war)}
            </div>
            <div class="war-statistics">
                ${this.createWarStatistics(war)}
            </div>
            <div class="participant-list">
                ${this.createParticipantList(war)}
            </div>
            <div class="territory-history">
                ${this.createTerritoryHistory(war)}
            </div>
        `;
    }

    createWarTimeline(war) {
        const events = war.events.sort((a, b) => 
            new Date(a.created_at) - new Date(b.created_at)
        );

        return `
            <h3>War Timeline</h3>
            <div class="timeline">
                ${events.map(event => `
                    <div class="timeline-item">
                        <div class="time">${this.formatTime(event.created_at)}</div>
                        <div class="event ${event.type}">
                            ${this.formatEvent(event)}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createWarStatistics(war) {
        return `
            <h3>War Statistics</h3>
            <div class="statistics-grid">
                <div class="stat-group">
                    <h4>Combat Stats</h4>
                    <div class="stat">Territories Captured: ${war.statistics.territories_captured}</div>
                    <div class="stat">Total Kills: ${war.statistics.total_kills}</div>
                    <div class="stat">Total Deaths: ${war.statistics.total_deaths}</div>
                </div>
                <div class="stat-group">
                    <h4>Resource Stats</h4>
                    <div class="stat">Crystals Earned: ${war.statistics.crystals_earned}</div>
                    <div class="stat">Exons Earned: ${war.statistics.exons_earned}</div>
                </div>
            </div>
        `;
    }

    createParticipantList(war) {
        const participants = Object.entries(war.participants)
            .sort((a, b) => b[1].points_contributed - a[1].points_contributed);

        return `
            <h3>Top Contributors</h3>
            <div class="participant-grid">
                ${participants.map(([userId, data]) => `
                    <div class="participant">
                        <div class="participant-info">
                            <span class="name">${data.username}</span>
                            <span class="contribution">${data.points_contributed} points</span>
                        </div>
                        <div class="participant-stats">
                            <span>Kills: ${data.kills}</span>
                            <span>Territories: ${data.territories_captured}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createTerritoryHistory(war) {
        return `
            <h3>Territory Control History</h3>
            <div class="territory-timeline" id="territory-timeline-${war.id}"></div>
        `;
    }

    initializeWarDetailsCharts(war) {
        // Initialize territory timeline chart
        this.initializeTerritoryChart(war);
    }

    initializeTerritoryChart(war) {
        const chartId = `territory-timeline-${war.id}`;
        const chartElement = document.getElementById(chartId);
        if (!chartElement) return;

        // Create territory control timeline chart using Chart.js
        new Chart(chartElement, {
            type: 'line',
            data: this.prepareTerritoryData(war),
            options: this.getTerritoryChartOptions()
        });
    }

    prepareTerritoryData(war) {
        // Process war events to create territory control timeline data
        // Implementation depends on your data structure
        return {};
    }

    getTerritoryChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            // Add more chart options as needed
        };
    }

    updatePagination(currentPage, totalPages) {
        const pagination = document.querySelector('.pagination');
        if (!pagination) return;

        pagination.innerHTML = this.createPaginationHTML(currentPage, totalPages);
    }

    createPaginationHTML(currentPage, totalPages) {
        return `
            ${currentPage > 1 ? `
                <a href="#" class="page-btn prev" data-page="${currentPage - 1}">Previous</a>
            ` : ''}
            
            <span class="page-info">Page ${currentPage} of ${totalPages}</span>
            
            ${currentPage < totalPages ? `
                <a href="#" class="page-btn next" data-page="${currentPage + 1}">Next</a>
            ` : ''}
        `;
    }

    updateStats(stats) {
        Object.entries(stats).forEach(([key, value]) => {
            const element = document.querySelector(`.stat.${key} .value`);
            if (element) {
                element.textContent = this.formatStatValue(key, value);
            }
        });
    }

    formatStatValue(key, value) {
        switch (key) {
            case 'win_rate':
                return value.toFixed(1) + '%';
            default:
                return value.toString();
        }
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    formatTime(dateString) {
        return new Date(dateString).toLocaleTimeString();
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }

    formatEvent(event) {
        switch (event.type) {
            case 'territory_capture':
                return `${event.details.capturer_name} captured ${event.details.territory_name}`;
            case 'territory_attack':
                return `${event.details.attacker_name} attacked ${event.details.territory_name}`;
            default:
                return event.details.message || 'Unknown event';
        }
    }

    async downloadWarArchive(warId) {
        try {
            const response = await fetch(`/api/war/archive/${warId}/download`);
            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `war_${warId}_archive.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (error) {
            console.error('Failed to download archive:', error);
            showError('Failed to download war archive');
        }
    }
}

// Initialize war archive when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.warArchive = new WarArchive();
});
