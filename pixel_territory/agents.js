export class Agent {
    constructor(id, x, y, color, name) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.color = color;
        this.name = name;
        this.capturedCount = 1;
        this.isStuck = false;
    }

    getNextMove(grid, width, height) {
        // To be implemented by subclasses
        return null;
    }

    getValidMoves(grid, width, height) {
        const moves = [
            { dx: 0, dy: -1 }, // Up
            { dx: 0, dy: 1 },  // Down
            { dx: -1, dy: 0 }, // Left
            { dx: 1, dy: 0 }   // Right
        ];

        return moves.filter(move => {
            const nx = this.x + move.dx;
            const ny = this.y + move.dy;
            // Valid if it's within bounds AND (it's empty OR it's our own color)
            return nx >= 0 && nx < width && ny >= 0 && ny < height && 
                   (grid[ny][nx] === -1 || grid[ny][nx] === this.id);
        });
    }

    findNearestEmpty(grid, width, height, validMoves) {
        if (validMoves.length === 0) return null;
        
        const visited = new Set();
        const queue = [];
        
        for (const move of validMoves) {
            const nx = this.x + move.dx;
            const ny = this.y + move.dy;
            queue.push({x: nx, y: ny, firstMove: move, dist: 1});
            visited.add(`${nx},${ny}`);
        }

        const maxScan = 500; 
        let scanned = 0;

        while (queue.length > 0 && scanned < maxScan) {
            const current = queue.shift();
            scanned++;

            const neighbors = [
                {x: current.x, y: current.y-1}, {x: current.x, y: current.y+1}, 
                {x: current.x-1, y: current.y}, {x: current.x+1, y: current.y}
            ];

            for (const n of neighbors) {
                if (n.x >= 0 && n.x < width && n.y >= 0 && n.y < height) {
                    if (grid[n.y][n.x] === -1) {
                        return current.firstMove;
                    }
                    const key = `${n.x},${n.y}`;
                    if (grid[n.y][n.x] === this.id && !visited.has(key)) {
                        visited.add(key);
                        queue.push({...n, firstMove: current.firstMove, dist: current.dist + 1});
                    }
                }
            }
        }
        return validMoves[Math.floor(Math.random() * validMoves.length)];
    }
}

export class RandomAgent extends Agent {
    getNextMove(grid, width, height) {
        const validMoves = this.getValidMoves(grid, width, height);
        if (validMoves.length === 0) return null;
        
        // Prioritize empty cells over own territory
        const emptyMoves = validMoves.filter(m => grid[this.y + m.dy][this.x + m.dx] === -1);
        if (emptyMoves.length > 0) {
            return emptyMoves[Math.floor(Math.random() * emptyMoves.length)];
        }
        
        return validMoves[Math.floor(Math.random() * validMoves.length)];
    }
}

export class GreedyAgent extends Agent {
    getNextMove(grid, width, height) {
        const validMoves = this.getValidMoves(grid, width, height);
        if (validMoves.length === 0) return null;

        // In a simple grid, greedy is just choosing a move that leads to more space.
        // For a 100x100 grid, finding the "nearest" empty cell globally is expensive every frame,
        // so we just pick a move that has the most empty neighbors.
        let bestMove = validMoves[0];
        let maxEmptyNeighbors = -1;

        for (const move of validMoves) {
            const nx = this.x + move.dx;
            const ny = this.y + move.dy;
            let emptyCount = 0;
            
            // Check neighbors of the potential new position
            const neighbors = [
                {x: nx, y: ny-1}, {x: nx, y: ny+1}, {x: nx-1, y: ny}, {x: nx+1, y: ny}
            ];

            for (const n of neighbors) {
                if (n.x >= 0 && n.x < width && n.y >= 0 && n.y < height && grid[n.y][n.x] === -1) {
                    emptyCount++;
                }
            }
            if (emptyCount > maxEmptyNeighbors) {
                maxEmptyNeighbors = emptyCount;
                bestMove = move;
            }
        }

        // If multiple moves have the same max empty neighbors, 
        // and we are on our own territory, prioritize moves that lead to empty space
        if (maxEmptyNeighbors <= 0) {
            return this.findNearestEmpty(grid, width, height, validMoves);
        }

        return bestMove;
    }
}

export class ScanAgent extends Agent {
    // This agent performs a BFS to find the largest reachable area
    getNextMove(grid, width, height) {
        const validMoves = this.getValidMoves(grid, width, height);
        if (validMoves.length === 0) return null;

        let bestMove = validMoves[0];
        let maxArea = -1;

        for (const move of validMoves) {
            const nx = this.x + move.dx;
            const ny = this.y + move.dy;
            
            const area = this.calculateArea(grid, nx, ny, width, height);
            if (area > maxArea) {
                maxArea = area;
                bestMove = move;
            }
        }

        if (maxArea <= 0) {
            return this.findNearestEmpty(grid, width, height, validMoves);
        }

        return bestMove;
    }

    calculateArea(grid, startX, startY, width, height) {
        // Simple BFS to count reachable empty cells
        // Limited depth to keep performance high
        const visited = new Set();
        const queue = [[startX, startY]];
        visited.add(`${startX},${startY}`);
        let count = 0;
        const maxDepth = 200; // Limit search to avoid lag

        while (queue.length > 0 && count < maxDepth) {
            const [x, y] = queue.shift();
            count++;

            const neighbors = [
                [x, y-1], [x, y+1], [x-1, y], [x+1, y]
            ];

            for (const [nx, ny] of neighbors) {
                const key = `${nx},${ny}`;
                // Passable if empty OR own territory
                if (nx >= 0 && nx < width && ny >= 0 && ny < height && 
                    (grid[ny][nx] === -1 || grid[ny][nx] === this.id) && !visited.has(key)) {
                    visited.add(key);
                    queue.push([nx, ny]);
                }
            }
        }
        return count;
    }
}
