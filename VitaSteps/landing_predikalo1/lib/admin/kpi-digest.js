const path = require('path');
const { execFile } = require('child_process');

/**
 * Executes the weekly_business_digest.py script with given arguments.
 * @param {Array<string>} args 
 * @returns {Promise<{ stdout: string, stderr: string }>}
 */
function runDigestScript(args = []) {
    return new Promise((resolve, reject) => {
        const scriptPath = path.resolve(__dirname, '../../scripts/weekly_business_digest.py');
        const pythonCmd = process.env.PYTHON_PATH || (process.platform === 'win32' ? 'python' : 'python3');

        const options = {
            encoding: 'utf8',
            maxBuffer: 10 * 1024 * 1024,
            timeout: 60000,
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8'
            }
        };

        execFile(pythonCmd, [scriptPath, ...args], options, (error, stdout, stderr) => {
            if (error) {
                console.error('Error running weekly_business_digest.py:', error, stderr);
                return reject(new Error(stderr || error.message));
            }
            resolve({ stdout, stderr });
        });
    });
}

/**
 * Handles KPI digest actions:
 * - action === 'send_push' or 'send_kpi_push' -> triggers --push, sends Pushbullet
 * - default -> runs --json and returns parsed digest JSON
 *
 * @param {import('http').IncomingMessage} req 
 * @param {import('http').ServerResponse} res 
 */
async function handleKpiDigest(req, res) {
    const action = req.body?.action || req.query?.action;
    const days = req.body?.days || req.query?.days;

    try {
        if (action === 'send_push' || action === 'send_kpi_push') {
            const args = ['--push'];
            if (days && !isNaN(parseInt(days))) {
                args.push('--days', String(parseInt(days)));
            }
            const { stdout } = await runDigestScript(args);
            return res.status(200).json({
                success: true,
                message: 'Pushbullet értesítés sikeresen kiküldve!',
                output: stdout.trim()
            });
        }

        // Default: Fetch JSON digest
        const args = ['--json'];
        if (days && !isNaN(parseInt(days))) {
            args.push('--days', String(parseInt(days)));
        }

        const { stdout } = await runDigestScript(args);

        let digestData;
        try {
            digestData = JSON.parse(stdout);
        } catch (jsonErr) {
            console.error('Failed to parse digest JSON output:', stdout);
            return res.status(500).json({
                success: false,
                error: 'Nem sikerült feldolgozni a digest kimenetét (érvénytelen JSON)',
                rawOutput: stdout
            });
        }

        return res.status(200).json({
            success: true,
            digest: digestData
        });

    } catch (err) {
        console.error('handleKpiDigest error:', err);
        return res.status(500).json({
            success: false,
            error: err.message || 'Hiba történt a heti digest generálása közben'
        });
    }
}

module.exports = {
    runDigestScript,
    handleKpiDigest
};
