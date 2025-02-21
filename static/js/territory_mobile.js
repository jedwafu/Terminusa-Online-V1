class TerritoryMobile {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.lastTap = 0;
        this.pinchStartDistance = 0;
        this.initialZoom = 1;
        this.isGesturing = false;
        this.selectedTerritory = null;
        this.gestureTimeout = null;

        // Mobile-specific settings
        this.settings = {
            doubleTapDelay: 300,
            longPressDelay: 500,
            minSwipeDistance: 30,
            maxTapMovement: 10,
            zoomSensitivity: 0.01
        };

        this.initializeMobileEvents();
        this.createMobileControls();
    }

    initializeMobileEvents() {
        // Touch events for map interaction
        const mapContainer = document.querySelector('.territory-map');
        if (mapContainer) {
            mapContainer.addEventListener('touchstart', (e) => this.handleTouchStart(e));
            mapContainer.addEventListener('touchmove', (e) => this.handleTouchMove(e));
            mapContainer.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        }

        // Prevent default browser gestures
        document.addEventListener('gesturestart', (e) => e.preventDefault());
        document.addEventListener('gesturechange', (e) => e.preventDefault());
        document.addEventListener('gestureend', (e) => e.preventDefault());

        // Handle orientation changes
        window.addEventListener('orientationchange', () => this.handleOrientationChange());
    }

    createMobileControls() {
        const controls = document.createElement('div');
        controls.className = 'mobile-controls';
        controls.innerHTML = `
            <div class="mobile-control-group">
                <button class="mobile-btn zoom-in">
                    <i class="fas fa-plus"></i>
                </button>
                <button class="mobile-btn zoom-out">
                    <i class="fas fa-minus"></i>
                </button>
            </div>
            <div class="mobile-control-group">
                <button class="mobile-btn attack">
                    <i class="fas fa-crosshairs"></i>
                </button>
                <button class="mobile-btn reinforce">
                    <i class="fas fa-shield-alt"></i>
                </button>
            </div>
            <div class="mobile-control-group">
                <button class="mobile-btn info">
                    <i class="fas fa-info-circle"></i>
                </button>
                <button class="mobile-btn menu">
                    <i class="fas fa-bars"></i>
                </button>
            </div>
        `;

        document.body.appendChild(controls);
        this.initializeMobileControls(controls);
    }

    initializeMobileControls(controls) {
        // Zoom controls
        controls.querySelector('.zoom-in').addEventListener('click', () => {
            if (window.territoryVisualization) {
                window.territoryVisualization.adjustZoom(0.1);
            }
        });

        controls.querySelector('.zoom-out').addEventListener('click', () => {
            if (window.territoryVisualization) {
                window.territoryVisualization.adjustZoom(-0.1);
            }
        });

        // Action controls
        controls.querySelector('.attack').addEventListener('click', () => {
            if (this.selectedTerritory && window.territoryInteractions) {
                window.territoryInteractions.executeAction('attack', this.selectedTerritory);
            }
        });

        controls.querySelector('.reinforce').addEventListener('click', () => {
            if (this.selectedTerritory && window.territoryInteractions) {
                window.territoryInteractions.executeAction('reinforce', this.selectedTerritory);
            }
        });

        // Info and menu controls
        controls.querySelector('.info').addEventListener('click', () => {
            if (this.selectedTerritory) {
                this.toggleTerritoryInfo();
            }
        });

        controls.querySelector('.menu').addEventListener('click', () => {
            this.showMobileMenu();
        });
    }

    handleTouchStart(e) {
        if (e.touches.length === 1) {
            // Single touch - potential tap or swipe
            const touch = e.touches[0];
            this.touchStartX = touch.clientX;
            this.touchStartY = touch.clientY;
            
            // Set up long press detection
            this.gestureTimeout = setTimeout(() => {
                this.handleLongPress(touch);
            }, this.settings.longPressDelay);

        } else if (e.touches.length === 2) {
            // Pinch gesture
            this.handlePinchStart(e);
        }
    }

    handleTouchMove(e) {
        if (this.gestureTimeout) {
            clearTimeout(this.gestureTimeout);
            this.gestureTimeout = null;
        }

        if (e.touches.length === 1) {
            // Handle pan/swipe
            const touch = e.touches[0];
            const deltaX = touch.clientX - this.touchStartX;
            const deltaY = touch.clientY - this.touchStartY;

            if (Math.abs(deltaX) > this.settings.minSwipeDistance ||
                Math.abs(deltaY) > this.settings.minSwipeDistance) {
                this.handlePan(deltaX, deltaY);
            }

        } else if (e.touches.length === 2) {
            // Handle pinch zoom
            this.handlePinchMove(e);
        }
    }

    handleTouchEnd(e) {
        if (this.gestureTimeout) {
            clearTimeout(this.gestureTimeout);
            this.gestureTimeout = null;
        }

        if (!this.isGesturing) {
            const touch = e.changedTouches[0];
            const deltaX = touch.clientX - this.touchStartX;
            const deltaY = touch.clientY - this.touchStartY;

            if (Math.abs(deltaX) < this.settings.maxTapMovement &&
                Math.abs(deltaY) < this.settings.maxTapMovement) {
                this.handleTap(touch);
            }
        }

        this.isGesturing = false;
    }

    handleTap(touch) {
        const now = Date.now();
        const timeSinceLastTap = now - this.lastTap;

        if (timeSinceLastTap < this.settings.doubleTapDelay) {
            // Double tap
            this.handleDoubleTap(touch);
        } else {
            // Single tap
            this.handleSingleTap(touch);
        }

        this.lastTap = now;
    }

    handleSingleTap(touch) {
        const territory = this.getTerritoryAtPoint(touch.clientX, touch.clientY);
        if (territory) {
            this.selectTerritory(territory);
        } else {
            this.clearSelection();
        }
    }

    handleDoubleTap(touch) {
        const territory = this.getTerritoryAtPoint(touch.clientX, touch.clientY);
        if (territory) {
            // Quick action based on territory status
            const action = territory.status === 'friendly' ? 'reinforce' : 'attack';
            if (window.territoryInteractions) {
                window.territoryInteractions.executeAction(action, territory.id);
            }
        }
    }

    handleLongPress(touch) {
        const territory = this.getTerritoryAtPoint(touch.clientX, touch.clientY);
        if (territory) {
            this.showTerritoryContextMenu(territory, touch.clientX, touch.clientY);
        }
    }

    handlePinchStart(e) {
        this.isGesturing = true;
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        this.pinchStartDistance = this.getPinchDistance(touch1, touch2);
        this.initialZoom = window.territoryVisualization?.currentZoom || 1;
    }

    handlePinchMove(e) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = this.getPinchDistance(touch1, touch2);
        const scale = currentDistance / this.pinchStartDistance;

        if (window.territoryVisualization) {
            const newZoom = this.initialZoom * scale;
            window.territoryVisualization.setZoom(newZoom);
        }
    }

    handlePan(deltaX, deltaY) {
        if (window.territoryVisualization) {
            window.territoryVisualization.pan(deltaX, deltaY);
        }
    }

    getPinchDistance(touch1, touch2) {
        return Math.hypot(
            touch2.clientX - touch1.clientX,
            touch2.clientY - touch1.clientY
        );
    }

    getTerritoryAtPoint(x, y) {
        const elements = document.elementsFromPoint(x, y);
        const territoryElement = elements.find(el => el.classList.contains('territory'));
        return territoryElement ? {
            id: territoryElement.dataset.id,
            status: territoryElement.dataset.status
        } : null;
    }

    showTerritoryContextMenu(territory, x, y) {
        const menu = document.createElement('div');
        menu.className = 'territory-context-menu';
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;

        menu.innerHTML = `
            <div class="context-menu-item" data-action="attack">
                <i class="fas fa-crosshairs"></i> Attack
            </div>
            <div class="context-menu-item" data-action="reinforce">
                <i class="fas fa-shield-alt"></i> Reinforce
            </div>
            <div class="context-menu-item" data-action="info">
                <i class="fas fa-info-circle"></i> Info
            </div>
        `;

        document.body.appendChild(menu);

        // Handle menu item clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.closest('.context-menu-item')?.dataset.action;
            if (action && window.territoryInteractions) {
                window.territoryInteractions.executeAction(action, territory.id);
            }
            menu.remove();
        });

        // Remove menu when clicking outside
        document.addEventListener('click', function removeMenu(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', removeMenu);
            }
        });
    }

    handleOrientationChange() {
        // Adjust map and controls layout
        setTimeout(() => {
            if (window.territoryVisualization) {
                window.territoryVisualization.resetView();
            }
            this.updateMobileControlsPosition();
        }, 100);
    }

    updateMobileControlsPosition() {
        const controls = document.querySelector('.mobile-controls');
        if (!controls) return;

        const isLandscape = window.innerWidth > window.innerHeight;
        controls.classList.toggle('landscape', isLandscape);
    }

    showMobileMenu() {
        const menu = document.createElement('div');
        menu.className = 'mobile-menu';
        menu.innerHTML = `
            <div class="mobile-menu-content">
                <h3>Territory Controls</h3>
                <div class="mobile-menu-section">
                    <h4>Gestures</h4>
                    <ul>
                        <li>Tap: Select territory</li>
                        <li>Double tap: Quick action</li>
                        <li>Long press: Context menu</li>
                        <li>Pinch: Zoom map</li>
                        <li>Pan: Move map</li>
                    </ul>
                </div>
                <button class="close-menu">Close</button>
            </div>
        `;

        document.body.appendChild(menu);

        menu.querySelector('.close-menu').addEventListener('click', () => {
            menu.remove();
        });
    }
}

// Initialize mobile optimizations when document is ready
document.addEventListener('DOMContentLoaded', () => {
    if ('ontouchstart' in window) {
        window.territoryMobile = new TerritoryMobile();
    }
});
