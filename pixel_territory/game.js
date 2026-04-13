import { RandomAgent, GreedyAgent, ScanAgent } from './agents.js';

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const statsPanel = document.getElementById('statsPanel');
const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');

const GRID_SIZE = 100;
const CELL_SIZE = canvas.width / GRID_SIZE;

let grid = [];
let players = [];
let animationId = null;
let isPaused = false;
let totalCells = GRID_SIZE * GRID_SIZE;

function init() {
    // Initialize empty grid
    grid = Array(GRID_SIZE).fill().map(() => Array(GRID_SIZE).fill(-1));

    // Define players with different strategies and colors
    players = [
        new RandomAgent(0, 5, 5, '#e74c3c', 'RED (Random)'),
        new GreedyAgent(1, 94, 5, '#3498db', 'BLUE (Greedy)'),
        new ScanAgent(2, 5, 94, '#2ecc71', 'GREEN (BFS)'),
        new ScanAgent(3, 94, 94, '#f1c40f', 'GOLD (Strategic)')
    ];

    // Place initial players on grid
    players.forEach(p => {
        grid[p.y][p.x] = p.id;
    });

    render();
    updateStats();
    isPaused = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
}

function update() {
    if (isPaused) return;

    let movesMade = 0;

    players.forEach(player => {
        if (player.isStuck) return;

        const move = player.getNextMove(grid, GRID_SIZE, GRID_SIZE);
        
        if (move) {
            const nx = player.x + move.dx;
            const ny = player.y + move.dy;

            const isCurrentEmpty = grid[ny][nx] === -1;

            // Move if empty OR if it's our own territory
            if (isCurrentEmpty || grid[ny][nx] === player.id) {
                if (isCurrentEmpty) {
                    grid[ny][nx] = player.id;
                    player.capturedCount++;
                }
                player.x = nx;
                player.y = ny;
                movesMade++;
            }
        } else {
            player.isStuck = true;
        }
    });

    // Termination condition: No empty cells left or nobody can make a move that leads to one
    // We'll simplify: stops if nobody made ANY move.
    if (movesMade === 0) {
        cancelAnimationFrame(animationId);
        startBtn.disabled = true;
        pauseBtn.disabled = true;
        alert("Simulation Finished!");
        return;
    }

    render();
    updateStats();
    animationId = requestAnimationFrame(() => {
        // Slow down the simulation for visibility
        setTimeout(update, 20); 
    });
}

function render() {
    // Clear background
    ctx.fillStyle = '#9bbc0f'; // GB Lightest
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid content
    for (let y = 0; y < GRID_SIZE; y++) {
        for (let x = 0; x < GRID_SIZE; x++) {
            const playerID = grid[y][x];
            if (playerID !== -1) {
                ctx.fillStyle = players[playerID].color;
                ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            }
        }
    }

    // Draw players (current position highlight)
    players.forEach(p => {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1;
        ctx.strokeRect(p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
    });
}

function updateStats() {
    statsPanel.innerHTML = players.map(p => {
        const percentage = ((p.capturedCount / totalCells) * 100).toFixed(1);
        return `
            <div class="stat-item">
                <span><span class="stat-color" style="background: ${p.color}"></span> ${p.name}</span>
                <span>${percentage}%</span>
            </div>
        `;
    }).join('');
}

startBtn.addEventListener('click', () => {
    isPaused = false;
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    update();
});

pauseBtn.addEventListener('click', () => {
    isPaused = !isPaused;
    pauseBtn.textContent = isPaused ? 'RESUME' : 'PAUSE';
});

resetBtn.addEventListener('click', () => {
    cancelAnimationFrame(animationId);
    init();
});

// Start the game
init();
