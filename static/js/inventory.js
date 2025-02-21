// API Handlers
const api = {
    async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showError('Failed to fetch data');
            throw error;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showError('Failed to process request');
            throw error;
        }
    }
};

// Inventory Management
let currentInventory = null;
let selectedItem = null;

async function loadInventory() {
    try {
        const result = await api.get('/api/inventory');
        if (result.success) {
            currentInventory = result.inventory;
            updateInventoryDisplay();
            updateEquippedSection();
            updateInventoryStats();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to load inventory');
    }
}

function updateInventoryDisplay() {
    const activeSection = document.querySelector('.inventory-section.active');
    if (activeSection.id === 'items-section') {
        displayItems();
    } else if (activeSection.id === 'mounts-section') {
        displayMounts();
    } else if (activeSection.id === 'pets-section') {
        displayPets();
    }
}

function displayItems() {
    const grid = document.getElementById('items-grid');
    grid.innerHTML = '';
    
    const typeFilter = document.getElementById('item-type-filter').value;
    const rarityFilter = document.getElementById('item-rarity-filter').value;
    
    const filteredItems = currentInventory.items.filter(item => {
        return (!typeFilter || item.type === typeFilter) &&
               (!rarityFilter || item.rarity.toLowerCase() === rarityFilter);
    });
    
    filteredItems.forEach(item => {
        const card = createItemCard(item);
        grid.appendChild(card);
    });
}

function createItemCard(item) {
    const card = document.createElement('div');
    card.className = `item-card ${item.rarity.toLowerCase()}`;
    card.onclick = () => showItemDetails(item);
    
    const durabilityClass = getDurabilityClass(item.durability);
    
    card.innerHTML = `
        <div class="item-image">
            <img src="/static/images/items/${item.type}/${item.image}" alt="${item.name}">
        </div>
        <div class="item-info">
            <h3>${item.name}</h3>
            <p class="rarity ${item.rarity.toLowerCase()}">${item.rarity}</p>
            <div class="durability-bar">
                <div class="durability-fill ${durabilityClass}" 
                     style="width: ${item.durability}%"></div>
            </div>
        </div>
    `;
    
    return card;
}

function getDurabilityClass(durability) {
    if (durability > 70) return 'durability-high';
    if (durability > 30) return 'durability-medium';
    return 'durability-low';
}

// Mount Management
function displayMounts() {
    const grid = document.getElementById('mounts-grid');
    grid.innerHTML = '';
    
    const rarityFilter = document.getElementById('mount-rarity-filter').value;
    
    const filteredMounts = currentInventory.mounts.filter(mount => 
        !rarityFilter || mount.rarity.toLowerCase() === rarityFilter
    );
    
    filteredMounts.forEach(mount => {
        const card = createMountCard(mount);
        grid.appendChild(card);
    });
}

function createMountCard(mount) {
    const card = document.createElement('div');
    card.className = `item-card ${mount.rarity.toLowerCase()}`;
    card.onclick = () => showMountDetails(mount);
    
    card.innerHTML = `
        <div class="item-image">
            <img src="/static/images/mounts/${mount.image}" alt="${mount.name}">
        </div>
        <div class="item-info">
            <h3>${mount.name}</h3>
            <p class="rarity ${mount.rarity.toLowerCase()}">${mount.rarity}</p>
            <div class="stats-preview">
                <span>Speed: ${mount.stats.speed}</span>
                <span>Stamina: ${mount.stats.stamina}</span>
            </div>
            ${mount.is_equipped ? '<div class="equipped-badge">Equipped</div>' : ''}
        </div>
    `;
    
    return card;
}

// Pet Management
function displayPets() {
    const grid = document.getElementById('pets-grid');
    grid.innerHTML = '';
    
    const rarityFilter = document.getElementById('pet-rarity-filter').value;
    
    const filteredPets = currentInventory.pets.filter(pet => 
        !rarityFilter || pet.rarity.toLowerCase() === rarityFilter
    );
    
    filteredPets.forEach(pet => {
        const card = createPetCard(pet);
        grid.appendChild(card);
    });
}

function createPetCard(pet) {
    const card = document.createElement('div');
    card.className = `item-card ${pet.rarity.toLowerCase()}`;
    card.onclick = () => showPetDetails(pet);
    
    card.innerHTML = `
        <div class="item-image">
            <img src="/static/images/pets/${pet.image}" alt="${pet.name}">
        </div>
        <div class="item-info">
            <h3>${pet.name}</h3>
            <p class="rarity ${pet.rarity.toLowerCase()}">${pet.rarity}</p>
            <div class="abilities-preview">
                ${pet.abilities.slice(0, 2).map(ability => 
                    `<span class="ability">${ability}</span>`
                ).join('')}
                ${pet.abilities.length > 2 ? '...' : ''}
            </div>
            ${pet.is_active ? '<div class="active-badge">Active</div>' : ''}
        </div>
    `;
    
    return card;
}

// Equipment Actions
async function equipMount(mountId) {
    try {
        const result = await api.post('/api/inventory/mount/equip', { mountId });
        if (result.success) {
            showSuccess(result.message);
            await loadInventory();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to equip mount');
    }
}

async function activatePet(petId) {
    try {
        const result = await api.post('/api/inventory/pet/activate', { petId });
        if (result.success) {
            showSuccess(result.message);
            await loadInventory();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to activate pet');
    }
}

async function repairItem(itemId) {
    try {
        const result = await api.post('/api/inventory/repair', { itemId });
        if (result.success) {
            showSuccess(result.message);
            await loadInventory();
            closeModal('item-details-modal');
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to repair item');
    }
}

// Inventory Management
async function expandInventory() {
    try {
        const result = await api.post('/api/inventory/expand');
        if (result.success) {
            showSuccess(result.message);
            await loadInventory();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to expand inventory');
    }
}

function updateInventoryStats() {
    const stats = currentInventory.stats;
    const progress = document.getElementById('inventory-progress');
    const slotsInfo = document.getElementById('slots-info');
    
    const usagePercent = (stats.slots_used / stats.slots_total) * 100;
    progress.style.width = `${usagePercent}%`;
    slotsInfo.textContent = `${stats.slots_used}/${stats.slots_total} slots`;
    
    // Update progress bar color based on usage
    if (usagePercent > 90) {
        progress.style.background = '#f44336';
    } else if (usagePercent > 70) {
        progress.style.background = '#ffc107';
    }
}

// Modal Management
function showItemDetails(item) {
    selectedItem = item;
    const modal = document.getElementById('item-details-modal');
    const details = document.getElementById('item-details');
    
    details.innerHTML = `
        <div class="item-details-content">
            <div class="item-image">
                <img src="/static/images/items/${item.type}/${item.image}" alt="${item.name}">
            </div>
            <h4>${item.name}</h4>
            <p class="rarity ${item.rarity.toLowerCase()}">${item.rarity}</p>
            <div class="stats-detail">
                ${Object.entries(item.stats).map(([key, value]) =>
                    `<div class="stat-row">
                        <span class="stat-name">${key}:</span>
                        <span class="stat-value">${value}</span>
                    </div>`
                ).join('')}
            </div>
            <div class="durability">
                Durability: ${item.durability}%
                <div class="durability-bar">
                    <div class="durability-fill ${getDurabilityClass(item.durability)}"
                         style="width: ${item.durability}%"></div>
                </div>
            </div>
        </div>
    `;
    
    // Update repair button state
    const repairBtn = document.getElementById('repair-btn');
    repairBtn.disabled = item.durability >= 100;
    
    modal.style.display = 'block';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(btn => 
                btn.classList.remove('active')
            );
            button.classList.add('active');
            
            document.querySelectorAll('.inventory-section').forEach(section => 
                section.classList.remove('active')
            );
            document.getElementById(`${button.dataset.target}-section`).classList.add('active');
            
            updateInventoryDisplay();
        });
    });
    
    // Filters
    document.querySelectorAll('.filters select').forEach(select => {
        select.addEventListener('change', updateInventoryDisplay);
    });
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

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}
