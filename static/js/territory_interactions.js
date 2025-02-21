class TerritoryInteractions {
    constructor() {
        this.selectedTerritory = null;
        this.currentForce = 100;
        this.maxForce = 1000;
        this.cooldowns = new Map();
        this.tooltips = new Map();

        // Initialize tooltips
        this.tooltip = this.createTooltip();
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Territory selection
        document.addEventListener('territory-select', (e) => {
            this.handleTerritorySelect(e.detail.territory);
        });

        // Force slider events
        document.getElementById('attack-force')?.addEventListener('input', (e) => {
            this.updateForcePreview(e.target.value, 'attack');
        });

        document.getElementById('reinforce-amount')?.addEventListener('input', (e) => {
            this.updateForcePreview(e.target.value, 'reinforce');
        });

        // Action buttons
        document.querySelectorAll('.territory-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                const territoryId = e.target.dataset.territoryId;
                this.executeAction(action, territoryId);
            });
        });

        // Mouse interaction for territory info
        document.addEventListener('mouseover', (e) => {
            const territory = e.target.closest('.territory');
            if (territory) {
                this.showTerritoryInfo(territory.dataset.id);
            }
        });

        document.addEventListener('mouseout', (e) => {
            const territory = e.target.closest('.territory');
            if (territory) {
                this.hideTerritoryInfo();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.selectedTerritory) {
                switch(e.key) {
                    case 'a':
                        this.quickAction('attack');
                        break;
                    case 'r':
                        this.quickAction('reinforce');
                        break;
                    case 'Escape':
                        this.deselectTerritory();
                        break;
                }
            }
        });

        // Touch events for mobile
        if ('ontouchstart' in window) {
            this.initializeTouchEvents();
        }
    }

    async handleTerritorySelect(territory) {
        if (this.selectedTerritory === territory.id) {
            this.deselectTerritory();
            return;
        }

        this.selectedTerritory = territory.id;
        
        // Get territory status
        const status = await this.getTerritoryStatus(territory.id);
        
        // Update UI
        this.updateActionPanel(territory, status);
        
        // Highlight territory
        if (window.territoryVisualization) {
            window.territoryVisualization.highlightTerritory(territory.id, true);
        }

        // Show territory details
        this.showTerritoryDetails(territory, status);
    }

    async getTerritoryStatus(territoryId) {
        try {
            const response = await fetch(`/api/guild/war/territory/${territoryId}/status`);
            const data = await response.json();
            return data.success ? data.status : null;
        } catch (error) {
            console.error('Failed to get territory status:', error);
            return null;
        }
    }

    updateActionPanel(territory, status) {
        const panel = document.getElementById('territory-actions');
        if (!panel) return;

        const canAttack = this.canAttack(territory, status);
        const canReinforce = this.canReinforce(territory, status);

        panel.innerHTML = `
            <div class="territory-header">
                <h3>${territory.name}</h3>
                <div class="territory-status">
                    <span class="status-indicator ${status}"></span>
                    ${status}
                </div>
            </div>
            <div class="territory-controls">
                ${this.createActionButtons(territory, canAttack, canReinforce)}
                ${this.createForceControls(territory, canAttack, canReinforce)}
            </div>
            ${this.createCooldownIndicator(territory.id)}
        `;

        this.initializeActionPanelControls();
    }

    createActionButtons(territory, canAttack, canReinforce) {
        return `
            <div class="action-buttons">
                <button class="action-btn attack" 
                        onclick="territoryInteractions.executeAction('attack', '${territory.id}')"
                        ${canAttack ? '' : 'disabled'}>
                    <i class="fas fa-crosshairs"></i>
                    Attack
                </button>
                <button class="action-btn reinforce"
                        onclick="territoryInteractions.executeAction('reinforce', '${territory.id}')"
                        ${canReinforce ? '' : 'disabled'}>
                    <i class="fas fa-shield-alt"></i>
                    Reinforce
                </button>
            </div>
        `;
    }

    createForceControls(territory, canAttack, canReinforce) {
        if (!canAttack && !canReinforce) return '';

        const action = canAttack ? 'attack' : 'reinforce';
        const max = action === 'attack' ? this.maxForce : Math.floor(this.maxForce / 2);

        return `
            <div class="force-controls">
                <label for="force-slider">Force Amount</label>
                <div class="force-slider-container">
                    <input type="range" id="force-slider"
                           min="50" max="${max}" step="10" value="${this.currentForce}"
                           oninput="territoryInteractions.updateForcePreview(this.value, '${action}')">
                    <div class="force-preview">
                        <span id="force-value">${this.currentForce}</span> units
                    </div>
                </div>
                <div class="force-presets">
                    <button onclick="territoryInteractions.setForce(${Math.floor(max * 0.25)})">25%</button>
                    <button onclick="territoryInteractions.setForce(${Math.floor(max * 0.5)})">50%</button>
                    <button onclick="territoryInteractions.setForce(${Math.floor(max * 0.75)})">75%</button>
                    <button onclick="territoryInteractions.setForce(${max})">Max</button>
                </div>
            </div>
        `;
    }

    createCooldownIndicator(territoryId) {
        const cooldown = this.cooldowns.get(territoryId);
        if (!cooldown || cooldown < Date.now()) return '';

        const timeLeft = Math.ceil((cooldown - Date.now()) / 1000);
        return `
            <div class="cooldown-indicator">
                <i class="fas fa-clock"></i>
                Action available in ${timeLeft}s
            </div>
        `;
    }

    async executeAction(action, territoryId) {
        if (this.isOnCooldown(territoryId)) {
            showError('Territory is on cooldown');
            return;
        }

        const force = document.getElementById('force-slider')?.value || this.currentForce;

        try {
            const response = await fetch(`/api/guild/war/territory/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: territoryId,
                    force: parseInt(force)
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.handleActionSuccess(action, territoryId, result);
            } else {
                showError(result.message);
            }

        } catch (error) {
            console.error(`Failed to execute ${action}:`, error);
            showError(`Failed to execute ${action}`);
        }
    }

    handleActionSuccess(action, territoryId, result) {
        // Set cooldown
        this.setCooldown(territoryId);
        
        // Update UI
        this.updateAfterAction(action, territoryId, result);
        
        // Show success message
        showSuccess(result.message);
        
        // Add combat effect
        if (window.territoryVisualization) {
            window.territoryVisualization.addCombatEffect(territoryId, action);
        }
    }

    updateAfterAction(action, territoryId, result) {
        // Update territory status
        if (window.territoryVisualization) {
            window.territoryVisualization.updateTerritoryStatus(territoryId, result.new_status);
        }

        // Update action panel
        this.updateActionPanel({id: territoryId}, result.new_status);

        // Update territory details
        this.updateTerritoryDetails(territoryId, result);
    }

    showTerritoryDetails(territory, status) {
        const details = document.getElementById('territory-details');
        if (!details) return;

        details.innerHTML = `
            <div class="territory-info">
                <div class="info-section">
                    <h4>Status</h4>
                    <div class="status-value ${status}">
                        <span class="status-indicator"></span>
                        ${status}
                    </div>
                </div>
                <div class="info-section">
                    <h4>Defense</h4>
                    <div class="defense-value">
                        ${territory.defense_data.reinforcements} units
                        (${territory.defense_data.base_defense}x multiplier)
                    </div>
                </div>
                <div class="info-section">
                    <h4>Recent Activity</h4>
                    <div class="activity-list">
                        ${this.createActivityList(territory.recent_events)}
                    </div>
                </div>
            </div>
        `;
    }

    createActivityList(events) {
        if (!events || events.length === 0) {
            return '<div class="no-activity">No recent activity</div>';
        }

        return events.map(event => `
            <div class="activity-item ${event.type}">
                <span class="activity-time">${this.formatTime(event.timestamp)}</span>
                <span class="activity-details">${this.formatEvent(event)}</span>
            </div>
        `).join('');
    }

    updateForcePreview(value, action) {
        const preview = document.getElementById('force-preview');
        if (!preview) return;

        this.currentForce = parseInt(value);

        if (action === 'attack') {
            const successChance = this.calculateSuccessChance(this.currentForce);
            preview.innerHTML = `
                <div class="preview-stat">
                    <span class="label">Success Chance</span>
                    <span class="value">${(successChance * 100).toFixed(1)}%</span>
                </div>
                <div class="preview-stat">
                    <span class="label">Potential Rewards</span>
                    <span class="value">${this.calculatePotentialRewards(this.currentForce)}</span>
                </div>
            `;
        } else {
            const effectiveDefense = this.calculateEffectiveDefense(this.currentForce);
            preview.innerHTML = `
                <div class="preview-stat">
                    <span class="label">Defense Increase</span>
                    <span class="value">+${this.currentForce}</span>
                </div>
                <div class="preview-stat">
                    <span class="label">Effective Defense</span>
                    <span class="value">${effectiveDefense}</span>
                </div>
            `;
        }
    }

    calculateSuccessChance(force) {
        // Implementation depends on your game mechanics
        return Math.min(0.9, Math.max(0.1, force / 1000));
    }

    calculatePotentialRewards(force) {
        // Implementation depends on your game mechanics
        return `${Math.floor(force * 1.5)} crystals`;
    }

    calculateEffectiveDefense(force) {
        // Implementation depends on your game mechanics
        return Math.floor(force * 1.2);
    }

    setCooldown(territoryId) {
        const cooldownTime = Date.now() + (5 * 60 * 1000); // 5 minutes
        this.cooldowns.set(territoryId, cooldownTime);
        this.updateCooldownDisplay(territoryId);
    }

    isOnCooldown(territoryId) {
        const cooldown = this.cooldowns.get(territoryId);
        return cooldown && cooldown > Date.now();
    }

    updateCooldownDisplay(territoryId) {
        const indicator = document.querySelector('.cooldown-indicator');
        if (!indicator) return;

        const updateCooldown = () => {
            const cooldown = this.cooldowns.get(territoryId);
            if (!cooldown || cooldown < Date.now()) {
                indicator.remove();
                return;
            }

            const timeLeft = Math.ceil((cooldown - Date.now()) / 1000);
            indicator.innerHTML = `
                <i class="fas fa-clock"></i>
                Action available in ${timeLeft}s
            `;

            requestAnimationFrame(updateCooldown);
        };

        updateCooldown();
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }

    formatEvent(event) {
        switch (event.type) {
            case 'attack':
                return `${event.attacker} attacked with ${event.force} units`;
            case 'reinforce':
                return `${event.reinforcer} added ${event.amount} reinforcements`;
            default:
                return event.message || 'Unknown event';
        }
    }

    initializeTouchEvents() {
        let touchStartX = 0;
        let touchStartY = 0;
        let isDragging = false;

        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isDragging = false;
        });

        document.addEventListener('touchmove', (e) => {
            if (Math.abs(e.touches[0].clientX - touchStartX) > 10 ||
                Math.abs(e.touches[0].clientY - touchStartY) > 10) {
                isDragging = true;
            }
        });

        document.addEventListener('touchend', (e) => {
            if (!isDragging) {
                const territory = e.target.closest('.territory');
                if (territory) {
                    this.handleTerritorySelect({
                        id: territory.dataset.id
                    });
                }
            }
        });
    }
}

// Initialize interactions when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.territoryInteractions = new TerritoryInteractions();
});
