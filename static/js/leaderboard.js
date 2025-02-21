// Initialize WebSocket connection
const socket = io();
let currentFilters = {
    hunters: {
        class: '',
        rank: ''
    },
    guilds: {
        size: ''
    },
    gates: {
        rank: '',
        type: ''
    }
};

// Navigation
document.querySelectorAll('.nav-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        button.classList.add('active');

        // Show corresponding section
        document.querySelectorAll('.leaderboard-section').forEach(section => 
            section.classList.remove('active')
        );
        document.getElementById(`${button.dataset.target}-section`).classList.add('active');
    });
});

// Filter Handlers
document.getElementById('hunter-class-filter').addEventListener('change', (e) => {
    currentFilters.hunters.class = e.target.value;
    applyFilters('hunters');
});

document.getElementById('hunter-rank-filter').addEventListener('change', (e) => {
    currentFilters.hunters.rank = e.target.value;
    applyFilters('hunters');
});

document.getElementById('guild-size-filter').addEventListener('change', (e) => {
    currentFilters.guilds.size = e.target.value;
    applyFilters('guilds');
});

document.getElementById('gate-rank-filter').addEventListener('change', (e) => {
    currentFilters.gates.rank = e.target.value;
    applyFilters('gates');
});

document.getElementById('gate-type-filter').addEventListener('change', (e) => {
    currentFilters.gates.type = e.target.value;
    applyFilters('gates');
});

// Apply Filters
async function applyFilters(section) {
    const tbody = document.getElementById(`${section}-tbody`);
    tbody.classList.add('loading');

    try {
        const response = await fetch(`/api/leaderboard/${section}?` + new URLSearchParams(currentFilters[section]));
        const data = await response.json();
        
        if (data.success) {
            updateTable(section, data.rankings);
        } else {
            showError('Failed to update rankings');
        }
    } catch (error) {
        console.error('Error applying filters:', error);
        showError('Failed to update rankings');
    } finally {
        tbody.classList.remove('loading');
    }
}

// Update Tables
function updateHuntersTable(rankings) {
    const tbody = document.getElementById('hunters-tbody');
    tbody.innerHTML = '';

    rankings.forEach((hunter, index) => {
        const row = document.createElement('tr');
        row.className = `hunter-row ${hunter.id === currentUserId ? 'current-user' : ''}`;
        
        row.innerHTML = `
            <td class="rank">${index + 1}</td>
            <td class="hunter-info">
                <img src="/static/images/avatars/${hunter.avatar || 'default_avatar.png'}" alt="${hunter.username}">
                <span>${hunter.username}</span>
                ${hunter.guild ? `<span class="guild-tag">[${hunter.guild.name}]</span>` : ''}
            </td>
            <td>${hunter.level}</td>
            <td class="class-${hunter.job_class.toLowerCase()}">${hunter.job_class}</td>
            <td class="rank-${hunter.hunter_class.toLowerCase()}">${hunter.hunter_class}</td>
            <td>${hunter.gates_cleared}</td>
            <td>${hunter.achievements_completed}/${hunter.achievements_total}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateGuildsTable(rankings) {
    const tbody = document.getElementById('guilds-tbody');
    tbody.innerHTML = '';

    rankings.forEach((guild, index) => {
        const row = document.createElement('tr');
        row.className = `guild-row ${guild.id === currentGuildId ? 'current-guild' : ''}`;
        
        row.innerHTML = `
            <td class="rank">${index + 1}</td>
            <td class="guild-info">
                <img src="/static/images/guilds/${guild.emblem || 'default_guild.png'}" alt="${guild.name}">
                <span>${guild.name}</span>
            </td>
            <td>${guild.level}</td>
            <td>${guild.member_count}/${guild.max_members}</td>
            <td>${guild.total_gates_cleared}</td>
            <td>${guild.average_level.toFixed(1)}</td>
            <td>${guild.achievements_completed}/${guild.achievements_total}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateGatesTable(rankings) {
    const tbody = document.getElementById('gates-tbody');
    tbody.innerHTML = '';

    rankings.forEach(gate => {
        const row = document.createElement('tr');
        row.className = `gate-row rank-${gate.rank.toLowerCase()}`;
        
        row.innerHTML = `
            <td class="gate-info">
                <span class="gate-rank">${gate.rank}</span>
                <span class="gate-name">${gate.name}</span>
            </td>
            <td class="first-clear">
                ${gate.first_clear ? createPlayerInfo(gate.first_clear, true) : '<span class="unclaimed">Unclaimed</span>'}
            </td>
            <td class="fastest-clear">
                ${gate.fastest_clear ? createPlayerInfo(gate.fastest_clear, false, gate.fastest_clear.duration) : '<span class="unclaimed">Unclaimed</span>'}
            </td>
            <td class="most-efficient">
                ${gate.most_efficient ? createPlayerInfo(gate.most_efficient, false, `${gate.most_efficient.efficiency}%`) : '<span class="unclaimed">Unclaimed</span>'}
            </td>
            <td>${gate.total_clears}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function createPlayerInfo(player, showDate, extraInfo = '') {
    return `
        <div class="player-info">
            <img src="/static/images/avatars/${player.avatar}" alt="${player.username}">
            <span>${player.username}</span>
            ${showDate ? 
                `<span class="clear-date">${formatDate(player.timestamp)}</span>` :
                `<span class="clear-info">${extraInfo}</span>`
            }
        </div>
    `;
}

// WebSocket Event Handlers
socket.on('leaderboard_update', function(data) {
    switch (data.type) {
        case 'hunters':
            updateHuntersTable(data.rankings);
            break;
        case 'guilds':
            updateGuildsTable(data.rankings);
            break;
        case 'gates':
            updateGatesTable(data.rankings);
            break;
        case 'stats':
            updateStats(data.stats);
            break;
    }
});

// Stats Update
function updateStats(stats) {
    document.querySelectorAll('.stat-card').forEach(card => {
        const statKey = card.dataset.stat;
        if (stats[statKey] !== undefined) {
            const valueElement = card.querySelector('.stat-value');
            const oldValue = parseInt(valueElement.textContent);
            const newValue = stats[statKey];
            
            valueElement.textContent = newValue;
            
            if (newValue > oldValue) {
                valueElement.classList.add('increase');
            } else if (newValue < oldValue) {
                valueElement.classList.add('decrease');
            }
            
            setTimeout(() => {
                valueElement.classList.remove('increase', 'decrease');
            }, 1000);
        }
    });
}

// Utility Functions
function formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showError(message) {
    const notification = document.createElement('div');
    notification.className = 'notification error';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get current user/guild IDs from data attributes
    window.currentUserId = document.body.dataset.userId;
    window.currentGuildId = document.body.dataset.guildId;
});
