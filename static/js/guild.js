// Initialize WebSocket connection
const socket = io();

// Navigation
document.querySelectorAll('.nav-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        button.classList.add('active');

        // Show corresponding section
        document.querySelectorAll('.guild-section').forEach(section => 
            section.classList.remove('active')
        );
        document.getElementById(`${button.dataset.target}-section`).classList.add('active');
    });
});

// Member Management
async function promoteMember(memberId) {
    try {
        const result = await api.post('/api/guild/promote', { memberId });
        if (result.success) {
            showSuccess('Member promoted successfully!');
            updateMemberList();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to promote member');
    }
}

async function demoteMember(memberId) {
    try {
        const result = await api.post('/api/guild/demote', { memberId });
        if (result.success) {
            showSuccess('Member demoted successfully!');
            updateMemberList();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to demote member');
    }
}

async function kickMember(memberId) {
    try {
        const result = await api.post('/api/guild/kick', { memberId });
        if (result.success) {
            showSuccess('Member kicked successfully!');
            updateMemberList();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to kick member');
    }
}

// Update Member List
function updateMemberList() {
    // Fetch updated member list and refresh the display
    loadGuildMembers();
}

// WebSocket Event Handlers
socket.on('guild_update', function(data) {
    if (data.guild_id === {{ guild.id }}) {
        updateMember(data.member);
    }
});

// Utility Functions
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
    loadGuildMembers();
});
