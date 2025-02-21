class TerritoryActions {
    constructor() {
        this.currentTerritory = null;
        this.maxAttackForce = 1000;
        this.maxReinforceAmount = 500;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Attack force slider
        const attackForceSlider = document.getElementById('attack-force');
        if (attackForceSlider) {
            attackForceSlider.addEventListener('input', (e) => {
                this.updateAttackPreview(e.target.value);
            });
        }

        // Reinforce amount slider
        const reinforceSlider = document.getElementById('reinforce-amount');
        if (reinforceSlider) {
            reinforceSlider.addEventListener('input', (e) => {
                this.updateReinforcePreview(e.target.value);
            });
        }

        // Form submissions
        const attackForm = document.getElementById('attack-form');
        if (attackForm) {
            attackForm.addEventListener('submit', (e) => this.executeAttack(e));
        }

        const reinforceForm = document.getElementById('reinforce-form');
        if (reinforceForm) {
            reinforceForm.addEventListener('submit', (e) => this.executeReinforce(e));
        }
    }

    showAttackModal(territory) {
        this.currentTerritory = territory;
        const modal = document.getElementById('attack-territory-modal');
        
        // Update territory info
        this.updateTerritoryInfo(modal, territory);
        
        // Reset and initialize attack form
        const attackForce = document.getElementById('attack-force');
        attackForce.value = 100;
        this.updateAttackPreview(100);
        
        // Show modal
        modal.style.display = 'block';
        this.initializeModalDrag(modal);
    }

    showReinforceModal(territory) {
        this.currentTerritory = territory;
        const modal = document.getElementById('reinforce-territory-modal');
        
        // Update territory info
        this.updateTerritoryInfo(modal, territory);
        
        // Reset and initialize reinforce form
        const reinforceAmount = document.getElementById('reinforce-amount');
        reinforceAmount.value = 50;
        this.updateReinforcePreview(50);
        
        // Show modal
        modal.style.display = 'block';
        this.initializeModalDrag(modal);
    }

    updateTerritoryInfo(modal, territory) {
        modal.querySelector('.territory-name').textContent = territory.name;
        modal.querySelector('.territory-status').innerHTML = `
            <span class="status-indicator ${territory.status}"></span>
            ${territory.status}
        `;
        
        // Update stats
        const stats = modal.querySelector('.territory-stats');
        if (stats) {
            stats.innerHTML = this.generateTerritoryStats(territory);
        }
    }

    generateTerritoryStats(territory) {
        return `
            <div class="stat">
                <span class="label">Controller</span>
                <span class="value">${territory.controller_name || 'None'}</span>
            </div>
            <div class="stat">
                <span class="label">Defense Force</span>
                <span class="value">${territory.defense_data.reinforcements}</span>
            </div>
            <div class="stat">
                <span class="label">Defense Bonus</span>
                <span class="value">${(territory.defense_data.base_defense).toFixed(1)}x</span>
            </div>
        `;
    }

    async updateAttackPreview(force) {
        if (!this.currentTerritory) return;

        try {
            const response = await fetch('/api/guild/war/territory/attack-preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: this.currentTerritory.id,
                    attacking_force: parseInt(force)
                })
            });

            const data = await response.json();
            if (data.success) {
                document.getElementById('force-value').textContent = force;
                document.getElementById('success-chance').textContent = 
                    `${(data.success_chance * 100).toFixed(1)}%`;
                document.getElementById('potential-rewards').textContent = 
                    this.formatRewards(data.potential_rewards);
            }
        } catch (error) {
            console.error('Failed to update attack preview:', error);
        }
    }

    async updateReinforcePreview(amount) {
        if (!this.currentTerritory) return;

        const currentDefense = this.currentTerritory.defense_data.reinforcements;
        const defenseBonus = this.currentTerritory.defense_data.base_defense;
        
        document.getElementById('reinforce-value').textContent = amount;
        document.getElementById('new-defense').textContent = 
            (currentDefense + parseInt(amount)).toString();
        document.getElementById('effective-defense').textContent = 
            ((currentDefense + parseInt(amount)) * defenseBonus).toFixed(0);
    }

    async executeAttack(event) {
        event.preventDefault();
        if (!this.currentTerritory) return;

        const form = event.target;
        const attackingForce = parseInt(form.attacking_force.value);

        try {
            form.classList.add('loading');
            const response = await fetch('/api/guild/war/territory/attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: this.currentTerritory.id,
                    attacking_force: attackingForce
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showSuccess(result.message);
                this.closeModal('attack-territory-modal');
                territoryMap.fetchTerritoryUpdates();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Failed to execute attack');
            console.error(error);
        } finally {
            form.classList.remove('loading');
        }
    }

    async executeReinforce(event) {
        event.preventDefault();
        if (!this.currentTerritory) return;

        const form = event.target;
        const reinforcementAmount = parseInt(form.reinforcement_amount.value);

        try {
            form.classList.add('loading');
            const response = await fetch('/api/guild/war/territory/reinforce', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    territory_id: this.currentTerritory.id,
                    reinforcement_amount: reinforcementAmount
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showSuccess(result.message);
                this.closeModal('reinforce-territory-modal');
                territoryMap.fetchTerritoryUpdates();
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            this.showError('Failed to send reinforcements');
            console.error(error);
        } finally {
            form.classList.remove('loading');
        }
    }

    formatRewards(rewards) {
        const parts = [];
        if (rewards.crystals) parts.push(`${rewards.crystals} Crystals`);
        if (rewards.exons) parts.push(`${rewards.exons} Exons`);
        return parts.join(', ');
    }

    showSuccess(message) {
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            this.currentTerritory = null;
        }
    }

    initializeModalDrag(modal) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        const header = modal.querySelector('h2');
        
        if (header) {
            header.onmousedown = dragMouseDown;
        }

        function dragMouseDown(e) {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            modal.style.top = (modal.offsetTop - pos2) + "px";
            modal.style.left = (modal.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
}

// Initialize territory actions when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.territoryActions = new TerritoryActions();
});
