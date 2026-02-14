const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

// Start Python backend server
function startBackend() {
    const pythonScript = path.join(__dirname, '..', 'backend', 'app.py');

    console.log('Starting Python backend...');
    pythonProcess = spawn('python', [pythonScript], {
        cwd: path.join(__dirname, '..', 'backend')
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });

    // Wait for server to start
    return new Promise((resolve) => {
        setTimeout(resolve, 3000);
    });
}

// Create main application window
async function createWindow() {
    // Start backend first
    await startBackend();

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'icon.ico'),
        title: 'Smart Attendance - FER System',
        backgroundColor: '#0f172a'
    });

    // Load the frontend
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html'));

    // Open DevTools in development
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    // Kill backend process
    if (pythonProcess) {
        pythonProcess.kill();
    }

    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Clean up on quit
app.on('quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
