document.addEventListener('DOMContentLoaded', function() {
    // Particle System
    class ParticleSystem {
        constructor() {
            this.canvas = document.createElement('canvas');
            this.ctx = this.canvas.getContext('2d');
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.zIndex = '-1';
            this.canvas.style.opacity = '0.3';
            document.body.appendChild(this.canvas);

            this.particles = [];
            this.maxParticles = 100;

            window.addEventListener('resize', () => this.initParticles());
            this.initParticles();
            this.animate();
        }

        initParticles() {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
            this.particles = [];

            for (let i = 0; i < this.maxParticles; i++) {
                this.particles.push({
                    x: Math.random() * this.canvas.width,
                    y: Math.random() * this.canvas.height,
                    size: Math.random() * 2 + 1,
                    speedX: Math.random() * 2 - 1,
                    speedY: Math.random() * 2 - 1,
                    color: `rgba(0, ${Math.random() * 255}, ${Math.random() * 100}, 0.5)`
                });
            }
        }

        animate() {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

            this.particles.forEach(particle => {
                particle.x += particle.speedX;
                particle.y += particle.speedY;

                if (particle.x < 0 || particle.x > this.canvas.width) particle.speedX *= -1;
                if (particle.y < 0 || particle.y > this.canvas.height) particle.speedY *= -1;

                this.ctx.beginPath();
                this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.ctx.fillStyle = particle.color;
                this.ctx.fill();
            });

            requestAnimationFrame(() => this.animate());
        }
    }

    // Rank Animation
    class RankAnimation {
        constructor(elements) {
            this.elements = elements;
            this.init();
        }

        init() {
            this.elements.forEach(element => {
                const rank = element.textContent;
                const colors = this.getRankColors(rank);
                
                element.style.position = 'relative';
                element.style.overflow = 'hidden';

                const glow = document.createElement('div');
                glow.style.position = 'absolute';
                glow.style.top = '0';
                glow.style.left = '-100%';
                glow.style.width = '50%';
                glow.style.height = '100%';
                glow.style.background = `linear-gradient(to right, transparent, ${colors[0]}, transparent)`;
                glow.style.animation = 'rankGlow 2s infinite';
                element.appendChild(glow);
            });
        }

        getRankColors(rank) {
            const colors = {
                'E': ['#666666'],
                'D': ['#CD7F32'],
                'C': ['#C0C0C0'],
                'B': ['#FFD700'],
                'A': ['#00FF00'],
                'S': ['#FFD700', '#FFA500'],
                'SS': ['#FF00FF', '#800080'],
                'SSS': ['#FF0000', '#00FF00', '#0000FF']
            };
            return colors[rank] || ['#FFFFFF'];
        }
    }

    // Power Surge Effect
    class PowerSurgeEffect {
        constructor(elements) {
            this.elements = elements;
            this.init();
        }

        init() {
            this.elements.forEach(element => {
                element.addEventListener('mouseenter', () => {
                    const surge = document.createElement('div');
                    surge.className = 'power-surge-effect';
                    surge.style.position = 'absolute';
                    surge.style.top = '0';
                    surge.style.left = '0';
                    surge.style.width = '100%';
                    surge.style.height = '100%';
                    surge.style.background = 'radial-gradient(circle, rgba(0,255,65,0.2) 0%, transparent 70%)';
                    surge.style.animation = 'surgePulse 0.5s ease-out';
                    
                    element.style.position = 'relative';
                    element.appendChild(surge);
                    
                    surge.addEventListener('animationend', () => {
                        surge.remove();
                    });
                });
            });
        }
    }

    // Initialize Effects
    const particles = new ParticleSystem();
    
    const rankElements = document.querySelectorAll('.rank-badge');
    const rankAnimation = new RankAnimation(rankElements);

    const powerElements = document.querySelectorAll('.feature-card');
    const powerSurge = new PowerSurgeEffect(powerElements);

    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes rankGlow {
            0% { left: -100%; }
            100% { left: 200%; }
        }

        @keyframes surgePulse {
            0% { transform: scale(0.8); opacity: 1; }
            100% { transform: scale(1.5); opacity: 0; }
        }

        .feature-card:hover .feature-stats .stat-fill {
            animation: statFill 0.5s ease-out forwards;
        }

        @keyframes statFill {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
        }
    `;
    document.head.appendChild(style);
});
