document.addEventListener('DOMContentLoaded', function() {
    const itemGrid = document.getElementById('marketplaceItems');
    const itemTemplate = document.getElementById('itemTemplate');
    const searchInput = document.getElementById('searchItem');
    const typeFilter = document.getElementById('itemType');
    const rarityFilter = document.getElementById('itemRarity');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    let currentPage = 1;
    let totalPages = 1;
    let currentFilters = {
        type: 'all',
        rarity: 'all',
        search: '',
        page: 1
    };

    // Load marketplace items
    async function loadItems() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch(`/api/marketplace/items?${new URLSearchParams(currentFilters)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load marketplace items');
            }

            const data = await response.json();
            displayItems(data.items);
            updatePagination(data.total_pages);

        } catch (error) {
            console.error('Error loading marketplace items:', error);
            showError('Failed to load marketplace items. Please try again later.');
        }
    }

    // Display items in the grid
    function displayItems(items) {
        itemGrid.innerHTML = '';
        items.forEach(item => {
            const itemCard = itemTemplate.content.cloneNode(true);
            
            // Set item details
            itemCard.querySelector('.item-image').src = `/static/images/items/${item.image}`;
            itemCard.querySelector('.item-image').alt = item.name;
            itemCard.querySelector('.item-name').textContent = item.name;
            itemCard.querySelector('.item-description').textContent = item.description;
            itemCard.querySelector('.item-stats').textContent = formatStats(item.stats);
            itemCard.querySelector('.item-price').textContent = `${item.price} Crystals`;
            
            // Add rarity class
            itemCard.querySelector('.item-card').classList.add(`rarity-${item.rarity.toLowerCase()}`);
            
            // Add purchase handler
            itemCard.querySelector('.buy-btn').addEventListener('click', () => purchaseItem(item.id));
            
            itemGrid.appendChild(itemCard);
        });
    }

    // Format item stats for display
    function formatStats(stats) {
        return Object.entries(stats)
            .map(([key, value]) => `${key.replace('_', ' ')}: ${value}`)
            .join(' | ');
    }

    // Purchase item
    async function purchaseItem(itemId) {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch(`/api/marketplace/purchase/${itemId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.message || 'Failed to purchase item');
            }

            const data = await response.json();
            showSuccess('Item purchased successfully!');
            loadItems(); // Refresh the marketplace

        } catch (error) {
            console.error('Error purchasing item:', error);
            showError(error.message || 'Failed to purchase item. Please try again later.');
        }
    }

    // Update pagination
    function updatePagination(total) {
        totalPages = total;
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevButton.disabled = currentPage === 1;
        nextButton.disabled = currentPage === totalPages;
    }

    // Event Listeners
    searchInput.addEventListener('input', debounce(() => {
        currentFilters.search = searchInput.value;
        currentFilters.page = 1;
        currentPage = 1;
        loadItems();
    }, 300));

    typeFilter.addEventListener('change', () => {
        currentFilters.type = typeFilter.value;
        currentFilters.page = 1;
        currentPage = 1;
        loadItems();
    });

    rarityFilter.addEventListener('change', () => {
        currentFilters.rarity = rarityFilter.value;
        currentFilters.page = 1;
        currentPage = 1;
        loadItems();
    });

    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            currentFilters.page = currentPage;
            loadItems();
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            currentFilters.page = currentPage;
            loadItems();
        }
    });

    // Utility functions
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function showError(message) {
        // Implement error notification
        alert(message);
    }

    function showSuccess(message) {
        // Implement success notification
        alert(message);
    }

    // Initial load
    loadItems();
});
