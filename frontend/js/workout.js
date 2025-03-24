/**
 * workout.js
 * Workout tracking functionality
 */

const WorkoutModule = (function() {
    /**
     * Predefined workout templates
     */
    const workoutTypes = {
        push: {
            name: 'Push Workout',
            exercises: [
                { name: 'Bench Press', sets: '4', reps: '8-12' },
                { name: 'Overhead Press', sets: '3', reps: '8-12' },
                { name: 'Incline Press', sets: '3', reps: '8-12' },
                { name: 'Lateral Raises', sets: '3', reps: '12-15' },
                { name: 'Tricep Extensions', sets: '3', reps: '12-15' }
            ]
        },
        pull: {
            name: 'Pull Workout',
            exercises: [
                { name: 'Barbell Rows', sets: '4', reps: '8-12' },
                { name: 'Pull-ups', sets: '3', reps: '8-12' },
                { name: 'Face Pulls', sets: '3', reps: '12-15' },
                { name: 'Bicep Curls', sets: '3', reps: '12-15' },
                { name: 'Lat Pulldowns', sets: '3', reps: '10-12' }
            ]
        },
        legs: {
            name: 'Leg Workout',
            exercises: [
                { name: 'Squats', sets: '4', reps: '8-12' },
                { name: 'Romanian Deadlifts', sets: '3', reps: '8-12' },
                { name: 'Leg Press', sets: '3', reps: '10-15' },
                { name: 'Calf Raises', sets: '4', reps: '15-20' },
                { name: 'Leg Extensions', sets: '3', reps: '12-15' }
            ]
        }
    };

    /**
     * Display workout options to user
     */
    function displayWorkoutOptions() {
        const workoutList = document.getElementById('workoutList');
        if (!workoutList) return;

        workoutList.innerHTML = Object.values(workoutTypes).map(type => `
            <div class="mb-6">
                <h2 class="text-xl font-bold text-white mb-4">${type.name}</h2>
                <div class="space-y-3">
                    ${type.exercises.map(exercise => `
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex justify-between items-center">
                                <h3 class="text-lg font-bold text-white">${exercise.name}</h3>
                                <span class="bg-red-600 px-3 py-1 rounded text-sm">
                                    ${exercise.sets} sets × ${exercise.reps} reps
                                </span>
                            </div>
                            <button onclick="WorkoutModule.logSet('${exercise.name}')" 
                                class="mt-2 w-full bg-red-600 text-white py-2 rounded hover:bg-red-700">
                                Log Set
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    /**
     * Load and display workout for a specific date
     * @param {Date} date - Date to load workout for
     */
    function loadWorkout(date) {
        const logs = StorageModule.getItem('workoutLogs', []);
        const dayLogs = logs.filter(log => log.date === date.toLocaleDateString());
        const workoutList = document.getElementById('workoutList');
        
        if (!workoutList) return;

        workoutList.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold text-white">Workout for ${date.toLocaleDateString()}</h2>
            </div>
        `;
        
        if (dayLogs.length > 0) {
            // Calculate total volume
            const totalVolume = dayLogs.reduce((sum, log) => sum + (log.weight * log.reps || 0), 0);
            
            // Display logged workout
            workoutList.innerHTML += `
                <div class="space-y-4">
                    ${dayLogs.map((log, index) => `
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex justify-between items-center">
                                <div>
                                    <h3 class="text-lg font-bold text-white">${log.exercise}</h3>
                                    <span class="text-sm text-gray-400">Set ${index + 1}</span>
                                </div>
                                <span class="bg-red-600 px-3 py-1 rounded text-sm">
                                    ${log.weight}kg × ${log.reps} reps (RPE: ${log.rpe})
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            updateWorkoutSummary(date);
        } else {
            // Display empty state
            workoutList.innerHTML += `
                <div class="text-center py-8">
                    <p class="text-gray-400 mb-4">No workout logged for this day</p>
                    <button onclick="WorkoutModule.generateWorkout()" 
                        class="w-full bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-2 rounded-lg mb-4">
                        Generate Workout
                    </button>
                </div>
            `;
        }
        updateWorkoutSummary(date);
    }

    /**
     * Generate a random workout from templates
     */
    function generateWorkout() {
        const workoutList = document.getElementById('workoutList');
        const selectedDate = document.getElementById('selectedDate')?.textContent || new Date().toLocaleDateString();
        if (!workoutList) return;

        // Pick a random workout type
        const types = Object.keys(workoutTypes);
        const randomType = types[Math.floor(Math.random() * types.length)];
        const workout = workoutTypes[randomType];

        // Save the generated workout to localStorage
        const generatedWorkout = workout.exercises.map(exercise => ({
            exercise: exercise.name,
            sets: exercise.sets,
            reps: exercise.reps,
            date: selectedDate
        }));
        StorageModule.setItem(`generatedWorkout_${selectedDate}`, generatedWorkout);

        // Display the generated workout
        workoutList.innerHTML = `
            <div class="mb-6">
                <h2 class="text-xl font-bold text-white mb-4">${workout.name}</h2>
                <div class="space-y-3">
                    ${workout.exercises.map(exercise => `
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex justify-between items-center">
                                <h3 class="text-lg font-bold text-white">${exercise.name}</h3>
                                <span class="bg-red-600 px-3 py-1 rounded text-sm">
                                    ${exercise.sets} sets × ${exercise.reps} reps
                                </span>
                            </div>
                            <button onclick="WorkoutModule.logSet('${exercise.name}')" 
                                class="mt-2 w-full bg-red-600 text-white py-2 rounded hover:bg-red-700">
                                Log Set
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Log a set for a specific exercise
     * @param {string} exercise - Exercise name
     */
    function logSet(exercise) {
        const selectedDate = document.getElementById('selectedDate')?.textContent || new Date().toLocaleDateString();

        // Show modal for entering set details
        UIModule.showModal({
            title: `Log Set - ${exercise}`,
            content: `
                <form id="setLogForm" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium mb-2">Weight (kg)</label>
                        <input type="number" id="weight" step="0.5" min="0" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Reps</label>
                        <input type="number" id="reps" min="1" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">RPE (1-10)</label>
                        <input type="number" id="rpe" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                </form>
            `,
            onSubmit: function() {
                const data = {
                    exercise,
                    weight: Number(document.getElementById('weight').value),
                    reps: Number(document.getElementById('reps').value),
                    rpe: Number(document.getElementById('rpe').value),
                    date: selectedDate
                };

                // Store the workout data
                StorageModule.addToArray('workoutLogs', data);

                // Reload the workout display
                loadWorkout(new Date(selectedDate));
                return true; // Close modal
            }
        });
    }

    /**
     * Update workout summary statistics
     * @param {Date} date - Date to calculate summary for
     */
    function updateWorkoutSummary(date) {
        const logs = StorageModule.getItem('workoutLogs', []);
        const dayLogs = logs.filter(log => log.date === date.toLocaleDateString());
        
        // Calculate summary statistics
        const summary = dayLogs.reduce((sum, log) => ({
            volume: sum.volume + (log.weight * log.reps),
            sets: sum.sets + 1,
            maxWeight: Math.max(sum.maxWeight, log.weight),
            totalReps: sum.totalReps + log.reps
        }), { volume: 0, sets: 0, maxWeight: 0, totalReps: 0 });

        // Update the summary display
        const elements = {
            totalVolume: { value: summary.volume, unit: 'kg' },
            totalSets: { value: summary.sets, unit: '' },
            maxWeight: { value: summary.maxWeight, unit: 'kg' },
            totalReps: { value: summary.totalReps, unit: '' }
        };

        // Update UI elements
        Object.entries(elements).forEach(([id, { value, unit }]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value ? `${Math.round(value)}${unit}` : `0${unit}`;
                // Add color based on value
                element.className = value > 0 ? 
                    'text-2xl font-bold text-green-500' : 
                    'text-2xl font-bold text-red-500';
            }
        });
    }

    /**
     * Reset all workout data for a specific day
     */
    function resetDayWorkout() {
        const selectedDate = document.getElementById('selectedDate').textContent;
        if (!selectedDate) return;

        const confirmReset = confirm('Are you sure you want to reset all workouts for this day?');
        if (!confirmReset) return;

        // Remove all logs for the selected date
        StorageModule.filterArray('workoutLogs', log => log.date !== selectedDate);

        // Reload the workout display
        loadWorkout(new Date(selectedDate));
    }

    // Public API
    return {
        displayWorkoutOptions,
        loadWorkout,
        generateWorkout,
        logSet,
        resetDayWorkout
    };
})();