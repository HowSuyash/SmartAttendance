/**
 * JavaScript for Smart Attendance FER System
 * Handles image upload, API communication, and results display
 */

const API_URL = 'http://localhost:8000';

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const className = document.getElementById('className');
const analyzeBtn = document.getElementById('analyzeBtn');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const removeImageBtn = document.getElementById('removeImageBtn');
const resultsSection = document.getElementById('resultsSection');

// State
let selectedFile = null;
let emotionChartInstance = null;

// ===== Event Listeners =====

// Browse button click
browseBtn.addEventListener('click', () => {
    fileInput.click();
});

// Drop zone click
dropZone.addEventListener('click', (e) => {
    if (e.target === dropZone || e.target.closest('.drop-zone-content')) {
        fileInput.click();
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFileSelect(file);
    } else {
        alert('Please drop a valid image file (PNG, JPG, JPEG)');
    }
});

// Remove image button
removeImageBtn.addEventListener('click', () => {
    resetUpload();
});

// Analyze button
analyzeBtn.addEventListener('click', () => {
    if (selectedFile) {
        analyzeImage();
    }
});

// ===== Functions =====

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
    }

    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        alert('File size must be less than 16MB');
        return;
    }

    selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        previewSection.style.display = 'block';
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

/**
 * Reset upload state
 */
function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    previewSection.style.display = 'none';
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';
}

/**
 * Analyze image
 */
async function analyzeImage() {
    if (!selectedFile) return;

    // Show loading state
    analyzeBtn.classList.add('loading');
    analyzeBtn.disabled = true;

    // Hide previous results
    resultsSection.style.display = 'none';

    try {
        // Create form data
        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('class_name', className.value || 'Unknown Class');

        console.log('🚀 Sending request to:', `${API_URL}/upload`);

        // Send to API
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        console.log('📥 Response status:', response.status);
        console.log('📥 Response headers:', response.headers);

        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Error response:', error);
            throw new Error(error.error || 'Analysis failed');
        }

        const data = await response.json();
        console.log('✅ Success! Response data:', data);

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('💥 Analysis error:', error);
        console.error('Error stack:', error.stack);
        alert(`Analysis failed: ${error.message}\n\nMake sure:\n1. Backend server is running\n2. Hugging Face API token is configured\n3. Firebase credentials are set up`);
    } finally {
        // Remove loading state
        analyzeBtn.classList.remove('loading');
        analyzeBtn.disabled = false;
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    const { faces, statistics, annotated_image } = data;

    // Update statistics cards
    document.getElementById('totalFaces').textContent = statistics.total_faces;
    document.getElementById('engagedCount').textContent = statistics.engaged_count;
    document.getElementById('disengagedCount').textContent = statistics.disengaged_count;
    document.getElementById('engagementPercent').textContent =
        statistics.engagement_percentage.toFixed(1) + '%';

    // Display annotated image
    if (annotated_image) {
        const annotatedImg = document.getElementById('annotatedImage');
        annotatedImg.src = `${API_URL}/image/${annotated_image}`;
    }

    // Display individual faces
    displayFaces(faces);

    // Display emotion chart
    displayEmotionChart(statistics.emotion_distribution);

    // Show results section
    resultsSection.style.display = 'block';

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

/**
 * Display individual faces
 */
function displayFaces(faces) {
    const facesGrid = document.getElementById('facesGrid');
    facesGrid.innerHTML = '';

    if (faces.length === 0) {
        facesGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No faces detected</p>';
        return;
    }

    faces.forEach((face, index) => {
        const faceCard = document.createElement('div');
        faceCard.className = 'face-card glass-card';
        faceCard.style.animationDelay = `${index * 0.1}s`;

        const emotionEmoji = getEmotionEmoji(face.emotion);
        const engagementClass = face.engagement_level === 'engaged' ? 'engaged' : 'disengaged';
        const impression = getEngagementImpression(face.emotion, face.engagement_level, face.emotion_score);

        faceCard.innerHTML = `
            <div class="face-info">
                <div style="font-size: 0.9rem; font-weight: 600; color: var(--primary); margin-bottom: 0.5rem;">
                    Student ${index + 1}
                </div>
                <div style="font-size: 4rem; margin-bottom: 0.5rem;">${emotionEmoji}</div>
                <div class="emotion-label">${face.emotion}</div>
                <div class="engagement-badge ${engagementClass}">
                    ${face.engagement_level}
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.75rem; padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: var(--radius-md); line-height: 1.4;">
                    ${impression}
                </div>
            </div>
        `;

        facesGrid.appendChild(faceCard);
    });
}

/**
 * Get emoji for emotion
 */
function getEmotionEmoji(emotion) {
    const emojiMap = {
        'happy': '😊',
        'sad': '😢',
        'angry': '😠',
        'surprise': '😲',
        'fear': '😨',
        'disgust': '🤢',
        'neutral': '😐',
        'error': '❌',
        'unknown': '❓'
    };
    return emojiMap[emotion] || '😐';
}

/**
 * Get engagement impression text based on emotion
 */
function getEngagementImpression(emotion, engagementLevel, score) {
    const impressions = {
        'happy': {
            'engaged': 'Showing positive engagement and enthusiasm for the lesson',
            'disengaged': 'Happy but may need focus redirection'
        },
        'neutral': {
            'engaged': 'Calm and focused, actively listening',
            'disengaged': 'Passive, may benefit from interactive activities'
        },
        'surprise': {
            'engaged': 'Highly attentive and curious about the content',
            'disengaged': 'Surprised, possibly confused'
        },
        'sad': {
            'engaged': 'Serious focus, though may need encouragement',
            'disengaged': 'Appears disengaged or struggling with content'
        },
        'angry': {
            'engaged': 'Intense concentration, possibly frustrated with difficulty',
            'disengaged': 'Frustrated or resistant, needs intervention'
        },
        'fear': {
            'engaged': 'Anxious but trying to follow along',
            'disengaged': 'Overwhelmed or intimidated by the material'
        },
        'disgust': {
            'engaged': 'Critical thinking, evaluating content',
            'disengaged': 'Disinterested or disapproving of current topic'
        }
    };

    const defaultImpression = engagementLevel === 'engaged'
        ? 'Student appears to be engaged in the lesson'
        : 'Student may need attention or clarification';

    return impressions[emotion]?.[engagementLevel] || defaultImpression;
}

/**
 * Display emotion distribution chart
 */
function displayEmotionChart(emotionDistribution) {
    const ctx = document.getElementById('emotionChart').getContext('2d');

    // Destroy previous chart if exists
    if (emotionChartInstance) {
        emotionChartInstance.destroy();
    }

    const labels = Object.keys(emotionDistribution);
    const data = Object.values(emotionDistribution);

    // Ocean Blue & Emerald theme colors for different emotions
    const backgroundColors = [
        'hsla(210, 85%, 45%, 0.8)',  // Deep Ocean Blue
        'hsla(190, 85%, 55%, 0.8)',  // Bright Cyan
        'hsla(155, 70%, 50%, 0.8)',  // Emerald Green
        'hsla(165, 75%, 55%, 0.8)',  // Light Emerald
        'hsla(200, 80%, 50%, 0.8)',  // Sky Blue
        'hsla(180, 70%, 45%, 0.8)',  // Turquoise
        'hsla(220, 80%, 55%, 0.8)',  // Bright Blue
    ];

    emotionChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(e => e.charAt(0).toUpperCase() + e.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#1a1a2e'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true, // Changed from false to true to match original behavior
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#ffffff',
                        padding: 15,
                        font: { size: 12, family: 'Inter' } // Added font family to match original
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
            }
        }
    });
}

// ===== Health Check on Load =====
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            console.log('✅ Backend server is running');
        }
    } catch (error) {
        console.warn('⚠️ Backend server is not reachable. Please start the server.');
    }
});
