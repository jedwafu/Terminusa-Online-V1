class TerritoryShortcuts {
    constructor() {
        this.shortcuts = {
            // Territory Selection
            'ArrowUp': () => this.moveSelection('up'),
            'ArrowDown': () => this.moveSelection('down'),
            'ArrowLeft': () => this.moveSelection('left'),
            'ArrowRight': () => this.moveSelection('right'),
            'Enter': () => this.confirmSelection(),
            'Escape': () => this.clearSelection(),

            // Territory Actions
            'a': () => this.quickAction('attack'),
            'r': () => this.quickAction('reinforce'),
            'f': () => this.adjustForce(10),
            'd': () => this.adjustForce(-10),
            'q': () => this.setForcePreset(0.25),
            'w': () => this.setForcePreset(0.5),
            'e': () => this.setForcePreset(0.75),
            'm': () => this.setForcePreset(1.0),

            // Map Navigation
            '+': () => this.adjustZoom(0.1),
            '-': () => this.adjustZoom(-0.1),
            'Home': () => this.resetView(),

            // Quick Info
            'Tab': (e) => {
                e.preventDefault();
                this.cycleNextTerritory();
            },
            'i': () => this.toggleTerritoryInfo()
        };

        this.selectedTerritory = null;
        this.territoryGrid = [];
        this.currentZoom = 1.0;
        this.isShiftPressed = false;

        this.initializeShortcuts();
        this.createShortcutOverlay();
    }

    initializeShortcuts() {
        // Handle key combinations
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // Track shift key state
            if (e.key === 'Shift') {
                this.isShiftPressed = true;
                return;
            }

            // Handle shortcut
            const shortcut = this.shortcuts[e.key];
            if (shortcut) {
                shortcut(e);
                e.preventDefault();
            }
        });

        document.addEventListener('keyup', (e) => {
            if (e.key === 'Shift') {
                this.isShiftPressed = false;
            }
        });

        // Handle shortcut help
        document.addEventListener('keydown', (e) => {
            if (e.key === '?' || (e.key === 'h' && e.ctrlKey)) {
                e.preventDefault();
                this.toggleShortcutHelp();
            }
        });
    }

    moveSelection(direction) {
        if (!this.selectedTerritory) {
            // Select nearest territory to center if none selected
            this.selectNearestTerritory(direction);
            return;
        }

        const territories = this.getTerritoryGrid();
        const current = territories.find(t => t.id === this.selectedTerritory);
        if (!current) return;

        let target;
        switch (direction) {
            case 'up':
                target = this.findNearestTerritory(current, t => t.y < current.y);
                break;
            case 'down':
                target = this.findNearestTerritory(current, t => t.y > current.y);
                break;
            case 'left':
                target = this.findNearestTerritory(current, t => t.x < current.x);
                break;
            case 'right':
                target = this.findNearestTerritory(current, t => t.x > current.x);
                break;
        }

        if (target) {
            this.selectTerritory(target.id);
        }
    }

    findNearestTerritory(current, filterFn) {
        const territories = this.getTerritoryGrid()
            .filter(filterFn)
            .sort((a, b) => {
                const distA = this.calculateDistance(current, a);
                const distB = this.calculateDistance(current, b);
                return distA - distB;
            });

        return territories[0];
    }

    calculateDistance(t1, t2) {
        return Math.sqrt(
            Math.pow(t2.x - t1.x, 2) + 
            Math.pow(t2.y - t1.y, 2)
        );
    }

    selectNearestTerritory() {
        const territories = this.getTerritoryGrid();
        if (territories.length === 0) return;

        const center = {
            x: window.innerWidth / 2,
            y: window.innerHeight / 2
        };

        const nearest = territories.sort((a, b) => {
            const distA = this.calculateDistance(center, a);
            const distB = this.calculateDistance(center, b);
            return distA - distB;
        })[0];

        this.selectTerritory(nearest.id);
    }

    selectTerritory(id) {
        if (window.territoryInteractions) {
            window.territoryInteractions.handleTerritorySelect({id});
        }
        this.selectedTerritory = id;
    }

    confirmSelection() {
        if (!this.selectedTerritory) return;

        if (this.isShiftPressed) {
            this.quickAction('attack');
        } else {
            this.quickAction('reinforce');
        }
    }

    clearSelection() {
        if (window.territoryInteractions) {
            window.territoryInteractions.deselectTerritory();
        }
        this.selectedTerritory = null;
    }

    quickAction(action) {
        if (!this.selectedTerritory) return;

        if (window.territoryInteractions) {
            window.territoryInteractions.executeAction(
                action,
                this.selectedTerritory
            );
        }
    }

    adjustForce(amount) {
        const slider = document.getElementById('force-slider');
        if (!slider) return;

        const newValue = Math.min(
            Math.max(
                parseInt(slider.value) + amount,
                parseInt(slider.min)
            ),
            parseInt(slider.max)
        );

        slider.value = newValue;
        slider.dispatchEvent(new Event('input'));
    }

    setForcePreset(percentage) {
        const slider = document.getElementById('force-slider');
        if (!slider) return;

        const newValue = Math.floor(
            parseInt(slider.min) +
            (parseInt(slider.max) - parseInt(slider.min)) * percentage
        );

        slider.value = newValue;
        slider.dispatchEvent(new Event('input'));
    }

    adjustZoom(delta) {
        this.currentZoom = Math.min(
            Math.max(0.5, this.currentZoom + delta),
            2.0
        );

        if (window.territoryVisualization) {
            window.territoryVisualization.setZoom(this.currentZoom);
        }
    }

    resetView() {
        this.currentZoom = 1.0;
        if (window.territoryVisualization) {
            window.territoryVisualization.resetView();
        }
    }

    cycleNextTerritory() {
        const territories = this.getTerritoryGrid();
        if (territories.length === 0) return;

        const currentIndex = territories.findIndex(t => t.id === this.selectedTerritory);
        const nextIndex = (currentIndex + 1) % territories.length;
        this.selectTerritory(territories[nextIndex].id);
    }

    toggleTerritoryInfo() {
        if (!this.selectedTerritory) return;

        const infoPanel = document.getElementById('territory-info');
        if (infoPanel) {
            infoPanel.classList.toggle('expanded');
        }
    }

    createShortcutOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'shortcut-overlay';
        overlay.style.display = 'none';
        
        overlay.innerHTML = `
            <div class="shortcut-content">
                <h2>Keyboard Shortcuts</h2>
                <div class="shortcut-section">
                    <h3>Navigation</h3>
                    <div class="shortcut-grid">
                        <div class="shortcut-item">
                            <kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd>
                            <span>Navigate territories</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Tab</kbd>
                            <span>Cycle through territories</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Esc</kbd>
                            <span>Clear selection</span>
                        </div>
                    </div>
                </div>
                <div class="shortcut-section">
                    <h3>Actions</h3>
                    <div class="shortcut-grid">
                        <div class="shortcut-item">
                            <kbd>A</kbd>
                            <span>Quick attack</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>R</kbd>
                            <span>Quick reinforce</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>F</kbd>/<kbd>D</kbd>
                            <span>Adjust force ±10</span>
                        </div>
                    </div>
                </div>
                <div class="shortcut-section">
                    <h3>Force Presets</h3>
                    <div class="shortcut-grid">
                        <div class="shortcut-item">
                            <kbd>Q</kbd><kbd>W</kbd><kbd>E</kbd><kbd>M</kbd>
                            <span>25% / 50% / 75% / Max</span>
                        </div>
                    </div>
                </div>
                <div class="shortcut-section">
                    <h3>View</h3>
                    <div class="shortcut-grid">
                        <div class="shortcut-item">
                            <kbd>+</kbd>/<kbd>-</kbd>
                            <span>Zoom in/out</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Home</kbd>
                            <span>Reset view</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>I</kbd>
                            <span>Toggle info panel</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
    }

    toggleShortcutHelp() {
        const overlay = document.querySelector('.shortcut-overlay');
        if (overlay) {
            overlay.style.display = overlay.style.display === 'none' ? 'flex' : 'none';
        }
    }

    getTerritoryGrid() {
        // Cache territory positions for performance
        if (this.territoryGrid.length === 0) {
            const territories = document.querySelectorAll('.territory');
            this.territoryGrid = Array.from(territories).map(t => {
                const rect = t.getBoundingClientRect();
                return {
                    id: t.dataset.id,
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                };
            });
        }
        return this.territoryGrid;
    }
}

// Initialize shortcuts when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.territoryShortcuts = new TerritoryShortcuts();
});
