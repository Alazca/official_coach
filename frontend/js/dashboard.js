/**
 * dashboard.js - Main JavaScript for the COACH dashboard
 * Handles dashboard initialization, chart rendering, and UI interactions
 */

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard scripts loaded');
    
    // Initialize dashboard components
    initializeReadinessChart();
    initializeChatControls();
    initializeEventListeners();
});
/**
 * Initialize readiness chart with user data
 * Displays a line chart showing readiness scores over time
 */
function initializeReadinessChart() {
    // Get the chart canvas element
    const ctx = document.getElementById('readinessChart');
    if (!ctx) return;

    // Get stored check-in data
    const checkIns = JSON.parse(localStorage.getItem('checkIns') || '[]');
    
    // Get the last 7 days of data
    const last7Days = checkIns
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(-7);

    // Create the chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: last7Days.map(day => new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })),
            datasets: [{
                label: 'Readiness Score',
                data: last7Days.map(day => day.readiness || 0),
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#9CA3AF' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: { 
                        color: '#9CA3AF',
                        callback: value => `${value}%`
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
}

/**
 * Initialize chat interface controls
 * Handles minimizing/maximizing the chat window
 */
function initializeChatControls() {
    const trainerChat = document.getElementById('trainerChat');
    const chatContent = document.getElementById('chatContent');
    const chatBubble = document.getElementById('chatBubble');
    const minimizeButton = document.getElementById('minimizeChat');

    // No operation if elements don't exist
    if (!trainerChat || !chatContent || !chatBubble || !minimizeButton) {
        return;
    }

    // Save chat state in localStorage
    const saveState = (isMinimized) => {
        localStorage.setItem('chat_minimized', isMinimized);
    };

    // Load saved state
    const loadState = () => {
        return localStorage.getItem('chat_minimized') === 'true';
    };

    // Function to minimize the chat
    const minimizeChat = () => {
        chatContent.style.display = 'none';
        trainerChat.style.display = 'none';
        chatBubble.classList.remove('hidden');
        saveState(true);
    };

    // Function to maximize the chat
    const maximizeChat = () => {
        trainerChat.style.display = 'block';
        chatContent.style.display = 'block';
        chatBubble.classList.add('hidden');
        saveState(false);
    };

    // Set initial state based on localStorage
    if (loadState()) {
        minimizeChat();
    }

    // Add event listeners
    minimizeButton.addEventListener('click', minimizeChat);
    chatBubble.addEventListener('click', maximizeChat);
}

/**
 * Initialize event listeners for dashboard elements
 */
function initializeEventListeners() {
    // Sign Up button
    const signUpButton = document.getElementById('signUpButton');
    if (signUpButton) {
        signUpButton.addEventListener('click', function() {
            // Navigate to signup page or show signup modal
            // This would be integrated with your authentication system
            console.log('Sign Up clicked');
            // Example: window.location.href = 'signup.html';
        });
    }

    // Check-in button
    const checkInButton = document.getElementById('checkInButton');
    if (checkInButton) {
        checkInButton.addEventListener('click', function() {
            console.log('Daily Check-In clicked');
            // Navigate to check-in page or open check-in modal
            // Example: window.location.href = 'checkin.html';
        });
    }

    // Workout tile
    const workoutTile = document.getElementById('workoutTile');
    if (workoutTile) {
        workoutTile.addEventListener('click', function() {
            console.log('Workout of the Day clicked');
            // Navigate to workout page
            // Example: window.location.href = 'workout.html';
        });
    }

    // Visualize data tile
    const visualizeTile = document.getElementById('visualizeTile');
    if (visualizeTile) {
        visualizeTile.addEventListener('click', function() {
            console.log('Visualize Data clicked');
            // Navigate to data visualization page
            // Example: window.location.href = 'visualize.html';
        });
    }

    // Log food tile
    const logFoodTile = document.getElementById('logFoodTile');
    if (logFoodTile) {
        logFoodTile.addEventListener('click', function() {
            console.log('Log Food clicked');
            // Navigate to food logging page
            // Example: window.location.href = 'nutrition.html';
        });
    }
}
