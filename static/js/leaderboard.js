document.addEventListener('DOMContentLoaded', function() {
    const rankFilter = document.getElementById('rankFilter');
    const timeFilter = document.getElementById('timeFilter');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    let currentPage = 1;
    let totalPages = 1;
    let currentFilters = {
        rank: 'all',
        timeframe: 'all',
        page: 1
    };

    // Load leaderboard data
    async function loadLeaderboard() {
        try {
            const response = await fetch(`/api/leaderboard?${new URLSearchParams(currentFilters)}`);

            if (!response.ok) {
                throw new Error('Failed to load leaderboard data');
            }

            const data = await response.json();
            updateLeaderboard(data);
            updatePagination(data.total_pages);

        } catch (error) {
            console.error('Error loading leaderboard:', error);
            showError('Failed to load leaderboard. Please try again later.');
        }
    }

    // Update leaderboard display
    function updateLeaderboard(data) {
        // Update top 3 players
        updateTopThree(data.players.slice(0, 3));
        
        // Update leaderboard table
        const tbody = document.querySelector('.leaderboard-table tbody');
        tbody.innerHTML = '';
        
        data.players.slice(3).forEach((player, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 4}</td>
                <td>${player.username}</td>
                <td>${player.level}</td>
                <td class="rank-${player.rank.toLowerCase()}">${player.rank}</td>
                <td>${player.gates_cleared}</td>
                <td>${player.title || 'Novice Hunter'}</td>
            `;
            tbody.appendChild(row);
        });

        // Add hover effects
        addTableHoverEffects();
    }

    // Update top three display
    function updateTopThree(topPlayers) {
        const positions = ['champion', 'runner-up left', 'runner-up right'];
        const frames = ['gold', 'silver', 'bronze'];
        
        topPlayers.forEach((player, index) => {
            const container = document.querySelector(`.${positions[index]}`);
            if (container) {
                const card = container.querySelector('.hunter-card');
                card.querySelector('h3').textContent = player.username;
                card.querySelector('.hunter-stats').innerHTML = `
                    Level ${player.level} • Rank ${player.rank}<br>
                    Gates Cleared: ${player.gates_cleared}
                `;
                
                // Update rank frame
                const frame = card.querySelector('.rank-frame');
                frame.src = `/static/images/rank-frame-${frames[index]}.png`;
                
                // Add animation class
                card.classList.add('animate-glow');
                setTimeout(() => card.classList.remove('animate-glow'), 2000);
            }
        });
    }

    // Add hover effects to table rows
    function addTableHoverEffects() {
        const rows = document.querySelectorAll('.leaderboard-table tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.classList.add('highlight');
                // Add particle effects or other visual enhancements
            });
            row.addEventListener('mouseleave', () => {
                row.classList.remove('highlight');
            });
        });
    }

    // Update pagination
    function updatePagination(total) {
        totalPages = total;
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevButton.disabled = currentPage === 1;
        nextButton.disabled = currentPage === totalPages;
    }

    // Event Listeners
    rankFilter.addEventListener('change', () => {
        currentFilters.rank = rankFilter.value;
        currentFilters.page = 1;
        currentPage = 1;
        loadLeaderboard();
    });

    timeFilter.addEventListener('change', () => {
        currentFilters.timeframe = timeFilter.value;
        currentFilters.page = 1;
        currentPage = 1;
        loadLeaderboard();
    });

    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            currentFilters.page = currentPage;
            loadLeaderboard();
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            currentFilters.page = currentPage;
            loadLeaderboard();
        }
    });

    // Add rank color indicators
    function addRankColorIndicators() {
        const ranks = ['S', 'A', 'B', 'C', 'D', 'E', 'F'];
        const rankCells = document.querySelectorAll('.rank-cell');
        
        rankCells.forEach(cell => {
            const rank = cell.textContent;
            cell.classList.add(`rank-${rank.toLowerCase()}`);
        });
    }

    // Add visual effects
    function addVisualEffects() {
        // Particle effects for top players
        const topCards = document.querySelectorAll('.hunter-card');
        topCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                // Add particle effects
                card.classList.add('particle-effect');
            });
            card.addEventListener('mouseleave', () => {
                card.classList.remove('particle-effect');
            });
        });

        // Smooth scrolling for pagination
        const tableContainer = document.querySelector('.leaderboard-table-container');
        if (tableContainer) {
            tableContainer.style.scrollBehavior = 'smooth';
        }
    }

    // Error handling
    function showError(message) {
        // Implement error notification
        alert(message);
    }

    // Initialize
    loadLeaderboard();
    addRankColorIndicators();
    addVisualEffects();

    // Auto-refresh leaderboard every 5 minutes
    setInterval(loadLeaderboard, 300000);
});
