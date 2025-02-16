// Authentication state management
class Auth {
    static getToken() {
        return localStorage.getItem('auth_token');
    }

    static getUserData() {
        const data = localStorage.getItem('user_data');
        return data ? JSON.parse(data) : null;
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static setAuth(token, userData) {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(userData));
        this.updateUI();
    }

    static logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/';
    }

    static updateUI() {
        const isAuth = this.isAuthenticated();
        const userData = this.getUserData();

        document.querySelectorAll('.logged-out').forEach(el => {
            el.style.display = isAuth ? 'none' : 'inline-block';
        });

        document.querySelectorAll('.logged-in').forEach(el => {
            el.style.display = isAuth ? 'inline-block' : 'none';
        });

        document.querySelectorAll('.username').forEach(el => {
            el.textContent = userData ? userData.username : '';
        });

        // Handle protected routes
        const authRequired = document.querySelector('.auth-required');
        if (authRequired && !isAuth && 
            window.location.pathname !== '/login' && 
            window.location.pathname !== '/register') {
            window.location.href = '/login';
        }
    }
}

// API client with authentication
class ApiClient {
    static async fetch(url, options = {}) {
        const token = Auth.getToken();
        if (token) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }
        
        try {
            const response = await fetch(url, options);
            const data = await response.json();

            if (response.status === 401) {
                Auth.logout();
                return null;
            }

            return { response, data };
        } catch (error) {
            console.error('API Error:', error);
            return { error };
        }
    }
}

// Navigation highlighting
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Feature card hover effects
function initFeatureCards() {
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Form validation
function validateForm(formData) {
    const errors = [];

    if (formData.password && formData.password.length < 8) {
        errors.push('Password must be at least 8 characters long');
    }

    if (formData.email && !formData.email.includes('@')) {
        errors.push('Invalid email address');
    }

    return errors;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    Auth.updateUI();
    highlightCurrentPage();
    initFeatureCards();

    // Global logout handler
    document.querySelectorAll('[onclick="logout()"]').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            Auth.logout();
        });
    });
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('Page Error:', e.message);
    // You could add user-friendly error notifications here
});

// Export for use in other scripts
window.Auth = Auth;
window.ApiClient = ApiClient;
