// Navigation
document.querySelectorAll('.nav-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        button.classList.add('active');

        // Show corresponding section
        document.querySelectorAll('.profile-section').forEach(section => 
            section.classList.remove('active')
        );
        document.getElementById(`${button.dataset.target}-section`).classList.add('active');
    });
});

// History Tabs
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        button.classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.history-content').forEach(content => 
            content.classList.remove('active')
        );
        document.getElementById(`${button.dataset.tab}-history`).classList.add('active');
    });
});

// Equipment Tooltips
document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('mouseenter', event => {
        const item = event.currentTarget.dataset;
        if (!item) return;

        const tooltip = document.createElement('div');
        tooltip.className = 'item-tooltip';
        tooltip.innerHTML = `
            <h4>${item.name}</h4>
            <p class="rarity ${item.rarity.toLowerCase()}">${item.rarity}</p>
            ${item.stats ? createStatsDisplay(item.stats) : ''}
            <div class="durability">
                Durability: ${item.durability}%
            </div>
        `;

        card.appendChild(tooltip);
    });

    card.addEventListener('mouseleave', () => {
        const tooltip = card.querySelector('.item-tooltip');
        if (tooltip) tooltip.remove();
    });
});

// Achievement Progress
document.querySelectorAll('.achievement-card').forEach(card => {
    const progress = card.querySelector('.progress');
    if (progress) {
        // Animate progress bar
        const width = progress.style.width;
        progress.style.width = '0%';
        setTimeout(() => {
            progress.style.width = width;
        }, 100);
    }
});

// Stats Chart (if using chart.js)
function initializeStatsChart() {
    const ctx = document.getElementById('stats-chart');
    if (!ctx) return;

    const stats = {
        strength: parseInt(ctx.dataset.strength),
        agility: parseInt(ctx.dataset.agility),
        intelligence: parseInt(ctx.dataset.intelligence),
        vitality: parseInt(ctx.dataset.vitality)
    };

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(stats),
            datasets: [{
                label: 'Stats',
                data: Object.values(stats),
                backgroundColor: 'rgba(0, 123, 255, 0.2)',
                borderColor: 'rgba(0, 123, 255, 1)',
                pointBackgroundColor: 'rgba(0, 123, 255, 1)'
            }]
        },
        options: {
            scale: {
                ticks: {
                    beginAtZero: true,
                    max: Math.max(...Object.values(stats)) + 10
                }
            }
        }
    });
}

// Utility Functions
function createStatsDisplay(stats) {
    return `
        <div class="stats-display">
            ${Object.entries(stats).map(([key, value]) => `
                <div class="stat-row">
                    <span class="stat-name">${key}</span>
                    <span class="stat-value">${value}</span>
                </div>
            `).join('')}
        </div>
    `;
}

// Real-time Updates
let socket = null;

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/profile`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleUpdate(data);
    };
    
    socket.onclose = function() {
        // Attempt to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
}

function handleUpdate(data) {
    switch (data.type) {
        case 'stats_update':
            updateStats(data.stats);
            break;
        case 'achievement_complete':
            updateAchievement(data.achievement);
            break;
        case 'equipment_change':
            updateEquipment(data.equipment);
            break;
        case 'currency_update':
            updateCurrency(data.currency);
            break;
    }
}

function updateStats(stats) {
    Object.entries(stats).forEach(([stat, value]) => {
        const element = document.querySelector(`.stat-value[data-stat="${stat}"]`);
        if (element) {
            element.textContent = value;
            element.classList.add('updated');
            setTimeout(() => element.classList.remove('updated'), 1000);
        }
    });
}

function updateAchievement(achievement) {
    const card = document.querySelector(`.achievement-card[data-id="${achievement.id}"]`);
    if (!card) return;

    if (achievement.completed) {
        card.classList.add('completed');
        card.querySelector('.progress-bar').innerHTML = `
            <div class="completion-date">
                Completed: ${new Date().toLocaleString()}
            </div>
        `;
    } else {
        const progress = card.querySelector('.progress');
        const progressText = card.querySelector('.progress-text');
        progress.style.width = `${(achievement.progress / achievement.target) * 100}%`;
        progressText.textContent = `${achievement.progress}/${achievement.target}`;
    }
}

function updateEquipment(equipment) {
    const slot = document.querySelector(`.equipment-slot.${equipment.slot}`);
    if (!slot) return;

    if (equipment.item) {
        slot.innerHTML = createEquipmentCard(equipment.item);
    } else {
        slot.innerHTML = '<div class="empty-slot">Empty</div>';
    }
}

function updateCurrency(currency) {
    Object.entries(currency).forEach(([type, amount]) => {
        const element = document.querySelector(`.currency.${type} span`);
        if (element) {
            const oldValue = parseFloat(element.textContent.replace(/,/g, ''));
            const newValue = parseFloat(amount);
            
            element.textContent = amount;
            element.classList.add(newValue > oldValue ? 'increase' : 'decrease');
            setTimeout(() => {
                element.classList.remove('increase', 'decrease');
            }, 1000);
        }
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeStatsChart();
    initializeWebSocket();
});
