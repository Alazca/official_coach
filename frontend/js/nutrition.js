/**
 * nutrition.js
 * Nutrition and meal tracking functionality
 */

const NutritionModule = (function() {
    /**
     * Predefined meal templates
     */
    const mealTypes = {
        breakfast: {
            name: 'Breakfast',
            options: [
                { name: 'Oatmeal', calories: 150, protein: 6, carbs: 27, fats: 3 },
                { name: 'Eggs & Toast', calories: 300, protein: 15, carbs: 30, fats: 12 },
                { name: 'Greek Yogurt', calories: 120, protein: 12, carbs: 8, fats: 4 }
            ]
        },
        lunch: {
            name: 'Lunch',
            options: [
                { name: 'Chicken Salad', calories: 350, protein: 25, carbs: 15, fats: 20 },
                { name: 'Turkey Sandwich', calories: 400, protein: 20, carbs: 45, fats: 12 },
                { name: 'Tuna Wrap', calories: 320, protein: 22, carbs: 35, fats: 10 }
            ]
        },
        dinner: {
            name: 'Dinner',
            options: [
                { name: 'Salmon & Rice', calories: 450, protein: 30, carbs: 40, fats: 18 },
                { name: 'Steak & Vegetables', calories: 500, protein: 35, carbs: 25, fats: 25 },
                { name: 'Chicken Stir-Fry', calories: 400, protein: 28, carbs: 35, fats: 15 }
            ]
        }
    };

    /**
     * Display all meal options to user
     */
    function displayAllMeals() {
        const foodList = document.getElementById('foodList');
        if (!foodList) return;

        foodList.innerHTML = Object.values(mealTypes).map(category => `
            <div class="mb-6">
                <h2 class="text-xl font-bold text-white mb-4">${category.name}</h2>
                <div class="space-y-3">
                    ${category.options.map(meal => `
                        <div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
                            <div class="flex justify-between items-center">
                                <h3 class="text-lg font-bold text-white">${meal.name}</h3>
                                <span class="bg-red-600 px-3 py-1 rounded text-sm">
                                    ${meal.calories} cal | P:${meal.protein}g C:${meal.carbs}g F:${meal.fats}g
                                </span>
                            </div>
                            <button onclick="NutritionModule.logMeal('${meal.name}', ${meal.calories}, ${meal.protein}, ${meal.carbs}, ${meal.fats})" 
                                class="mt-2 w-full bg-red-600 text-white py-2 rounded hover:bg-red-700">
                                Log Meal
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    /**
     * Load and display meals for a specific date
     * @param {Date} date - Date to load meals for
     */
    function loadMeals(date) {
        const logs = StorageModule.getItem('mealLogs', []);
        const dayLogs = logs.filter(log => log.date === date.toLocaleDateString());
        const foodList = document.getElementById('foodList');
        
        if (!foodList) return;
        
        if (dayLogs.length > 0) {
            // Calculate totals
            const totalCals = dayLogs.reduce((sum, log) => sum + (log.calories || 0), 0);
            const totalProtein = dayLogs.reduce((sum, log) => sum + (log.protein || 0), 0);
            
            // Display logged meals
            foodList.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-white">Meals for ${date.toLocaleDateString()}</h2>
                    <div class="text-sm">
                        <span class="bg-red-600 px-3 py-1 rounded">
                            Total: ${totalCals} cal | ${totalProtein}g protein
                        </span>
                    </div>
                </div>
                ${dayLogs.map((log, index) => `
                    <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 mb-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <h3 class="text-lg font-bold text-white">${log.name}</h3>
                                <span class="text-sm text-gray-400">Meal ${index + 1}</span>
                            </div>
                            <span class="bg-red-600 px-3 py-1 rounded text-sm">
                                ${log.calories} cal | P:${log.protein}g C:${log.carbs}g F:${log.fats}g
                            </span>
                        </div>
                    </div>
                `).join('')}
                <div class="flex gap-4 mt-6">
                    <button onclick="NutritionModule.displayAllMeals()" 
                        class="flex-1 bg-red-600 text-white py-2 rounded hover:bg-red-700">
                        Add Another Meal
                    </button>
                    <button onclick="NutritionModule.resetDayMeals('${date.toLocaleDateString()}')" 
                        class="px-4 bg-gray-700 text-white py-2 rounded hover:bg-gray-600">
                        Reset Day
                    </button>
                </div>
            `;
            updateDailyTotals(date);
        } else {
            displayAllMeals();
            updateDailyTotals(date);
        }
    }

    /**
     * Log a meal with nutrition data
     * @param {string} name - Meal name
     * @param {number} calories - Calories
     * @param {number} protein - Protein in grams
     * @param {number} carbs - Carbs in grams
     * @param {number} fats - Fats in grams
     */
    function logMeal(name, calories, protein, carbs, fats) {
        try {
            if (!name || !validateNutritionData(calories, protein, carbs, fats)) {
                UIModule.showToast('Invalid meal data', 'error');
                return;
            }

            const selectedDate = document.getElementById('selectedDate')?.textContent || new Date().toLocaleDateString();
            const data = {
                name,
                calories: Math.round(calories),
                protein: Math.round(protein),
                carbs: Math.round(carbs),
                fats: Math.round(fats),
                date: selectedDate,
                timestamp: Date.now()
            };
            
            StorageModule.addToArray('mealLogs', data);
            loadMeals(new Date(selectedDate));
            UIModule.showToast('Meal logged successfully!', 'success');
        } catch (error) {
            console.error('Error logging meal:', error);
            UIModule.showToast('Failed to log meal', 'error');
        }
    }

    function validateNutritionData(calories, protein, carbs, fats) {
        return (
            Number.isFinite(calories) && calories > 0 &&
            Number.isFinite(protein) && protein >= 0 &&
            Number.isFinite(carbs) && carbs >= 0 &&
            Number.isFinite(fats) && fats >= 0
        );
    }

    function showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 left-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Reset all meal data for a specific day
     * @param {string} dateString - Date string to reset
     */
    function resetDayMeals(dateString) {
        if (!dateString) {
            dateString = document.getElementById('selectedDate').textContent;
        }
        
        const confirmReset = confirm(`Are you sure you want to reset all meals for ${dateString}?`);
        if (!confirmReset) return;

        // Remove all logs for the selected date
        StorageModule.filterArray('mealLogs', log => log.date !== dateString);

        // Reload the meals display
        loadMeals(new Date(dateString));
    }

    /**
     * Generate a random meal suggestion
     */
    function generateMealSuggestion() {
        const typeKeys = Object.keys(mealTypes);
        const randomType = typeKeys[Math.floor(Math.random() * typeKeys.length)];
        const randomMeal = mealTypes[randomType].options[
            Math.floor(Math.random() * mealTypes[randomType].options.length)
        ];
        
        const foodList = document.getElementById('foodList');
        if (!foodList) return;

        foodList.innerHTML = `
            <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 mb-3">
                <div class="flex justify-between items-center">
                    <h3 class="text-lg font-bold text-white">${randomMeal.name}</h3>
                    <span class="bg-red-600 px-3 py-1 rounded text-sm">
                        ${randomMeal.calories} cal | P:${randomMeal.protein}g C:${randomMeal.carbs}g F:${randomMeal.fats}g
                    </span>
                </div>
                <button onclick="NutritionModule.logMeal('${randomMeal.name}', ${randomMeal.calories}, ${randomMeal.protein}, ${randomMeal.carbs}, ${randomMeal.fats})" 
                    class="mt-2 w-full bg-red-600 text-white py-2 rounded hover:bg-red-700">
                    Log Meal
                </button>
            </div>
        `;
    }

    /**
     * Update daily nutrition totals and targets
     * @param {Date} date - Date to calculate totals for
     */
    function updateDailyTotals(date) {
        const logs = StorageModule.getItem('mealLogs', []);
        const dayLogs = logs.filter(log => log.date === date.toLocaleDateString());
        
        // Get targets from localStorage or use defaults
        const targets = {
            calories: Number(localStorage.getItem('calorieTarget')) || 2000,
            protein: Number(localStorage.getItem('proteinTarget')) || 150,
            carbs: Number(localStorage.getItem('carbsTarget')) || 250,
            fats: Number(localStorage.getItem('fatsTarget')) || 55
        };

        // Calculate totals
        const totals = dayLogs.reduce((sum, log) => ({
            calories: sum.calories + (log.calories || 0),
            protein: sum.protein + (log.protein || 0),
            carbs: sum.carbs + (log.carbs || 0),
            fats: sum.fats + (log.fats || 0)
        }), { calories: 0, protein: 0, carbs: 0, fats: 0 });

        // Calculate remaining
        const remaining = {
            calories: Math.max(0, targets.calories - totals.calories),
            protein: Math.max(0, targets.protein - totals.protein),
            carbs: Math.max(0, targets.carbs - totals.carbs),
            fats: Math.max(0, targets.fats - totals.fats)
        };

        // Update display if elements exist
        updateElementText('totalCalories', totals.calories);
        updateElementText('totalProtein', `${totals.protein}g`);
        updateElementText('totalCarbs', `${totals.carbs}g`);
        updateElementText('totalFats', `${totals.fats}g`);

        updateElementText('calorieTarget', `${targets.calories}`);
        updateElementText('proteinTarget', `${targets.protein}g`);
        updateElementText('carbsTarget', `${targets.carbs}g`);
        updateElementText('fatsTarget', `${targets.fats}g`);

        updateElementText('caloriesRemaining', remaining.calories);
        updateElementText('proteinRemaining', `${remaining.protein}g`);
        updateElementText('carbsRemaining', `${remaining.carbs}g`);
        updateElementText('fatsRemaining', `${remaining.fats}g`);

        // Update colors based on progress
        ['calories', 'protein', 'carbs', 'fats'].forEach(nutrient => {
            const totalElement = document.getElementById(`total${nutrient.charAt(0).toUpperCase() + nutrient.slice(1)}`);
            const remainingElement = document.getElementById(`${nutrient}Remaining`);
            
            if (totalElement && remainingElement) {
                if (totals[nutrient] >= targets[nutrient]) {
                    totalElement.classList.remove('text-red-500');
                    totalElement.classList.add('text-green-500');
                    remainingElement.classList.remove('text-green-500');
                    remainingElement.classList.add('text-red-500');
                } else {
                    totalElement.classList.remove('text-green-500');
                    totalElement.classList.add('text-red-500');
                    remainingElement.classList.remove('text-red-500');
                    remainingElement.classList.add('text-green-500');
                }
            }
        });
    }

    /**
     * Helper to update text content if element exists
     * @param {string} id - Element ID
     * @param {string|number} text - Text to set
     */
    function updateElementText(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }

    // Public API
    return {
        displayAllMeals,
        loadMeals,
        logMeal,
        resetDayMeals,
        generateMealSuggestion
    };
})();