/**
 * workout.js
 * 
 * This module handles all workout-related functionality including:
 * - Loading workouts from storage/API
 * - Generating workouts via API calls
 * - Exercise recommendations via API calls
 * - Managing workout data state
 * - Displaying workout data
 * - Saving workouts via API calls
 */

const WorkoutModule = (() => {
    // Private variables and utility functions
    const config = {
        generateWorkoutEndpoint: '/api/generate-workout', // Updated endpoint
        recommendationsEndpoint: '/api/recommendations',
        saveWorkoutEndpoint: '/api/save-workout', // Added endpoint
        loadWorkoutEndpoint: '/api/load-workout' // Added endpoint
    };
    
    let currentWorkout = {
        date: new Date().toISOString().split('T')[0],
        exercises: [],
        notes: '',
        duration: 0,
        intensity_level: '',
        estimated_duration: 0,
        calories_burn_estimate: 0,
        workout_notes_from_engine: [] // To store notes from the engine
    };

    // DOM Elements (cache them if used frequently)
    const workoutListEl = document.getElementById('workoutList');
    const recommendationsListEl = document.getElementById('recommendationsList');
    const recommendationsLoaderEl = document.getElementById('recommendationsLoader');
    const workoutDateEl = document.getElementById('workoutDate');
    const workoutDurationEl = document.getElementById('workoutDuration');
    const workoutNotesEl = document.getElementById('workoutNotes');
    const selectedDateEl = document.getElementById('selectedDate');
    // Summary elements
    const totalVolumeEl = document.getElementById('totalVolume');
    const totalSetsEl = document.getElementById('totalSets');
    const maxWeightEl = document.getElementById('maxWeight');
    const totalRepsEl = document.getElementById('totalReps');


    /**
     * Fetches data from the API.
     * @param {string} url - The API endpoint.
     * @param {string} method - HTTP method (GET, POST, etc.).
     * @param {object} [body=null] - Request body for POST/PUT requests.
     * @returns {Promise<object>} - The JSON response from the API.
     */
    const apiRequest = async (url, method = 'GET', body = null) => {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                // Add authorization headers if needed
                // 'Authorization': `Bearer ${localStorage.getItem('authToken')}` 
            }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(`API Error (${response.status}): ${errorData.message || 'Unknown error'}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error during API request to ${url}:`, error);
            // Display error to user (using a UI notification system is better)
            alert(`Error: ${error.message}`); 
            throw error; // Re-throw to allow calling function to handle
        }
    };

    /**
     * Loads a workout for a specific date from the backend.
     * @param {string} dateString - The date to load the workout for (YYYY-MM-DD).
     */
    const loadWorkout = async (dateString) => {
        console.log(`Loading workout for date: ${dateString}`);
        currentWorkout = { // Reset current workout before loading
            date: dateString,
            exercises: [],
            notes: '',
            duration: 0,
            intensity_level: '',
            estimated_duration: 0,
            calories_burn_estimate: 0,
            workout_notes_from_engine: []
        };
        try {
            // TODO: Add user ID or session handling to the request
            const data = await apiRequest(`${config.loadWorkoutEndpoint}?date=${dateString}`, 'GET'); 
            if (data && data.workout) {
                // Assuming the backend returns workout data in a 'workout' property
                currentWorkout.exercises = data.workout.exercises || [];
                currentWorkout.notes = data.workout.notes || '';
                currentWorkout.duration = data.workout.duration || 0;
                // Populate other fields if returned by backend
                currentWorkout.intensity_level = data.workout.intensity_level || '';
                currentWorkout.estimated_duration = data.workout.estimated_duration || 0;
                currentWorkout.calories_burn_estimate = data.workout.calories_burn_estimate || 0;
                currentWorkout.workout_notes_from_engine = data.workout.workout_notes_from_engine || [];

                console.log("Loaded workout:", currentWorkout);
            } else {
                 console.log("No workout found for this date, starting fresh.");
            }
        } catch (error) {
            console.error("Failed to load workout:", error);
            // Keep the reset/empty workout state
        } finally {
            displayWorkout(); // Display loaded or empty workout
        }
    };
    
    /**
     * Gets the current workout data.
     * @returns {Object} Current workout object.
     */
    const getCurrentWorkout = () => {
        // Update notes and duration from UI before returning, in case they were edited
        currentWorkout.notes = workoutNotesEl ? workoutNotesEl.value : currentWorkout.notes;
        currentWorkout.duration = workoutDurationEl ? parseInt(workoutDurationEl.value, 10) || 0 : currentWorkout.duration;
        return currentWorkout;
    };
    
    /**
     * Generates a workout based on the selected type via API call.
     * @param {string} workoutType - The type of workout to generate (maps to goals/muscle groups).
     */
    const generateWorkout = async (workoutType) => {
        console.log(`Generating workout for type: ${workoutType}`);
        // Clear previous workout before generating new one
        resetDayWorkout(false); // Don't reload, just clear state and UI

        // Show loader maybe?
        if (workoutListEl) workoutListEl.innerHTML = '<p class="text-center text-gray-400">Generating workout...</p>';

        try {
            // Prepare data payload for the backend
            // This should include user preferences/goals fetched from profile or settings
            const requestData = {
                // user_id: getUserId(), // Function to get logged-in user ID
                workout_goal: workoutType, // Map the button type to a goal the backend understands
                // fitness_level: getUserFitnessLevel(), // Fetch from user profile
                // available_equipment: getUserEquipment(), // Fetch from user profile
                // target_muscle_groups: workoutType === 'full_body' ? ['full_body'] : [workoutType], // Example mapping
                // workout_duration: 45, // Default or from user preference
                // energy_level: getUserEnergyLevel() // Maybe from a daily check-in?
            };

            const data = await apiRequest(config.generateWorkoutEndpoint, 'POST', requestData);
            
            if (data && data.workout_plan) {
                currentWorkout.exercises = data.workout_plan;
                currentWorkout.intensity_level = data.intensity_level || '';
                currentWorkout.estimated_duration = data.estimated_duration || 0;
                currentWorkout.calories_burn_estimate = data.calories_burn_estimate || 0;
                currentWorkout.workout_notes_from_engine = data.notes || [];
                currentWorkout.notes = data.notes ? data.notes.join('\n') : ''; // Pre-fill notes
                currentWorkout.duration = data.estimated_duration || 0; // Pre-fill duration

                console.log("Generated workout:", currentWorkout);
            } else {
                console.error("Failed to generate workout, response format incorrect:", data);
                currentWorkout.notes = "Workout generation failed. Please try again.";
            }
        } catch (error) {
            console.error("Error generating workout:", error);
            currentWorkout.notes = `Error generating workout: ${error.message}`;
        } finally {
            displayWorkout(); // Display the generated workout or error message
        }
    };
    
    /**
     * Gets exercise recommendations via API call.
     */
    const getRecommendations = async () => {
        console.log("Getting recommendations...");
        if (recommendationsLoaderEl) recommendationsLoaderEl.classList.remove('hidden');
        if (recommendationsListEl) recommendationsListEl.innerHTML = ''; // Clear previous

        try {
            // TODO: Add user ID or profile data to the request if needed by the backend
            const data = await apiRequest(config.recommendationsEndpoint, 'GET'); 
            
            if (data && data.recommended_exercises) { // Assuming backend returns { recommended_exercises: { dimension: [ex1, ex2] } }
                displayRecommendations(data.recommended_exercises);
            } else {
                 if (recommendationsListEl) recommendationsListEl.innerHTML = '<p class="text-gray-400">No recommendations available at this time.</p>';
            }
        } catch (error) {
            console.error("Failed to get recommendations:", error);
             if (recommendationsListEl) recommendationsListEl.innerHTML = `<p class="text-red-400">Error loading recommendations: ${error.message}</p>`;
        } finally {
             if (recommendationsLoaderEl) recommendationsLoaderEl.classList.add('hidden');
        }
    };

    /**
     * Displays recommendations in the UI.
     * @param {object} recommendations - Object with dimensions as keys and exercise lists as values.
     */
    const displayRecommendations = (recommendations) => {
        if (!recommendationsListEl) return;
        recommendationsListEl.innerHTML = ''; // Clear previous

        if (Object.keys(recommendations).length === 0) {
            recommendationsListEl.innerHTML = '<p class="text-gray-400">No specific recommendations based on current analysis.</p>';
            return;
        }

        for (const dimension in recommendations) {
            const exercises = recommendations[dimension];
            if (exercises.length > 0) {
                const section = document.createElement('div');
                section.className = 'mb-4';
                const title = document.createElement('h4');
                title.className = 'font-semibold text-red-500 mb-1 capitalize';
                title.textContent = dimension.replace(/_/g, ' '); // Make dimension readable
                section.appendChild(title);

                const list = document.createElement('ul');
                list.className = 'list-disc list-inside text-sm space-y-1';
                exercises.forEach(exName => {
                    const listItem = document.createElement('li');
                    listItem.textContent = exName;
                    // Optional: Add button to add exercise directly to workout
                    // const addButton = document.createElement('button');
                    // addButton.textContent = '+';
                    // addButton.className = 'ml-2 text-green-500 hover:text-green-400';
                    // addButton.onclick = () => addExerciseToWorkout(exName, 3, 10, 0); // Example defaults
                    // listItem.appendChild(addButton);
                    list.appendChild(listItem);
                });
                section.appendChild(list);
                recommendationsListEl.appendChild(section);
            }
        }
    };
    
    /**
     * Add an exercise to the current workout state (does not save yet).
     * @param {string} name - Exercise name.
     * @param {number|string} sets - Number of sets.
     * @param {number|string} reps - Number of reps or rep range/description.
     * @param {number} [weight=0] - Weight used.
     * @param {number} [rest=60] - Rest period in seconds.
     * @param {string} [muscleGroup='unknown'] - Muscle group targeted.
     */
    const addExerciseToWorkout = (name, sets, reps, weight = 0, rest = 60, muscleGroup = 'unknown') => {
        currentWorkout.exercises.push({
            exercise: name, // Match backend structure
            sets: sets,
            reps: reps,
            weight: weight, // Add weight if applicable
            rest: rest,     // Add rest if applicable
            muscle_group: muscleGroup // Add muscle group
        });
        displayWorkout(); // Update UI
    };
    
    /**
     * Resets the workout for the current day.
     * @param {boolean} [reload=true] - Whether to reload data for the current date after reset.
     */
    const resetDayWorkout = (reload = true) => {
        console.log("Resetting workout for date:", currentWorkout.date);
        const dateToReload = currentWorkout.date;
        currentWorkout = {
            date: dateToReload,
            exercises: [],
            notes: '',
            duration: 0,
            intensity_level: '',
            estimated_duration: 0,
            calories_burn_estimate: 0,
            workout_notes_from_engine: []
        };
        if (reload) {
            loadWorkout(dateToReload); // Reload (will likely show empty if not saved)
        } else {
            displayWorkout(); // Just update UI to show empty state
        }
    };

    /**
     * Saves the current workout to the backend.
     */
    const saveWorkout = async () => {
        console.log("Saving workout...");
        const workoutData = getCurrentWorkout(); // Get data including UI updates

        if (!workoutData.date) {
            alert("Please select a date for the workout.");
            return;
        }
        if (workoutData.exercises.length === 0) {
            alert("Please add at least one exercise or generate a workout before saving.");
            return;
        }

        // Show saving indicator?
        const saveButton = document.getElementById('saveWorkoutBtn');
        if (saveButton) saveButton.textContent = 'Saving...';
        if (saveButton) saveButton.disabled = true;


        try {
            // TODO: Add user ID
            const payload = {
                // user_id: getUserId(),
                workout_date: workoutData.date,
                duration: workoutData.duration,
                notes: workoutData.notes,
                exercises: workoutData.exercises,
                // Include other relevant data if needed by backend
                intensity_level: workoutData.intensity_level,
                estimated_duration: workoutData.estimated_duration,
                calories_burn_estimate: workoutData.calories_burn_estimate
            };
            const response = await apiRequest(config.saveWorkoutEndpoint, 'POST', payload);
            console.log("Save response:", response);
            alert(response.message || "Workout saved successfully!"); // Use a better notification
        } catch (error) {
            console.error("Failed to save workout:", error);
            // Error already shown by apiRequest
        } finally {
             if (saveButton) saveButton.textContent = 'Save Workout';
             if (saveButton) saveButton.disabled = false;
        }
    };
    
    /**
     * Displays the current workout in the UI.
     */
    const displayWorkout = () => {
        console.log("Displaying workout:", currentWorkout);
        if (!workoutListEl || !workoutDateEl || !workoutDurationEl || !workoutNotesEl || !selectedDateEl) {
            console.error("One or more UI elements not found for displaying workout.");
            return;
        }

        // Update Date display
        workoutDateEl.value = currentWorkout.date;
        selectedDateEl.textContent = new Date(currentWorkout.date + 'T00:00:00').toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }); // User-friendly date

        // Update Duration and Notes
        workoutDurationEl.value = currentWorkout.duration || '';
        workoutNotesEl.value = currentWorkout.notes || '';

        // Clear previous workout list
        workoutListEl.innerHTML = ''; 

        if (currentWorkout.exercises.length === 0) {
            workoutListEl.innerHTML = '<p class="text-center text-gray-400">No exercises added yet. Generate a workout or add exercises manually.</p>';
        } else {
            currentWorkout.exercises.forEach((exercise, index) => {
                const exerciseEl = document.createElement('div');
                exerciseEl.className = 'bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center';
                
                // Basic exercise info
                let exerciseInfo = `
                    <div class="flex-grow mr-4">
                        <p class="font-semibold text-red-500">${exercise.exercise}</p>
                        <p class="text-sm text-gray-300">
                            Sets: ${exercise.sets} | Reps: ${exercise.reps} | Rest: ${exercise.rest}s 
                            ${exercise.weight ? `| Weight: ${exercise.weight}kg` : ''} 
                            ${exercise.muscle_group && exercise.muscle_group !== 'unknown' ? `(${exercise.muscle_group})` : ''}
                        </p>
                    </div>
                `;
                // TODO: Add inputs for editing sets/reps/weight directly?
                // TODO: Add button to remove exercise

                exerciseEl.innerHTML = exerciseInfo;
                workoutListEl.appendChild(exerciseEl);
            });
        }
        
        // Update Summary - Placeholder calculations
        updateSummary();
    };

    /**
     * Updates the workout summary section.
     */
    const updateSummary = () => {
        let volume = 0;
        let sets = 0;
        let maxWt = 0;
        let reps = 0;

        currentWorkout.exercises.forEach(ex => {
            const exSets = parseInt(ex.sets) || 0;
            const exWeight = parseFloat(ex.weight) || 0;
            
            // Try to parse reps - handle ranges like "8-12" or "AMRAP" or "30 seconds"
            let avgReps = 0;
            if (typeof ex.reps === 'number') {
                avgReps = ex.reps;
            } else if (typeof ex.reps === 'string') {
                if (ex.reps.includes('-')) {
                    const parts = ex.reps.split('-').map(p => parseInt(p.trim()));
                    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
                        avgReps = (parts[0] + parts[1]) / 2;
                    }
                } else if (!isNaN(parseInt(ex.reps))) {
                     avgReps = parseInt(ex.reps);
                }
                // Ignore "AMRAP", "seconds", etc. for volume/rep count for now
            }

            if (exSets > 0 && avgReps > 0 && exWeight > 0) {
                 volume += exSets * avgReps * exWeight;
            }
            sets += exSets;
            if (avgReps > 0) {
                 reps += exSets * avgReps; // Total reps = sets * reps_per_set
            }
            if (exWeight > maxWt) {
                maxWt = exWeight;
            }
        });

        if (totalVolumeEl) totalVolumeEl.textContent = `${Math.round(volume)} kg`;
        if (totalSetsEl) totalSetsEl.textContent = sets;
        if (maxWeightEl) maxWeightEl.textContent = `${maxWt} kg`;
        if (totalRepsEl) totalRepsEl.textContent = Math.round(reps);
    };

    // Public methods
    return {
        loadWorkout,
        getCurrentWorkout,
        generateWorkout,
        getRecommendations,
        addExerciseToWorkout, // Keep if manual adding is needed
        resetDayWorkout,
        saveWorkout,
        displayWorkout // Expose if needed externally (e.g., by calendar)
    };
})();

// Make sure the module is available globally or imported where needed
window.WorkoutModule = WorkoutModule;

// Initial load for today's date (might be better called from index.js or workout_dashboard.js)
// document.addEventListener('DOMContentLoaded', () => {
//     const today = new Date().toISOString().split('T')[0];
//     WorkoutModule.loadWorkout(today); 
// });