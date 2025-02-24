const canvas = document.getElementById('matrixRain');
const ctx = canvas.getContext('2d');

let width = window.innerWidth;
let height = window.innerHeight;
const fontSize = 16;
const columns = width / fontSize;
const matrix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%";
const drops = [];

// Initialize drops
for(let x = 0; x < columns; x++) {
    drops[x] = Math.floor(Math.random() * height);
}

function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
}

function draw() {
    // Semi-transparent background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
    ctx.fillRect(0, 0, width, height);

    // Set text style
    ctx.fillStyle = '#00FF41';
    ctx.font = `${fontSize}px monospace`;

    // Draw characters
    for(let i = 0; i < drops.length; i++) {
        const text = matrix[Math.floor(Math.random() * matrix.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        // Reset drops that reach the bottom
        if(drops[i] * fontSize > height && Math.random() > 0.975) {
            drops[i] = 0;
        }

        drops[i]++;
    }
}

// Initialize
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Start animation
setInterval(draw, 35);
