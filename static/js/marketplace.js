// Market Navigation
document.querySelectorAll('.nav-btn').forEach(button => {
    button.addEventListener('click', () => {
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        // Show corresponding section
        const target = button.dataset.target;
        document.querySelectorAll('.market-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${target}-market`).classList.add('active');

        // Load content based on section
        if (target === 'items') {
            loadItemListings();
        } else if (target === 'mounts') {
            loadMountListings();
        } else if (target === 'pets') {
            loadPetListings();
        } else if (target === 'my-listings') {
            loadMyListings();
        }
    });
});

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

// Listing Management
async function loadItemListings() {
    const filters = {
        itemType: document.getElementById('item-type').value,
        currency: document.getElementById('currency-type').value,
        minPrice: document.getElementById('min-price').value,
        maxPrice: document.getElementById('max-price').value
    };

    try {
        const listings = await api.get('/api/marketplace/listings?' + new URLSearchParams(filters));
        renderListings(listings, 'items-grid');
    } catch (error) {
        showError('Failed to load listings');
    }
}

async function loadMountListings() {
    try {
        const listings = await api.get('/api/marketplace/mounts');
        renderListings(listings, 'mounts-grid');
    } catch (error) {
        showError('Failed to load mount listings');
    }
}

async function loadPetListings() {
    try {
        const listings = await api.get('/api/marketplace/pets');
        renderListings(listings, 'pets-grid');
    } catch (error) {
        showError('Failed to load pet listings');
    }
}

async function loadMyListings() {
    try {
        const listings = await api.get('/api/marketplace/my-listings');
        renderMyListings(listings);
    } catch (error) {
        showError('Failed to load your listings');
    }
}

// Rendering Functions
function renderListings(listings, gridId) {
    const grid = document.getElementById(gridId);
    grid.innerHTML = '';
    
    listings.forEach(listing => {
        const card = createListingCard(listing);
        grid.appendChild(card);
    });
}

function createListingCard(listing) {
    const card = document.createElement('div');
    card.className = 'listing-card';
    
    const content = `
        <div class="item-image">
            <img src="/static/images/${listing.type.toLowerCase()}/${listing.image}" alt="${listing.name}">
        </div>
        <div class="item-info">
            <h3>${listing.name}</h3>
            <p class="rarity ${listing.rarity.toLowerCase()}">${listing.rarity}</p>
            ${listing.level_requirement ? `<p>Level Req: ${listing.level_requirement}</p>` : ''}
            ${listing.stats ? createStatsDisplay(listing.stats) : ''}
            ${listing.abilities ? createAbilitiesDisplay(listing.abilities) : ''}
            <div class="price">
                <img src="/static/images/currency/${listing.currency}.png" alt="${listing.currency}">
                <span>${listing.price.toLocaleString()}</span>
            </div>
        </div>
        <button onclick="purchaseListing(${listing.id})" class="purchase-btn">Purchase</button>
    `;
    
    card.innerHTML = content;
    return card;
}

function createStatsDisplay(stats) {
    return `
        <div class="stats">
            ${Object.entries(stats).map(([key, value]) => 
                `<div class="stat">${key}: ${value}</div>`
            ).join('')}
        </div>
    `;
}

function createAbilitiesDisplay(abilities) {
    return `
        <div class="abilities">
            ${abilities.map(ability => 
                `<div class="ability" data-tooltip="${getAbilityDescription(ability)}">${ability}</div>`
            ).join('')}
        </div>
    `;
}

// Gacha System
async function rollGacha(type, amount) {
    try {
        const result = await api.post('/api/gacha/roll', { type, amount });
        if (result.success) {
            showGachaResults(result.results);
            updateCurrencyDisplay();
            updatePityInfo();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to process gacha roll');
    }
}

function showGachaResults(results) {
    const modal = document.getElementById('gacha-result-modal');
    const resultsDiv = document.getElementById('gacha-results');
    resultsDiv.innerHTML = '';

    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.className = `gacha-result ${result.rarity.toLowerCase()}`;
        resultElement.innerHTML = `
            <div class="result-image">
                <img src="/static/images/${result.type.toLowerCase()}/${result.image}" alt="${result.name}">
            </div>
            <h4>${result.name}</h4>
            <p class="rarity">${result.rarity}</p>
            ${result.stats ? createStatsDisplay(result.stats) : ''}
            ${result.abilities ? createAbilitiesDisplay(result.abilities) : ''}
        `;
        resultsDiv.appendChild(resultElement);
    });

    modal.style.display = 'block';
}

// Transaction Functions
async function purchaseListing(listingId) {
    try {
        const result = await api.post('/api/marketplace/purchase', { listingId });
        if (result.success) {
            showSuccess('Purchase successful!');
            updateCurrencyDisplay();
            loadItemListings();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to complete purchase');
    }
}

async function createListing(formData) {
    try {
        const result = await api.post('/api/marketplace/create', formData);
        if (result.success) {
            showSuccess('Listing created successfully!');
            closeModal('create-listing-modal');
            loadMyListings();
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('Failed to create listing');
    }
}

// UI Updates
async function updateCurrencyDisplay() {
    try {
        const currency = await api.get('/api/user/currency');
        document.querySelector('.solana span').textContent = currency.solana_balance.toLocaleString();
        document.querySelector('.exons span').textContent = currency.exons_balance.toLocaleString();
        document.querySelector('.crystals span').textContent = currency.crystals.toLocaleString();
    } catch (error) {
        console.error('Error updating currency display');
    }
}

async function updatePityInfo() {
    try {
        const pityInfo = await api.get('/api/gacha/pity');
        updatePityDisplay(pityInfo);
    } catch (error) {
        console.error('Error updating pity info');
    }
}

// Utility Functions
function updatePityDisplay(pityInfo) {
    const mountPity = document.querySelector('.pity-mount');
    const petPity = document.querySelector('.pity-pet');
    
    mountPity.innerHTML = `
        <p>Mount Rolls until:</p>
        <div>Legendary: ${pityInfo.mount_pity.rolls_until_legendary}</div>
        <div>Immortal: ${pityInfo.mount_pity.rolls_until_immortal}</div>
    `;
    
    petPity.innerHTML = `
        <p>Pet Rolls until:</p>
        <div>Legendary: ${pityInfo.pet_pity.rolls_until_legendary}</div>
        <div>Immortal: ${pityInfo.pet_pity.rolls_until_immortal}</div>
    `;
}

function getAbilityDescription(ability) {
    const descriptions = {
        'Item Finder': 'Increases chance of finding rare items',
        'Combat Support': 'Provides combat bonuses during battles',
        'Stat Boost': 'Temporarily enhances player stats',
        'Special Skill': 'Unique ability based on pet type',
        'Unique Ability': 'Powerful ability unique to this pet'
    };
    return descriptions[ability] || ability;
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

// Modal Controls
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadItemListings();
    updateCurrencyDisplay();
    updatePityInfo();
    
    // Setup filter change handlers
    document.querySelectorAll('.filters select, .filters input').forEach(element => {
        element.addEventListener('change', () => {
            const activeSection = document.querySelector('.market-section.active');
            if (activeSection.id === 'items-market') {
                loadItemListings();
            }
        });
    });
});
