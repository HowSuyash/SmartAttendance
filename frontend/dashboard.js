/**
 * Dashboard JavaScript for Smart Attendance FER System
 * Displays historical data and engagement trends
 */

const API_URL = 'https://smartattendance-tnmh.onrender.com';

// State
let trendsChartInstance = null;

// Load dashboard on page load
window.addEventListener('load', async () => {
    await loadDashboard();
});

/**
 * Load dashboard data
 */
async function loadDashboard() {
    const loadingState = document.getElementById('loadingState');
    const dashboardContent = document.getElementById('dashboardContent');
    const errorState = document.getElementById('errorState');
    const noDataState = document.getElementById('noDataState');

    try {
        // Show loading
        loadingState.style.display = 'flex';
        dashboardContent.style.display = 'none';
        errorState.style.display = 'none';

        // Fetch dashboard stats
        const response = await fetch(`${API_URL}/dashboard/stats?days=7`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Dashboard API error:', response.status, errorText);
            throw new Error(`Server error (${response.status}). Please ensure the backend is running.`);
        }

        const data = await response.json();
        console.log('Dashboard data received:', data);

        // Hide loading
        loadingState.style.display = 'none';

        // Check if we have data
        if (!data.recent_sessions || data.recent_sessions.length === 0) {
            noDataState.style.display = 'flex';
            dashboardContent.style.display = 'block'; // Still show the content area
            return;
        }

        // Display dashboard
        dashboardContent.style.display = 'block';

        // Display recent sessions
        displayRecentSessions(data.recent_sessions);

        // Display trends
        displayTrends(data.trends || {});

    } catch (error) {
        console.error('Dashboard error:', error);
        loadingState.style.display = 'none';
        errorState.style.display = 'flex';

        // Provide helpful error message
        const errorMessage = document.getElementById('errorMessage');
        if (error.message.includes('Failed to fetch')) {
            errorMessage.textContent = 'Cannot connect to the backend server. Please make sure it is running on http://localhost:5001';
        } else {
            errorMessage.textContent = error.message || 'An unexpected error occurred';
        }
    }
}

/**
 * Display recent sessions
 */
function displayRecentSessions(sessions) {
    const container = document.getElementById('recentSessions');
    container.innerHTML = '';

    if (sessions.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-muted); grid-column: 1/-1;">No sessions yet</p>';
        return;
    }

    sessions.forEach((session, index) => {
        const sessionCard = document.createElement('div');
        sessionCard.className = 'session-card glass-card';
        sessionCard.style.animationDelay = `${index * 0.1}s`;

        // Handle different timestamp formats defensively
        let timestamp = 'Unknown date';
        try {
            if (session.timestamp) {
                if (session.timestamp._seconds) {
                    // Firestore timestamp format
                    timestamp = new Date(session.timestamp._seconds * 1000).toLocaleString();
                } else if (session.timestamp.seconds) {
                    // Alternative Firestore format
                    timestamp = new Date(session.timestamp.seconds * 1000).toLocaleString();
                } else if (typeof session.timestamp === 'string') {
                    // ISO string format
                    timestamp = new Date(session.timestamp).toLocaleString();
                } else if (session.timestamp instanceof Date) {
                    // Already a Date object
                    timestamp = session.timestamp.toLocaleString();
                }
            }
        } catch (error) {
            console.warn('Error parsing timestamp for session:', session.id, error);
        }

        const stats = session.statistics || {};

        sessionCard.innerHTML = `
            <div class="session-header">
                <h4 class="session-title">${session.class_name || 'Unknown Class'}</h4>
                <span class="session-status ${session.status || 'unknown'}">${session.status || 'unknown'}</span>
            </div>
            <div class="session-meta">
                <span class="session-time">📅 ${timestamp}</span>
                <span class="session-image">📎 ${session.image_name || 'N/A'}</span>
            </div>
            ${session.status === 'completed' ? `
                <div class="session-stats">
                    <div class="mini-stat">
                        <span class="mini-stat-label">Total</span>
                        <span class="mini-stat-value">${stats.total_faces || 0}</span>
                    </div>
                    <div class="mini-stat success">
                        <span class="mini-stat-label">Engaged</span>
                        <span class="mini-stat-value">${stats.engaged_count || 0}</span>
                    </div>
                    <div class="mini-stat danger">
                        <span class="mini-stat-label">Disengaged</span>
                        <span class="mini-stat-value">${stats.disengaged_count || 0}</span>
                    </div>
                </div>
                <div class="engagement-bar">
                    <div class="engagement-bar-fill" style="width: ${stats.engagement_percentage || 0}%"></div>
                </div>
                <p class="engagement-text">${(stats.engagement_percentage || 0).toFixed(1)}% Engagement Rate</p>
            ` : '<p style="color: var(--text-muted); font-size: 0.9rem;">Processing...</p>'}
        `;

        container.appendChild(sessionCard);
    });
}

/**
 * Display engagement trends
 */
function displayTrends(trends) {
    const ctx = document.getElementById('trendsChart').getContext('2d');

    // Destroy previous chart if exists
    if (trendsChartInstance) {
        trendsChartInstance.destroy();
    }

    // Check if we have trend data
    if (Object.keys(trends).length === 0) {
        ctx.canvas.parentElement.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No trend data available yet</p>';
        return;
    }

    // Prepare data
    const dates = Object.keys(trends).sort();
    const engagedData = dates.map(date => trends[date].engaged);
    const disengagedData = dates.map(date => trends[date].disengaged);
    const totalData = dates.map(date => trends[date].total_faces);

    // Format dates for display
    const labels = dates.map(date => {
        const d = new Date(date);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    trendsChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Engaged',
                    data: engagedData,
                    borderColor: 'hsl(155, 70%, 50%)',  // Emerald Green
                    backgroundColor: 'hsla(155, 70%, 50%, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Disengaged',
                    data: disengagedData,
                    borderColor: 'hsl(350, 85%, 60%)', // Rose
                    backgroundColor: 'hsla(350, 85%, 60%, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Total Students',
                    data: totalData,
                    borderColor: 'hsl(190, 85%, 55%)',  // Bright Cyan (Ocean Blue)
                    backgroundColor: 'hsla(190, 85%, 55%, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Changed from true to false
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff', // Changed from #e5e7eb to #ffffff
                        font: {
                            size: 14,
                            family: 'Inter'
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 16,
                        family: 'Inter'
                    },
                    bodyFont: {
                        size: 14,
                        family: 'Inter'
                    },
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#9ca3af',
                        font: {
                            family: 'Inter'
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#9ca3af',
                        font: {
                            family: 'Inter'
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                }
            }
        }
    });
}
