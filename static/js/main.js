document.addEventListener('DOMContentLoaded', function() {
    // Navigation highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Register form handling
    const registerButton = document.querySelector('a[href="/register"]');
    if (registerButton) {
        registerButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/register';
        });
    }

    // Login form handling
    const loginButton = document.querySelector('a[href="/login"]');
    if (loginButton) {
        loginButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/login';
        });
    }

    // Feature card hover effects
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.3s ease';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Check authentication status
    function checkAuth() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // User is logged in
            document.querySelectorAll('.cta-buttons').forEach(div => {
                div.innerHTML = `
                    <a href="/play" class="button primary">Play Now</a>
                    <a href="/logout" class="button secondary">Logout</a>
                `;
            });
        }
    }

    // Initialize
    checkAuth();

    // Handle logout
    document.addEventListener('click', function(e) {
        if (e.target.matches('a[href="/logout"]')) {
            e.preventDefault();
            localStorage.removeItem('auth_token');
            window.location.href = '/';
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading indicators
    function addLoadingIndicators() {
        const buttons = document.querySelectorAll('.button');
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                if (!this.classList.contains('loading')) {
                    const originalText = this.textContent;
                    this.classList.add('loading');
                    this.textContent = 'Loading...';
                    
                    // Reset after 2 seconds if no response
                    setTimeout(() => {
                        if (this.classList.contains('loading')) {
                            this.classList.remove('loading');
                            this.textContent = originalText;
                        }
                    }, 2000);
                }
            });
        });
    }

    // Initialize loading indicators
    addLoadingIndicators();

    // Error handling
    window.addEventListener('error', function(e) {
        console.error('Page Error:', e.message);
        // You could add user-friendly error notifications here
    });

    // Check if service worker is supported
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('ServiceWorker registration successful');
            })
            .catch(err => {
                console.log('ServiceWorker registration failed:', err);
            });
    }
});
