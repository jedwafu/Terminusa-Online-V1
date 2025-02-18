document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    const typeFilter = document.getElementById('type-filter');
    const rarityFilter = document.getElementById('rarity-filter');
    const itemsGrid = document.querySelector('.items-grid');

    function filterItems() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedType = typeFilter.value;
        const selectedRarity = rarityFilter.value;

        document.querySelectorAll('.item-card').forEach(card => {
            const name = card.querySelector('.item-name').textContent.toLowerCase();
            const type = card.querySelector('.item-type span:first-child').textContent.toLowerCase();
            const rarity = card.querySelector('.item-rarity').textContent.toLowerCase();

            const matchesSearch = name.includes(searchTerm);
            const matchesType = selectedType === 'all' || type === selectedType;
            const matchesRarity = selectedRarity === 'all' || rarity === selectedRarity;

            card.style.display = matchesSearch && matchesType && matchesRarity ? 'block' : 'none';
        });
    }

    // Add event listeners
    if (searchInput) {
        searchInput.addEventListener('input', filterItems);
    }
    if (typeFilter) {
        typeFilter.addEventListener('change', filterItems);
    }
    if (rarityFilter) {
        rarityFilter.addEventListener('change', filterItems);
    }
});

// Global functions for item actions
window.createItem = function() {
    // Implementation for creating new item
    console.log('Create item functionality will be implemented');
};

window.purchaseItem = function(itemId) {
    // Implementation for purchasing item
    console.log('Purchase item functionality will be implemented for item:', itemId);
};
