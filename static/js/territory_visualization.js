class TerritoryVisualization {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 900,
            height: options.height || 600,
            gridSize: options.gridSize || 50,
            animationDuration: options.animationDuration || 500,
            ...options
        };

        // SVG layers
        this.svg = null;
        this.gridLayer = null;
        this.connectionLayer = null;
        this.territoryLayer = null;
        this.effectLayer = null;

        // Territory data
        this.territories = new Map();
        this.connections = new Map();
        this.selectedTerritory = null;

        // Initialize visualization
        this.initializeVisualization();
        this.setupEventListeners();
    }

    initializeVisualization() {
        // Create SVG container with layers
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .attr('class', 'territory-map');

        // Add gradient definitions
        this.addGradients();

        // Create layers in specific order
        this.gridLayer = this.svg.append('g').attr('class', 'grid-layer');
        this.connectionLayer = this.svg.append('g').attr('class', 'connection-layer');
        this.territoryLayer = this.svg.append('g').attr('class', 'territory-layer');
        this.effectLayer = this.svg.append('g').attr('class', 'effect-layer');

        // Initialize grid
        this.drawGrid();
    }

    addGradients() {
        const defs = this.svg.append('defs');

        // Territory status gradients
        const gradients = {
            neutral: ['#9e9e9e', '#616161'],
            friendly: ['#4CAF50', '#2E7D32'],
            enemy: ['#f44336', '#c62828'],
            contested: ['#ff9800', '#f57c00']
        };

        Object.entries(gradients).forEach(([status, colors]) => {
            const gradient = defs.append('radialGradient')
                .attr('id', `territory-${status}`)
                .attr('cx', '50%')
                .attr('cy', '50%')
                .attr('r', '50%');

            gradient.append('stop')
                .attr('offset', '0%')
                .attr('style', `stop-color: ${colors[0]}; stop-opacity: 0.8`);

            gradient.append('stop')
                .attr('offset', '100%')
                .attr('style', `stop-color: ${colors[1]}; stop-opacity: 0.4`);
        });

        // Connection gradients
        const connectionGradient = defs.append('linearGradient')
            .attr('id', 'connection-line')
            .attr('gradientUnits', 'userSpaceOnUse');

        connectionGradient.append('stop')
            .attr('offset', '0%')
            .attr('style', 'stop-color: rgba(255,255,255,0.2)');

        connectionGradient.append('stop')
            .attr('offset', '50%')
            .attr('style', 'stop-color: rgba(255,255,255,0.1)');

        connectionGradient.append('stop')
            .attr('offset', '100%')
            .attr('style', 'stop-color: rgba(255,255,255,0.2)');
    }

    drawGrid() {
        const { width, height, gridSize } = this.options;
        const numRows = Math.ceil(height / gridSize);
        const numCols = Math.ceil(width / gridSize);

        // Draw vertical lines
        for (let i = 0; i <= numCols; i++) {
            this.gridLayer.append('line')
                .attr('x1', i * gridSize)
                .attr('y1', 0)
                .attr('x2', i * gridSize)
                .attr('y2', height)
                .attr('class', 'grid-line');
        }

        // Draw horizontal lines
        for (let i = 0; i <= numRows; i++) {
            this.gridLayer.append('line')
                .attr('x1', 0)
                .attr('y1', i * gridSize)
                .attr('x2', width)
                .attr('y2', i * gridSize)
                .attr('class', 'grid-line');
        }
    }

    updateTerritories(territories) {
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
        territoryElements.exit()
            .transition()
            .duration(this.options.animationDuration)
            .style('opacity', 0)
            .remove();

        // Add new territories
        const newTerritories = territoryElements.enter()
            .append('g')
            .attr('class', 'territory')
            .attr('data-id', d => d.id)
            .style('opacity', 0);

        // Add territory components
        this.addTerritoryComponents(newTerritories);

        // Update all territories
        this.territoryLayer.selectAll('.territory')
            .transition()
            .duration(this.options.animationDuration)
            .style('opacity', 1)
            .attr('transform', d => `translate(${d.position_x * this.options.width}, ${d.position_y * this.options.height})`);

        // Update territory status and effects
        this.updateTerritoryStatus();
    }

    addTerritoryComponents(territory) {
        // Add base circle
        territory.append('circle')
            .attr('r', 20)
            .attr('class', 'territory-base');

        // Add pulse effect
        territory.append('circle')
            .attr('r', 20)
            .attr('class', 'territory-pulse');

        // Add icon
        territory.append('text')
            .attr('class', 'territory-icon')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .text(d => this.getTerritoryIcon(d.type));

        // Add label
        territory.append('text')
            .attr('class', 'territory-label')
            .attr('text-anchor', 'middle')
            .attr('y', 30)
            .text(d => d.name);
    }

    updateConnections() {
        const connections = this.calculateConnections();
        
        const lines = this.connectionLayer
            .selectAll('.connection')
            .data(connections, d => `${d.source.id}-${d.target.id}`);

        // Remove old connections
        lines.exit()
            .transition()
            .duration(this.options.animationDuration)
            .style('opacity', 0)
            .remove();

        // Add new connections
        const newLines = lines.enter()
            .append('line')
            .attr('class', 'connection')
            .style('opacity', 0);

        // Update all connections
        this.connectionLayer.selectAll('.connection')
            .transition()
            .duration(this.options.animationDuration)
            .style('opacity', 0.5)
            .attr('x1', d => d.source.position_x * this.options.width)
            .attr('y1', d => d.source.position_y * this.options.height)
            .attr('x2', d => d.target.position_x * this.options.width)
            .attr('y2', d => d.target.position_y * this.options.height);
    }

    updateTerritoryStatus() {
        this.territoryLayer.selectAll('.territory')
            .each((d, i, nodes) => {
                const territory = d3.select(nodes[i]);
                
                // Update status classes
                territory.attr('class', `territory ${d.status}`);
                
                // Update pulse animation based on status
                if (d.status === 'contested') {
                    territory.select('.territory-pulse')
                        .style('animation', 'pulse 2s infinite');
                } else {
                    territory.select('.territory-pulse')
                        .style('animation', 'none');
                }
            });
    }

    addCombatEffect(territoryId, type) {
        const territory = this.territories.get(territoryId);
        if (!territory) return;

        const x = territory.position_x * this.options.width;
        const y = territory.position_y * this.options.height;

        const effect = this.effectLayer.append('g')
            .attr('class', `combat-effect ${type}`)
            .attr('transform', `translate(${x},${y})`);

        switch (type) {
            case 'attack':
                this.createAttackEffect(effect);
                break;
            case 'capture':
                this.createCaptureEffect(effect);
                break;
            case 'reinforce':
                this.createReinforceEffect(effect);
                break;
        }

        // Remove effect after animation
        setTimeout(() => {
            effect.transition()
                .duration(500)
                .style('opacity', 0)
                .remove();
        }, 2000);
    }

    createAttackEffect(container) {
        const particles = 12;
        const radius = 30;

        for (let i = 0; i < particles; i++) {
            const angle = (i / particles) * 2 * Math.PI;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            container.append('circle')
                .attr('r', 2)
                .attr('cx', 0)
                .attr('cy', 0)
                .style('fill', '#f44336')
                .transition()
                .duration(1000)
                .attr('cx', x)
                .attr('cy', y)
                .style('opacity', 0);
        }
    }

    createCaptureEffect(container) {
        container.append('circle')
            .attr('r', 20)
            .style('fill', 'none')
            .style('stroke', '#4CAF50')
            .style('stroke-width', 2)
            .transition()
            .duration(1000)
            .attr('r', 40)
            .style('opacity', 0);
    }

    createReinforceEffect(container) {
        const shield = container.append('path')
            .attr('d', 'M0,-20 L10,0 L0,20 L-10,0 Z')
            .style('fill', '#2196F3')
            .style('opacity', 0);

        shield.transition()
            .duration(500)
            .style('opacity', 1)
            .transition()
            .duration(500)
            .style('opacity', 0);
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

    setupEventListeners() {
        this.territoryLayer.selectAll('.territory')
            .on('mouseover', (event, d) => this.handleTerritoryHover(d))
            .on('mouseout', () => this.handleTerritoryUnhover())
            .on('click', (event, d) => this.handleTerritoryClick(d));
    }

    handleTerritoryHover(territory) {
        // Highlight territory and connections
        this.highlightTerritory(territory.id, true);
    }

    handleTerritoryUnhover() {
        // Remove highlights if no territory is selected
        if (!this.selectedTerritory) {
            this.highlightTerritory(null, false);
        }
    }

    handleTerritoryClick(territory) {
        // Toggle territory selection
        if (this.selectedTerritory === territory.id) {
            this.selectedTerritory = null;
            this.highlightTerritory(null, false);
        } else {
            this.selectedTerritory = territory.id;
            this.highlightTerritory(territory.id, true);
        }

        // Emit territory selection event
        if (this.options.onTerritorySelect) {
            this.options.onTerritorySelect(territory);
        }
    }

    highlightTerritory(territoryId, highlight) {
        this.territoryLayer.selectAll('.territory')
            .classed('highlighted', d => highlight && d.id === territoryId)
            .classed('dimmed', d => highlight && d.id !== territoryId);

        this.connectionLayer.selectAll('.connection')
            .classed('highlighted', d => 
                highlight && (d.source.id === territoryId || d.target.id === territoryId)
            )
            .classed('dimmed', d => 
                highlight && (d.source.id !== territoryId && d.target.id !== territoryId)
            );
    }

    calculateConnections() {
        const connections = [];
        const territories = Array.from(this.territories.values());
        const maxDistance = this.options.width * 0.2;

        territories.forEach((territory, i) => {
            territories.slice(i + 1).forEach(otherTerritory => {
                const distance = this.calculateDistance(
                    territory.position_x * this.options.width,
                    territory.position_y * this.options.height,
                    otherTerritory.position_x * this.options.width,
                    otherTerritory.position_y * this.options.height
                );

                if (distance < maxDistance) {
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
}

// Initialize visualization when document is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('territory-map')) {
        window.territoryVisualization = new TerritoryVisualization('territory-map', {
            onTerritorySelect: (territory) => {
                if (window.territoryActions) {
                    window.territoryActions.handleTerritorySelect(territory);
                }
            }
        });
    }
});
