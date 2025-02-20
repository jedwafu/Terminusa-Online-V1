document.addEventListener('DOMContentLoaded', function() {
    // Password requirements validation
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        const requirements = document.querySelectorAll('.requirement');
        
        passwordInput.addEventListener('input', function() {
            const value = this.value;
            
            // Check each requirement
            requirements.forEach(req => {
                const type = req.dataset.requirement;
                let isMet = false;
                
                switch(type) {
                    case 'length':
                        isMet = value.length >= 8;
                        break;
                    case 'uppercase':
                        isMet = /[A-Z]/.test(value);
                        break;
                    case 'number':
                        isMet = /[0-9]/.test(value);
                        break;
                    case 'special':
                        isMet = /[^A-Za-z0-9]/.test(value);
                        break;
                }
                
                if (isMet) {
                    req.classList.add('met');
                } else {
                    req.classList.remove('met');
                }
            });
        });
    }

    // Password confirmation validation
    const confirmPassword = document.getElementById('confirm_password');
    if (confirmPassword && passwordInput) {
        const validateMatch = () => {
            if (confirmPassword.value !== passwordInput.value) {
                confirmPassword.setCustomValidity('Passwords do not match');
            } else {
                confirmPassword.setCustomValidity('');
            }
        };

        passwordInput.addEventListener('input', validateMatch);
        confirmPassword.addEventListener('input', validateMatch);
    }

    // Clear flash messages on input
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                const messages = form.querySelectorAll('.alert');
                messages.forEach(msg => {
                    msg.classList.add('sliding-out');
                    setTimeout(() => msg.remove(), 300);
                });
            });
        });
    });

    // Add loading state to submit buttons
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const button = this.querySelector('button[type="submit"]');
            if (button) {
                button.classList.add('loading');
            }
        });
    });
});
