/**
 * index.js
 * Entry point for the fitness tracking application
 * 
 * This file loads all required modules and initializes the application.
 * It should be included in all HTML pages.
 */

// Load order matters! Dependencies must be loaded first
document.addEventListener("DOMContentLoaded", function() {
    console.log("Fitness Tracker initializing...");
    
    // Initialize any buttons that need POST and redirect functionality
    initializePostAndRedirectButtons();
});

/**
 * Script loading order:
 * 
 * 1. utils.js - No dependencies
 * 2. storage.js - No dependencies
 * 3. ui.js - No dependencies
 * 4. calendar.js - Depends on storage.js
 * 5. workout.js - Depends on storage.js, ui.js
 * 6. nutrition.js - Depends on storage.js, ui.js
 * 7. readiness.js - Depends on storage.js, ui.js
 * 8. core.js - Depends on all other modules
 * 
 * Each module is loaded as a self-contained IIFE that exposes only
 * necessary public methods and properties.
 */

/**
 * Initialize buttons that need to send POST requests and redirect
 */

function initializePostAndRedirectButtons() {
    // Check if CoachUtils exists
    if (!window.CoachUtils) {
        console.error('CoachUtils not loaded. Make sure utils.js is included before index.js');
        return;
    }
    
    // Example: Setup a "Save Workout" button if it exists on the page
    if (document.getElementById('saveWorkoutBtn')) {
        CoachUtils.setupButtonWithPostAndRedirect(
            'saveWorkoutBtn', 
            '/api/workouts/save', 
            () => {
                // Function to collect data from the form
                const workoutData = {
                    date: document.getElementById('workoutDate')?.value || new Date().toISOString().split('T')[0],
                    exercises: collectExerciseData(),
                    notes: document.getElementById('workoutNotes')?.value || '',
                    duration: document.getElementById('workoutDuration')?.value || 0
                };
                return workoutData;
            },
            'workout_of_the_day.html'
        );
    }
    
    // Example: Setup a "Log Food" button if it exists on the page
    if (document.getElementById('logFoodBtn')) {
        CoachUtils.setupButtonWithPostAndRedirect(
            'logFoodBtn', 
            '/api/nutrition/log', 
            () => {
                // Function to collect nutrition data
                const nutritionData = {
                    date: document.getElementById('foodDate')?.value || new Date().toISOString().split('T')[0],
                    foodItems: collectFoodItems(),
                    totalCalories: calculateTotalCalories(),
                    mealType: document.getElementById('mealType')?.value || 'snack'
                };
                return nutritionData;
            },
            'log_food.html'
        );
    }
    
    // Add more button setups as needed
}

/**
 * Render the readiness chart if present
 */

function initializeReadinessChart() {
    const ctx = document.getElementById("readinessChart");
    if (!ctx || typeof Chart === "undefined") return;

    const checkIns = JSON.parse(localStorage.getItem("checkIns") || "[]");
    const last7Days = checkIns
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(-7);

    new Chart(ctx, {
        type: "line",
        data: {
            labels: last7Days.map(day => new Date(day.date).toLocaleDateString("en-US", { weekday: "short" })),
            datasets: [{
                label: "Readiness Score",
                data: last7Days.map(day => day.readiness || 0),
                borderColor: "#ef4444",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: "#9CA3AF" }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)"
                    },
                    ticks: {
                        color: "#9CA3AF",
                        callback: value => `${value}%`
                    }
                },
                x: {
                    grid: {
                        color: "rgba(255, 255, 255, 0.1)"
                    },
                    ticks: { color: "#9CA3AF" }
                }
            }
        }
    });
}

/**
 * Helper function to collect exercise data from the form
 * @returns {Array} Array of exercise objects
 */

function collectExerciseData() {
    const exercises = [];
    const exerciseRows = document.querySelectorAll('.exercise-row');
    
    exerciseRows.forEach(row => {
        const exerciseName = row.querySelector('.exercise-name')?.value;
        const sets = row.querySelector('.exercise-sets')?.value;
        const reps = row.querySelector('.exercise-reps')?.value;
        const weight = row.querySelector('.exercise-weight')?.value;
        
        if (exerciseName) {
            exercises.push({
                name: exerciseName,
                sets: parseInt(sets) || 0,
                reps: parseInt(reps) || 0,
                weight: parseFloat(weight) || 0
            });
        }
    });
    
    return exercises;
}

/**
 * Helper function to collect food items from the form
 * @returns {Array} Array of food item objects
 */

function collectFoodItems() {
    const foodItems = [];
    const foodRows = document.querySelectorAll('.food-item-row');
    
    foodRows.forEach(row => {
        const foodName = row.querySelector('.food-name')?.value;
        const servingSize = row.querySelector('.serving-size')?.value;
        const calories = row.querySelector('.food-calories')?.value;
        
        if (foodName) {
            foodItems.push({
                name: foodName,
                servingSize: servingSize || 'N/A',
                calories: parseInt(calories) || 0
            });
        }
    });
    
    return foodItems;
}

/**
 * Helper function to calculate total calories
 * @returns {number} Total calories
 */

function calculateTotalCalories() {
    let total = 0;
    const caloriesInputs = document.querySelectorAll('.food-calories');
    
    caloriesInputs.forEach(input => {
        total += parseInt(input.value) || 0;
    });
    
    return total;
}
