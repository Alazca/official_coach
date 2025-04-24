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
});

/**
 * Script loading order:
 * 
 * 1. storage.js - No dependencies
 * 2. ui.js - No dependencies
 * 3. calendar.js - Depends on storage.js
 * 4. workout.js - Depends on storage.js, ui.js
 * 5. nutrition.js - Depends on storage.js, ui.js
 * 6. readiness.js - Depends on storage.js, ui.js
 * 7. core.js - Depends on all other modules
 * 
 * Each module is loaded as a self-contained IIFE that exposes only
 * necessary public methods and properties.
 */