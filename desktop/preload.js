// Preload script for Electron security bridge
const { contextBridge } = require('electron');

// Expose safe APIs to renderer process
contextBridge.exposeInMainWorld('electron', {
    platform: process.platform,
    versions: process.versions
});
