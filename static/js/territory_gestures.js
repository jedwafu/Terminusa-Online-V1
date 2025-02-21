class TerritoryGestures {
    constructor() {
        this.hammer = null;
        this.pinchStart = { scale: 1 };
        this.lastPanPosition = { x: 0, y: 0 };
        this.isGesturing = false;
        this.gestureTimeout = null;

        // Gesture settings
        this.settings = {
            panThreshold: 10,
            pinchThreshold: 0.1,
            rotationThreshold: 15,
            doubleTapDelay: 300,
            longPressDelay: 500,
            minSwipeVelocity: 0.3
        };

        this.initializeGestures();
    }

    initializeGestures() {
        const mapContainer = document.querySelector('.territory-map');
        if (!mapContainer || !window.Hammer) return;

        // Initialize Hammer.js
        this.hammer = new Hammer.Manager(mapContainer);

        // Add recognizers
        this.addPanRecognizer();
        this.addPinchRecognizer();
        this.addTapRecognizer();
        this.addSwipeRecognizer();

        // Bind gesture handlers
        this.bindGestureHandlers();
    }

    addPanRecognizer() {
        const pan = new Hammer.Pan({ 
            threshold: this.settings.panThreshold,
            direction: Hammer.DIRECTION_ALL
        });
        this.hammer.add(pan);
    }

    addPinchRecognizer() {
        const pinch = new Hammer.Pinch({
            threshold: this.settings.pinchThreshold
        });
        this.hammer.add(pinch);
    }

    addTapRecognizer() {
        const tap = new Hammer.Tap({ 
            taps: 1 
        });
        const doubleTap = new Hammer.Tap({ 
            taps: 2,
            interval: this.settings.doubleTapDelay
        });
        const press = new Hammer.Press({
            time: this.settings.longPressDelay
        });

        this.hammer.add([tap, doubleTap, press]);
        doubleTap.recognizeWith(tap);
        tap.requireFailure(doubleTap);
    }

    addSwipeRecognizer() {
        const swipe = new Hammer.Swipe({
            velocity: this.settings.minSwipeVelocity,
            direction: Hammer.DIRECTION_ALL
        });
        this.hammer.add(swipe);
    }

    bindGestureHandlers() {
        // Pan handling
        this.hammer.on('panstart', (e) => {
            this.handlePanStart(e);
        });

        this.hammer.on('panmove', (e) => {
            this.handlePanMove(e);
        });

        this.hammer.on('panend', (e) => {
            this.handlePanEnd(e);
        });

        // Pinch handling
        this.hammer.on('pinchstart', (e) => {
            this.handlePinchStart(e);
        });

        this.hammer.on('pinchmove', (e) => {
            this.handlePinchMove(e);
        });

        this.hammer.on('pinchend', (e) => {
            this.handlePinchEnd(e);
        });

        // Tap handling
        this.hammer.on('tap', (e) => {
            this.handleTap(e);
        });

        this.hammer.on('doubletap', (e) => {
            this.handleDoubleTap(e);
        });

        this.hammer.on('press', (e) => {
            this.handlePress(e);
        });

        // Swipe handling
        this.hammer.on('swipe', (e) => {
            this.handleSwipe(e);
        });
    }

    handlePanStart(event) {
        this.isGesturing = true;
        this.lastPanPosition = {
            x: event.center.x,
            y: event.center.y
        };

        // Add visual feedback
        this.addTouchFeedback(event.center.x, event.center.y);
    }

    handlePanMove(event) {
        if (!this.isGesturing) return;

        const deltaX = event.center.x - this.lastPanPosition.x;
        const deltaY = event.center.y - this.lastPanPosition.y;

        if (window.territoryVisualization) {
            window.territoryVisualization.pan(deltaX, deltaY);
        }

        this.lastPanPosition = {
            x: event.center.x,
            y: event.center.y
        };
    }

    handlePanEnd(event) {
        this.isGesturing = false;
        
        // Add momentum if swipe was fast enough
        if (event.velocity > this.settings.minSwipeVelocity) {
            this.addPanMomentum(event);
        }
    }

    handlePinchStart(event) {
        this.isGesturing = true;
        this.pinchStart.scale = event.scale;

        // Add visual feedback
        this.addPinchFeedback(event.center.x, event.center.y);
    }

    handlePinchMove(event) {
        if (!this.isGesturing) return;

        const scaleDelta = event.scale / this.pinchStart.scale;
        if (window.territoryVisualization) {
            window.territoryVisualization.zoom(scaleDelta);
        }
    }

    handlePinchEnd() {
        this.isGesturing = false;
    }

    handleTap(event) {
        const territory = this.getTerritoryAtPoint(event.center.x, event.center.y);
        if (territory) {
            this.selectTerritory(territory);
        } else {
            this.clearSelection();
        }

        // Add visual feedback
        this.addTapFeedback(event.center.x, event.center.y);
    }

    handleDoubleTap(event) {
        const territory = this.getTerritoryAtPoint(event.center.x, event.center.y);
        if (territory) {
            // Quick action based on territory status
            const action = territory.status === 'friendly' ? 'reinforce' : 'attack';
            this.executeQuickAction(territory, action);
        } else {
            // Reset view to default zoom/position
            if (window.territoryVisualization) {
                window.territoryVisualization.resetView();
            }
        }

        // Add visual feedback
        this.addDoubleTapFeedback(event.center.x, event.center.y);
    }

    handlePress(event) {
        const territory = this.getTerritoryAtPoint(event.center.x, event.center.y);
        if (territory) {
            this.showContextMenu(territory, event.center.x, event.center.y);
        }

        // Add visual feedback
        this.addPressFeedback(event.center.x, event.center.y);
    }

    handleSwipe(event) {
        // Handle quick navigation between territories
        const direction = this.getSwipeDirection(event);
        if (window.territoryInteractions) {
            window.territoryInteractions.navigateTerritory(direction);
        }
    }

    getTerritoryAtPoint(x, y) {
        const elements = document.elementsFromPoint(x, y);
        const territoryElement = elements.find(el => el.classList.contains('territory'));
        return territoryElement ? {
            id: territoryElement.dataset.id,
            status: territoryElement.dataset.status
        } : null;
    }

    selectTerritory(territory) {
        if (window.territoryInteractions) {
            window.territoryInteractions.handleTerritorySelect(territory);
        }
    }

    clearSelection() {
        if (window.territoryInteractions) {
            window.territoryInteractions.deselectTerritory();
        }
    }

    executeQuickAction(territory, action) {
        if (window.territoryInteractions) {
            window.territoryInteractions.executeAction(action, territory.id);
        }
    }

    showContextMenu(territory, x, y) {
        if (window.territoryMobile) {
            window.territoryMobile.showTerritoryContextMenu(territory, x, y);
        }
    }

    addPanMomentum(event) {
        const velocityX = event.velocityX * 100;
        const velocityY = event.velocityY * 100;
        let frame = 0;

        const animate = () => {
            if (frame >= 30) return; // Stop after 30 frames

            const easeOut = 1 - (frame / 30);
            const deltaX = velocityX * easeOut;
            const deltaY = velocityY * easeOut;

            if (window.territoryVisualization) {
                window.territoryVisualization.pan(deltaX, deltaY);
            }

            frame++;
            requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
    }

    addTouchFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'touch-feedback';
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        document.body.appendChild(feedback);

        feedback.addEventListener('animationend', () => {
            feedback.remove();
        });
    }

    addPinchFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'pinch-feedback';
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        document.body.appendChild(feedback);

        feedback.addEventListener('animationend', () => {
            feedback.remove();
        });
    }

    addTapFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'tap-feedback';
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        document.body.appendChild(feedback);

        feedback.addEventListener('animationend', () => {
            feedback.remove();
        });
    }

    addDoubleTapFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'double-tap-feedback';
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        document.body.appendChild(feedback);

        feedback.addEventListener('animationend', () => {
            feedback.remove();
        });
    }

    addPressFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'press-feedback';
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        document.body.appendChild(feedback);

        feedback.addEventListener('animationend', () => {
            feedback.remove();
        });
    }

    getSwipeDirection(event) {
        const angle = event.angle;
        if (angle > -45 && angle <= 45) return 'right';
        if (angle > 45 && angle <= 135) return 'down';
        if (angle > 135 || angle <= -135) return 'left';
        return 'up';
    }
}

// Initialize gestures when document is ready
document.addEventListener('DOMContentLoaded', () => {
    if ('ontouchstart' in window && window.Hammer) {
        window.territoryGestures = new TerritoryGestures();
    }
});
