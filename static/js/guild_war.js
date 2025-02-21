// Initialize WebSocket connection
const socket = io();

// War Timer
function updateTimer(endTime) {
    const timerElement = document.querySelector('.countdown');
    if (!timerElement) return;

    const endDateTime = new Date(endTime);
    
    function updateDisplay() {
        const now = new Date();
        const diff = endDateTime - now;

        if (diff <= 0) {
            timerElement.innerHTML = 'War Ended';
            location.reload();  // Refresh to show results
            return;
        }

        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        timerElement.innerHTML = `
            <span class="hours">${String(hours).padStart(2, '0')}</span>:
            <span class="minutes">${String(minutes).padStart(2, '0')}</span>:
            <span class="seconds">${String(seconds).padStart(2, '0')}</span>
        `;
    }

    updateDisplay();
    setInterval(updateDisplay, 1000);
}

// War Declaration
async function declareWar(event) {
    event.preventDefault();
    const form = event.target;
    const targetGuildId = form.querySelector('#target-guild').value;

    try {
        const response = await fetch('/api/guild/war/declare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_guild_id: targetGuildId
            })
        });

        const data = await response.json();
        if (data.success) {
            showSuccess('War declared successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('Failed to declare war');
        console.error(error);
    }
}

// Participant Management
let selectedParticipants = new Set();

function updateParticipants(checkbox) {
    const memberId = checkbox.value;
    
    if (checkbox.checked) {
        if (selectedParticipants.size >= maxParticipants) {
            checkbox.checked = false;
            showError(`Maximum ${maxParticipants} participants allowed`);
            return;
        }
        selectedParticipants.add(memberId);
    } else {
        selectedParticipants.delete(memberId);
    }

    updateParticipantCount();
    saveParticipants();
}

function updateParticipantCount() {
    const countElement = document.querySelector('.registered-count');
    if (countElement) {
        countElement.textContent = `${selectedParticipants.size}/${maxParticipants} Members Registered`;
    }
}

async function saveParticipants() {
    try {
        const response = await fetch('/api/guild/war/participants', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                war_id: warId,
                participants: Array.from(selectedParticipants)
            })
        });

        const data = await response.json();
        if (!data.success) {
            showError(data.message);
        }
    } catch (error) {
        showError('Failed to update participants');
        console.error(error);
    }
}

// Territory Management
const territories = document.querySelectorAll('.territory');
territories.forEach(territory => {
    territory.addEventListener('click', () => {
        if (!territory.classList.contains('active')) {
            showTerritoryInfo(territory);
        }
    });
});

function showTerritoryInfo(territory) {
    const territoryId = territory.dataset.id;
    const territoryName = territory.dataset.name;
    const controller = territory.dataset.controller;

    const infoBox = document.createElement('div');
    infoBox.className = 'territory-info';
    infoBox.innerHTML = `
        <h3>${territoryName}</h3>
        <p>Controlled by: ${controller || 'Neutral'}</p>
        <div class="territory-actions">
            <button onclick="attackTerritory('${territoryId}')" 
                    class="action-btn"
                    ${controller === guildName ? 'disabled' : ''}>
                Attack
            </button>
            <button onclick="reinforceTerritory('${territoryId}')"
                    class="action-btn"
                    ${controller !== guildName ? 'disabled' : ''}>
                Reinforce
            </button>
        </div>
    `;

    // Remove any existing info boxes
    document.querySelectorAll('.territory-info').forEach(box => box.remove());
    territory.appendChild(infoBox);
    territory.classList.add('active');

    // Close when clicking outside
    document.addEventListener('click', function closeInfo(e) {
        if (!territory.contains(e.target)) {
            infoBox.remove();
            territory.classList.remove('active');
            document.removeEventListener('click', closeInfo);
        }
    });
}

async function attackTerritory(territoryId) {
    try {
        const response = await fetch('/api/guild/war/territory/attack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ territory_id: territoryId })
        });

        const data = await response.json();
        if (data.success) {
            showSuccess('Attack initiated!');
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('Failed to initiate attack');
        console.error(error);
    }
}

async function reinforceTerritory(territoryId) {
    try {
        const response = await fetch('/api/guild/war/territory/reinforce', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ territory_id: territoryId })
        });

        const data = await response.json();
        if (data.success) {
            showSuccess('Territory reinforced!');
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('Failed to reinforce territory');
        console.error(error);
    }
}

// WebSocket Event Handlers
socket.on('war_update', function(data) {
    if (data.war_id === warId) {
        switch (data.type) {
            case 'score_update':
                updateScores(data.scores);
                break;
            case 'territory_update':
                updateTerritory(data.territory);
                break;
            case 'event':
                addEventToLog(data.event);
                break;
        }
    }
});

function updateScores(scores) {
    Object.entries(scores).forEach(([guildId, score]) => {
        const scoreElement = document.querySelector(`.guild-${guildId} .score`);
        if (scoreElement) {
            scoreElement.textContent = score;
        }
    });
}

function updateTerritory(territory) {
    const territoryElement = document.querySelector(`.territory[data-id="${territory.id}"]`);
    if (territoryElement) {
        territoryElement.className = `territory ${territory.status}`;
        territoryElement.dataset.controller = territory.controller_name;
    }
}

function addEventToLog(event) {
    const eventList = document.querySelector('.event-list');
    if (!eventList) return;

    const eventElement = document.createElement('div');
    eventElement.className = `event-item ${event.type}`;
    eventElement.innerHTML = `
        <div class="event-time">${formatTime(event.timestamp)}</div>
        <div class="event-details">${formatEventDetails(event)}</div>
        <div class="event-points">+${event.points} points</div>
    `;

    eventList.insertBefore(eventElement, eventList.firstChild);

    // Remove old events if too many
    if (eventList.children.length > 50) {
        eventList.lastChild.remove();
    }
}

// Utility Functions
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

function formatEventDetails(event) {
    switch (event.type) {
        case 'kill':
            return `<span class="player">${event.killer}</span> defeated <span class="player">${event.victim}</span>`;
        case 'capture':
            return `<span class="guild">${event.guild}</span> captured ${event.territory}`;
        case 'boss':
            return `<span class="guild">${event.guild}</span> defeated boss at ${event.location}`;
        default:
            return event.message;
    }
}

function showSuccess(message) {
    const notification = document.createElement('div');
    notification.className = 'notification success';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
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
    const countdownElement = document.querySelector('.countdown');
    if (countdownElement) {
        updateTimer(countdownElement.dataset.endTime);
    }

    // Initialize participant checkboxes
    const participantCheckboxes = document.querySelectorAll('input[name="war_participant"]');
    participantCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedParticipants.add(checkbox.value);
        }
    });
    updateParticipantCount();
});
