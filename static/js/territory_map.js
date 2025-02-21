class TerritoryMap {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 900,
            height: options.height || 600,
            territorySize: options.territorySize || 40,
            updateInterval: options.updateInterval || 5000,
            ...options
        };

        this.territories = new Map();
        this.selectedTerritory = null;
        this.guildId = document.body.dataset.guildId;

        this.initializeMap();
        this.initializeEventListeners();
        this.startUpdateLoop();
    }

    initializeMap() {
        // Create SVG container
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .attr('class', 'territory-map');

        // Add background grid
        this.addGrid();

        // Add territory layer
        this.territoryLayer = this.svg.append('g')
            .attr('class', 'territory-layer');

        // Add connection lines layer
        this.connectionLayer = this.svg.append('g')
            .attr('class', 'connection-layer');

        // Add tooltip
        this.tooltip = d3.select(this.container)
            .append('div')
            .attr('class', 'territory-tooltip')
            .style('opacity', 0);
    }

    addGrid() {
        const gridSize = 50;
        const numRows = Math.ceil(this.options.height / gridSize);
        const numCols = Math.ceil(this.options.width / gridSize);

        // Add vertical lines
        for (let i = 0; i <= numCols; i++) {
            this.svg.append('line')
                .attr('x1', i * gridSize)
                .attr('y1', 0)
                .attr('x2', i * gridSize)
                .attr('y2', this.options.height)
                .attr('class', 'grid-line');
        }

        // Add horizontal lines
        for (let i = 0; i <= numRows; i++) {
            this.svg.append('line')
                .attr('x1', 0)
                .attr('y1', i * gridSize)
                .attr('x2', this.options.width)
                .attr('y2', i * gridSize)
                .attr('class', 'grid-line');
        }
    }

    updateTerritories(territories) {
        const self = this;

        // Update territory data
        territories.forEach(territory => {
            this.territories.set(territory.id, territory);
        });

        // Update connections
        this.updateConnections();

        // Update territory visualizations
        const territoryElements = this.territoryLayer
            .selectAll('.territory')
            .data(territories, d => d.id);

        // Remove old territories
        territoryElements.exit().remove();

        // Add new territories
        const newTerritories = territoryElements.enter()
            .append('g')
            .attr('class', 'territory')
            .attr('data-id', d => d.id);

        // Add territory circles
        newTerritories.append('circle')
            .attr('r', this.options.territorySize / 2)
            .attr('class', d => `territory-circle ${d.status}`);

        // Add territory icons
        newTerritories.append('text')
            .attr('class', 'territory-icon')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .text(d => this.getTerritoryIcon(d.type));

        // Update all territories
        this.territoryLayer.selectAll('.territory')
            .attr('transform', d => `translate(${d.position_x * this.options.width}, ${d.position_y * this.options.height})`)
            .each(function(d) {
                const territory = d3.select(this);
                territory.select('.territory-circle')
                    .attr('class', `territory-circle ${d.status}`);
            })
            .on('mouseover', function(event, d) {
                self.showTooltip(d, event);
            })
            .on('mouseout', () => {
                this.tooltip.style('opacity', 0);
            })
            .on('click', (event, d) => {
                this.selectTerritory(d);
            });
    }

    updateConnections() {
        const connections = this.calculateConnections();
        
        const lines = this.connectionLayer
            .selectAll('.connection')
            .data(connections, d => `${d.source.id}-${d.target.id}`);

        // Remove old connections
        lines.exit().remove();

        // Add new connections
        lines.enter()
            .append('line')
            .attr('class', 'connection')
            .merge(lines)
            .attr('x1', d => d.source.position_x * this.options.width)
            .attr('y1', d => d.source.position_y * this.options.height)
            .attr('x2', d => d.target.position_x * this.options.width)
            .attr('y2', d => d.target.position_y * this.options.height);
    }

    calculateConnections() {
        const connections = [];
        const territories = Array.from(this.territories.values());

        territories.forEach((territory, i) => {
            territories.slice(i + 1).forEach(otherTerritory => {
                const distance = this.calculateDistance(
                    territory.position_x * this.options.width,
                    territory.position_y * this.options.height,
                    otherTerritory.position_x * this.options.width,
                    otherTerritory.position_y * this.options.height
                );

                if (distance < this.options.width * 0.2) {  // Connect if within 20% of map width
                    connections.push({
                        source: territory,
                        target: otherTerritory
                    });
                }
            });
        });

        return connections;
    }

    calculateDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }

    getTerritoryIcon(type) {
        const icons = {
            'gate': '⛩️',
            'resource': '💎',
            'stronghold': '🏰',
            'outpost': '🗼'
        };
        return icons[type] || '❓';
    }

    showTooltip(territory, event) {
        const tooltipContent = `
            <div class="tooltip-header">
                <h4>${territory.name}</h4>
                <span class="territory-type">${territory.type}</span>
            </div>
            <div class="tooltip-body">
                <p>Status: ${territory.status}</p>
                <p>Controller: ${territory.controller_name || 'None'}</p>
                ${this.getTooltipBonuses(territory)}
            </div>
        `;

        this.tooltip
            .html(tooltipContent)
            .style('left', `${event.pageX + 10}px`)
            .style('top', `${event.pageY - 10}px`)
            .style('opacity', 1);
    }

    getTooltipBonuses(territory) {
        if (!territory.bonuses) return '';

        return `
            <div class="tooltip-bonuses">
                <p>Bonuses:</p>
                <ul>
                    ${territory.bonuses.reward_multiplier ? 
                        `<li>Reward Multiplier: ${territory.bonuses.reward_multiplier}x</li>` : ''}
                    ${territory.bonuses.defense_bonus ? 
                        `<li>Defense Bonus: ${territory.bonuses.defense_bonus}x</li>` : ''}
                </ul>
            </div>
        `;
    }

    selectTerritory(territory) {
        if (this.selectedTerritory === territory.id) {
            this.selectedTerritory = null;
            this.hideActionPanel();
        } else {
            this.selectedTerritory = territory.id;
            this.showActionPanel(territory);
        }

        // Update territory highlighting
        this.territoryLayer.selectAll('.territory')
            .classed('selected', d => d.id === this.selectedTerritory);
    }

    showActionPanel(territory) {
        const actionPanel = document.getElementById('territory-actions');
        if (!actionPanel) return;

        const canAttack = territory.status !== 'friendly';
        const canReinforce = territory.status === 'friendly';

        actionPanel.innerHTML = `
            <h3>${territory.name}</h3>
            <div class="action-buttons">
                ${canAttack ? `
                    <button onclick="territoryMap.attackTerritory(${territory.id})" 
                            class="action-btn attack">
                        Attack Territory
                    </button>
                ` : ''}
                ${canReinforce ? `
                    <button onclick="territoryMap.reinforceTerritory(${territory.id})"
                            class="action-btn reinforce">
                        Reinforce Territory
                    </button>
                ` : ''}
            </div>
        `;
        actionPanel.style.display = 'block';
    }

    hideActionPanel() {
        const actionPanel = document.getElementById('territory-actions');
        if (actionPanel) {
            actionPanel.style.display = 'none';
        }
    }

    async attackTerritory(territoryId) {
        try {
            const response = await fetch('/api/guild/war/territory/attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: territoryId,
                    attacking_force: 100  // TODO: Make this configurable
                })
            });

            const result = await response.json();
            if (result.success) {
                showSuccess(result.message);
                this.fetchTerritoryUpdates();
            } else {
                showError(result.message);
            }
        } catch (error) {
            showError('Failed to attack territory');
            console.error(error);
        }
    }

    async reinforceTerritory(territoryId) {
        try {
            const response = await fetch('/api/guild/war/territory/reinforce', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: territoryId,
                    reinforcement_amount: 50  // TODO: Make this configurable
                })
            });

            const result = await response.json();
            if (result.success) {
                showSuccess(result.message);
                this.fetchTerritoryUpdates();
            } else {
                showError(result.message);
            }
        } catch (error) {
            showError('Failed to reinforce territory');
            console.error(error);
        }
    }

    async fetchTerritoryUpdates() {
        try {
            const warId = document.body.dataset.warId;
            const response = await fetch(`/api/guild/war/${warId}/territories`);
            const data = await response.json();
            
            if (data.success) {
                this.updateTerritories(data.territories);
            }
        } catch (error) {
            console.error('Failed to fetch territory updates:', error);
        }
    }

    startUpdateLoop() {
        setInterval(() => this.fetchTerritoryUpdates(), this.options.updateInterval);
    }

    initializeEventListeners() {
        // Listen for WebSocket updates
        socket.on('territory_update', (data) => {
            if (data.war_id === document.body.dataset.warId) {
                this.updateTerritories([data.territory]);
            }
        });
    }
}

// Initialize map when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.territoryMap = new TerritoryMap('territory-map', {
        width: 900,
        height: 600
    });
});
