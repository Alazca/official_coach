/**
 * COACH Food Logger Module
 * Handles all functionality related to logging food and meal tracking
 */
const FoodLoggerModule = (() => {
  // Private variables
  let currentDate = new Date();

  /**
   * Initialize the food logger components
   */
  const initialize = () => {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("Food Logger Module initializing...");

      // Check dependencies
      if (
        typeof NutritionModule === "undefined" ||
        typeof CalendarModule === "undefined"
      ) {
        console.error(
          "Required modules (NutritionModule or CalendarModule) not found!",
        );
        return;
      }

      // Initialize calendar and nutrition components
      CalendarModule.initializeCalendar();
      NutritionModule.displayAllMeals();

      // Set today's date as the default food date
      const today = new Date().toISOString().split("T")[0];
      const foodDateInput = document.getElementById("foodDate");
      if (foodDateInput) {
        foodDateInput.value = today;
      }

      // Set up event listeners
      initializeEventListeners();
      initializeFoodItemManager();

      // Connect the Save Food Log button with the API
      setupSaveButton();
    });
  };

  /**
   * Initialize all event listeners for the food logger
   */
  const initializeEventListeners = () => {
    // Setup Reset Day button
    const resetButton = document.querySelector(
      'button[onclick="resetDayMeals()"]',
    );

    // --------------------- Home Button ---------------------
    const homeButton = document.getElementById("homeButton");
    if (homeButton) {
      homeButton.addEventListener("click", () => {
        // Navigate to root; adjust if your home route differs
        window.location.href = "/dashboard";
      });
    }

    if (resetButton) {
      // Replace the inline handler with a proper event listener
      resetButton.removeAttribute("onclick");
      resetButton.addEventListener("click", () => {
        if (
          typeof NutritionModule !== "undefined" &&
          NutritionModule.resetDayMeals
        ) {
          NutritionModule.resetDayMeals();
        } else {
          console.error("NutritionModule.resetDayMeals not found");
        }
      });
    }

    // Setup Generate Meal Suggestions button
    const generateButton = document.querySelector(
      'button[onclick="NutritionModule.generateMealSuggestion()"]',
    );
    if (generateButton) {
      // Replace the inline handler with a proper event listener
      generateButton.removeAttribute("onclick");
      generateButton.addEventListener("click", () => {
        if (
          typeof NutritionModule !== "undefined" &&
          NutritionModule.generateMealSuggestion
        ) {
          NutritionModule.generateMealSuggestion();
        } else {
          console.error("NutritionModule.generateMealSuggestion not found");
        }
      });
    }
  };

  /**
   * Initialize the food item row management (add/remove)
   */
  const initializeFoodItemManager = () => {
    // Initialize add food item button functionality
    const addFoodItemBtn = document.getElementById("addFoodItemBtn");
    if (addFoodItemBtn) {
      addFoodItemBtn.addEventListener("click", addNewFoodItemRow);
    }

    // Add remove functionality to initial food item
    const initialRemoveBtn = document.querySelector(".remove-food");
    if (initialRemoveBtn) {
      initialRemoveBtn.addEventListener("click", handleRemoveFoodItem);
    }
  };

  /**
   * Add a new food item row to the container
   */
  const addNewFoodItemRow = () => {
    const container = document.getElementById("foodItemsContainer");
    if (!container) return;

    const newRow = document.createElement("div");
    newRow.className = "food-item-row grid grid-cols-12 gap-2";
    newRow.innerHTML = `
      <div class="col-span-6">
        <input type="text" placeholder="Food name" class="food-name w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-1 focus:ring-red-500 text-sm">
      </div>
      <div class="col-span-3">
        <input type="text" placeholder="Serving" class="serving-size w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-1 focus:ring-red-500 text-sm">
      </div>
      <div class="col-span-2">
        <input type="number" placeholder="Kcal" class="food-calories w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-1 focus:ring-red-500 text-sm">
      </div>
      <div class="col-span-1 flex items-center justify-center">
        <button type="button" class="remove-food text-red-500 hover:text-red-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    `;
    container.appendChild(newRow);

    // Add event listener to the remove button
    newRow
      .querySelector(".remove-food")
      .addEventListener("click", handleRemoveFoodItem);
  };

  /**
   * Handle removing a food item row
   */
  const handleRemoveFoodItem = function () {
    const container = document.getElementById("foodItemsContainer");
    if (!container) return;

    if (container.children.length > 1) {
      this.closest(".food-item-row").remove();
    } else {
      // Clear inputs instead of removing if it's the last row
      const row = this.closest(".food-item-row");
      if (row) {
        const nameInput = row.querySelector(".food-name");
        const servingInput = row.querySelector(".serving-size");
        const caloriesInput = row.querySelector(".food-calories");

        if (nameInput) nameInput.value = "";
        if (servingInput) servingInput.value = "";
        if (caloriesInput) caloriesInput.value = "";
      }
    }
  };

  /**
   * Collect all food item data from the form
   * @returns {Array} Array of food items
   */
  const collectFoodItems = () => {
    const foodItems = [];
    const rows = document.querySelectorAll(".food-item-row");

    rows.forEach((row) => {
      const nameInput = row.querySelector(".food-name");
      const servingInput = row.querySelector(".serving-size");
      const caloriesInput = row.querySelector(".food-calories");

      // Only add items that have at least a name
      if (nameInput && nameInput.value.trim()) {
        foodItems.push({
          name: nameInput.value.trim(),
          serving: servingInput ? servingInput.value.trim() : "",
          calories: caloriesInput ? parseInt(caloriesInput.value, 10) || 0 : 0,
        });
      }
    });

    return foodItems;
  };

  /**
   * Set up the save button to use the CoachUtils API
   */
  const setupSaveButton = () => {
    const saveButton = document.getElementById("logFoodBtn");
    if (!saveButton) return;

    saveButton.addEventListener("click", () => {
      // Collect form data
      const foodDate = document.getElementById("foodDate")?.value;
      const mealType = document.getElementById("mealType")?.value;
      const foodItems = collectFoodItems();

      // Validate data
      if (!foodDate || !mealType || foodItems.length === 0) {
        alert(
          "Please fill out all required fields and add at least one food item.",
        );
        return;
      }

      // Prepare data for API
      const mealData = {
        date: foodDate,
        mealType: mealType,
        items: foodItems,
      };

      // Send data to API
      if (window.CoachUtils) {
        window.CoachUtils.sendPostAndRedirect(
          "/api/meals",
          mealData,
          "visualize_data.html",
          (result) => {
            console.log("Meal logged successfully:", result);
          },
          (error) => {
            console.error("Error logging meal:", error);
          },
        );
      } else {
        console.error(
          "CoachUtils not loaded. Make sure utils.js is included before food_logger.js",
        );
      }
    });
  };

  // Public API
  return {
    initialize,
    addNewFoodItemRow,
    collectFoodItems,
  };
})();

// Initialize the module when loaded
FoodLoggerModule.initialize();
