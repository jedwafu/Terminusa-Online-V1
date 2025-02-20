document.addEventListener('DOMContentLoaded', function() {
    // Login form handler
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.classList.add('loading');
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const remember = document.getElementById('remember').checked;
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ username, password, remember })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Store token
                    localStorage.setItem('token', data.token);
                    
                    // Show success message
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success';
                    successMessage.textContent = 'Login successful! Redirecting...';
                    loginForm.insertBefore(successMessage, loginForm.firstChild);
                    
                    // Redirect to game
                    setTimeout(() => {
                        window.location.href = data.redirect || '/play';
                    }, 1000);
                } else {
                    // Show error message
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'alert alert-error';
                    errorMessage.textContent = data.message || 'Login failed. Please try again.';
                    loginForm.insertBefore(errorMessage, loginForm.firstChild);
                    
                    // Remove loading state
                    submitButton.classList.remove('loading');
                }
            } catch (error) {
                console.error('Login error:', error);
                
                // Show error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'alert alert-error';
                errorMessage.textContent = 'Login failed. Please try again.';
                loginForm.insertBefore(errorMessage, loginForm.firstChild);
                
                // Remove loading state
                submitButton.classList.remove('loading');
            }
        });
    }
    
    // Register form handler
    const registerForm = document.querySelector('.register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.classList.add('loading');
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            if (password !== confirmPassword) {
                const errorMessage = document.createElement('div');
                errorMessage.className = 'alert alert-error';
                errorMessage.textContent = 'Passwords do not match!';
                registerForm.insertBefore(errorMessage, registerForm.firstChild);
                submitButton.classList.remove('loading');
                return;
            }
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Show success message
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success';
                    successMessage.textContent = 'Registration successful! Redirecting to login...';
                    registerForm.insertBefore(successMessage, registerForm.firstChild);
                    
                    // Redirect to login
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    // Show error message
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'alert alert-error';
                    errorMessage.textContent = data.message || 'Registration failed. Please try again.';
                    registerForm.insertBefore(errorMessage, registerForm.firstChild);
                    
                    // Remove loading state
                    submitButton.classList.remove('loading');
                }
            } catch (error) {
                console.error('Registration error:', error);
                
                // Show error message
                const errorMessage = document.createElement('div');
                errorMessage.className = 'alert alert-error';
                errorMessage.textContent = 'Registration failed. Please try again.';
                registerForm.insertBefore(errorMessage, registerForm.firstChild);
                
                // Remove loading state
                submitButton.classList.remove('loading');
            }
        });
    }
    
    // Clear messages when inputs change
    const forms = document.querySelectorAll('.login-form, .register-form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                const messages = form.querySelectorAll('.alert');
                messages.forEach(msg => msg.remove());
            });
        });
    });
});
