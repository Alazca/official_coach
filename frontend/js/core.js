/**
 * core.js
 * Core application initialization and routing
 */

// Initialize application when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    console.log('Core.js initialized');
    
    // Handle "Daily Check-In" button
    const checkInButton = document.getElementById('checkInButton');
    if (checkInButton) {
        console.log('Found checkInButton');
        checkInButton.addEventListener('click', () => {
            console.log('Daily Check-In button clicked');
            ReadinessModule.showCheckInModal();
        });
    } else {
        console.error('checkInButton not found');
    }

    // Handle navigation from main page to log food page
    const logFoodButton = document.getElementById('logFoodTile');
    if (logFoodButton) {
        console.log('Found logFoodTile button');
        logFoodButton.addEventListener('click', function() {
            console.log('Log food button clicked');
            window.location.href = 'log_food.html';
        });
    } else {
        console.error('logFoodTile button not found');
    }
    
    // Simple direct button handlers
    const buttons = document.querySelectorAll('button[id]');
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            console.log('Button clicked:', button.id); // Debug log
            
            switch(button.id) {
                case 'workoutTile':
                    window.location.href = 'workout_of_the_day.html';
                    break;
                case 'visualizeTile':
                    window.location.href = 'visualize_data.html';
                    break;
                case 'logFoodTile':
                    window.location.href = 'log_food.html';
                    break;
                case 'signUpButton':
                    showSignUpModal();
                    break;
                default:
                    break;
            }
        });
    });

    try {
        // Initialize all buttons first
        UIModule.initializeAllButtons();
        
        // Add specific button handlers
        const buttons = {
            'checkInButton': () => ReadinessModule.showCheckInModal(),
            'sendMessageBtn': () => window.sendMessage?.()
        };

        // Attach handlers to buttons
        Object.entries(buttons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });

        // Initialize page-specific functionality
        const currentPage = window.location.pathname;
        
        switch(true) {
            case currentPage.endsWith('workout_of_the_day.html'):
                initializeWorkoutPage();
                break;
            case currentPage.endsWith('log_food.html'):
                initializeNutritionPage();
                break;
            case currentPage.endsWith('visualize_data.html'):
                initializeVisualizationPage();
                break;
            default:
                initializeHomePage();
        }
    } catch (error) {
        console.error('Initialization error:', error);
        showErrorMessage('Failed to initialize application');
    }
});

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

function initializeWorkoutPage() {
    CalendarModule.initializeCalendar();
    CalendarModule.initializePageCalendar();
    const currentDate = new Date();
    WorkoutModule.loadWorkout(currentDate);
}

function initializeNutritionPage() {
    CalendarModule.initializeCalendar();
    CalendarModule.initializePageCalendar();
    const currentDate = new Date();
    NutritionModule.loadMeals(currentDate);
}

function initializeVisualizationPage() {
    initializeCharts();
    updateCharts();
}

function initializeHomePage() {
    const checkInButton = document.getElementById("checkInButton");
    const activityLog = document.getElementById("activityLog");
    
    if (checkInButton && activityLog) {
        checkInButton.addEventListener("click", ReadinessModule.showCheckInModal);
        
        // Load last check-in
        const checkIns = StorageModule.getItem('checkIns', []);
        const today = new Date().toLocaleDateString();
        const lastCheckIn = checkIns.find(check => check.date === today);
        
        if (lastCheckIn) {
            ReadinessModule.updateReadinessDisplay(lastCheckIn);
        }
    }

    // Initialize readiness chart if on index page
    if (document.getElementById('readinessChart')) {
        ReadinessModule.initializeReadinessChart();
    }
}

/**
 * Initialize navigation between app pages
 */
function initializeNavigation() {
    const navItems = {
        "workoutTile": "workout_of_the_day.html",
        "visualizeTile": "visualize_data.html",
        "logFoodTile": "log_food.html"  // Make sure this matches the button ID
    };

    Object.entries(navItems).forEach(([id, path]) => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener("click", (e) => {
                e.preventDefault();
                console.log(`Navigating to ${path}`); // Debug log
                window.location.href = path;
            });
        }
    });
}

// Initialize visualization functionality
// Note: This would be moved to visualization.js in a full refactoring
function initializeCharts() {
    // Chart initialization code
    console.log("Charts initialized");
}

function updateCharts() {
    // Chart update code
    console.log("Charts updated");
}

function showSignUpModal() {
    UIModule.showModal({
        title: 'Sign Up',
        content: `
            <form id="signUpForm" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Email</label>
                    <input type="email" id="email" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Password</label>
                    <input type="password" id="password" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                </div>
            </form>
        `,
        onSubmit: () => {
            // Handle sign up logic here
            UIModule.showToast('Sign up successful!');
            return true;
        }
    });
}

// Show the Daily Check-In modal
function showCheckInModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full text-white">
            <h3 class="text-2xl font-bold mb-6">Daily Check-In</h3>
            <form id="checkInForm" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Weight (kg)</label>
                    <input type="number" id="weight" step="0.1" min="0" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Sleep Quality (1-10)</label>
                    <input type="number" id="sleep" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Stress Level (1-10)</label>
                    <input type="number" id="stress" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                </div>
                <div class="flex gap-4">
                    <button type="submit" class="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">Save</button>
                    <button type="button" onclick="this.closest('div').remove()" class="flex-1 bg-gray-700 text-white py-2 rounded-lg hover:bg-gray-600">Cancel</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('checkInForm').onsubmit = (e) => {
        e.preventDefault();
        saveCheckInData();
        modal.remove();
    };
}

// Save check-in data to localStorage
function saveCheckInData() {
    const data = {
        weight: Number(document.getElementById('weight').value),
        sleep: Number(document.getElementById('sleep').value),
        stress: Number(document.getElementById('stress').value),
        date: new Date().toLocaleDateString()
    };

    // Save to localStorage
    const checkIns = JSON.parse(localStorage.getItem('checkIns') || '[]');
    checkIns.push(data);
    localStorage.setItem('checkIns', JSON.stringify(checkIns));

    console.log('Check-in data saved:', data);
    updateReadinessDisplay(data);
}

// Update readiness display
function updateReadinessDisplay(data) {
    const activityLog = document.getElementById('activityLog');
    if (!activityLog) return;

    const readinessScore = calculateReadiness(data);
    activityLog.innerHTML = `
        <div class="p-4">
            <h3 class="text-xl font-bold">Today's Readiness Score</h3>
            <p class="text-3xl font-bold text-green-500">${readinessScore}%</p>
            <p class="text-sm mt-2">Sleep: ${data.sleep}/10, Stress: ${data.stress}/10</p>
        </div>
    `;
}

// Calculate readiness score
function calculateReadiness(data) {
    const sleepWeight = 0.5;
    const stressWeight = 0.5;
    const sleepScore = data.sleep * sleepWeight;
    const stressScore = (10 - data.stress) * stressWeight;
    return Math.round((sleepScore + stressScore) * 10);
}