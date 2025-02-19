document.addEventListener('DOMContentLoaded', function() {
    // Matrix Rain Effect
    class MatrixRain {
        constructor() {
            this.canvas = document.createElement('canvas');
            this.ctx = this.canvas.getContext('2d');
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.zIndex = '-1';
            this.canvas.style.opacity = '0.05';
            document.body.appendChild(this.canvas);

            this.characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
            this.fontSize = 14;
            this.columns = 0;
            this.drops = [];

            window.addEventListener('resize', () => this.initRain());
            this.initRain();
            this.animate();
        }

        initRain() {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
            this.columns = Math.floor(this.canvas.width / this.fontSize);
            this.drops = [];
            for (let i = 0; i < this.columns; i++) {
                this.drops[i] = Math.random() * -100;
            }
        }

        animate() {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#00FF41';
            this.ctx.font = this.fontSize + 'px monospace';

            for (let i = 0; i < this.drops.length; i++) {
                const char = this.characters[Math.floor(Math.random() * this.characters.length)];
                this.ctx.fillText(char, i * this.fontSize, this.drops[i] * this.fontSize);
                if (this.drops[i] * this.fontSize > this.canvas.height && Math.random() > 0.975) {
                    this.drops[i] = 0;
                }
                this.drops[i]++;
            }
            requestAnimationFrame(() => this.animate());
        }
    }

    // Glitch Text Effect
    class GlitchText {
        constructor(elements) {
            this.elements = elements;
            this.chars = '!<>-_\\/[]{}—=+*^?#________';
            this.update();
        }

        update() {
            this.elements.forEach(element => {
                const originalText = element.getAttribute('data-text');
                if (!originalText) return;

                let iterations = 0;
                const maxIterations = 10;

                const interval = setInterval(() => {
                    element.innerText = originalText.split('')
                        .map((char, index) => {
                            if (index < iterations) return originalText[index];
                            return this.chars[Math.floor(Math.random() * this.chars.length)];
                        })
                        .join('');

                    iterations += 1/3;

                    if (iterations >= maxIterations) {
                        clearInterval(interval);
                        element.innerText = originalText;
                    }
                }, 30);
            });
        }
    }

    // Power Surge Effect
    class PowerSurge {
        constructor(elements) {
            this.elements = elements;
            this.init();
        }

        init() {
            this.elements.forEach(element => {
                element.addEventListener('mouseenter', () => {
                    element.style.transform = 'scale(1.05)';
                    element.style.boxShadow = '0 0 20px var(--matrix-green)';
                });

                element.addEventListener('mouseleave', () => {
                    element.style.transform = 'scale(1)';
                    element.style.boxShadow = 'none';
                });
            });
        }
    }

    // Initialize Effects
    const matrixRain = new MatrixRain();
    
    const glitchElements = document.querySelectorAll('.glitch');
    const glitchText = new GlitchText(glitchElements);
    setInterval(() => glitchText.update(), 5000);

    const powerElements = document.querySelectorAll('.energy-surge');
    const powerSurge = new PowerSurge(powerElements);

    // Typing Effect
    function typeWriter(element, text, speed = 50) {
        let i = 0;
        element.innerHTML = '';
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        type();
    }

    const typingElements = document.querySelectorAll('.typing-effect');
    typingElements.forEach(element => {
        const text = element.getAttribute('data-text') || element.textContent;
        element.textContent = '';
        typeWriter(element, text);
    });

    // Scan Line Effect
    const scanLine = document.createElement('div');
    scanLine.classList.add('scan-line-element');
    document.body.appendChild(scanLine);

    // Portal Effect
    function addPortalEffect(element) {
        element.addEventListener('mouseenter', () => {
            element.style.transform = 'scale(1.1) rotate(5deg)';
            element.style.filter = 'brightness(1.5)';
        });

        element.addEventListener('mouseleave', () => {
            element.style.transform = 'scale(1) rotate(0)';
            element.style.filter = 'brightness(1)';
        });
    }

    const portalElements = document.querySelectorAll('.portal-frame');
    portalElements.forEach(addPortalEffect);
});
