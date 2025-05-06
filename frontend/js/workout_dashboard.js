/**
 * COACH Workout Dashboard Module
 * Initializes the workout page, calendar, and connects UI elements to WorkoutModule functions.
 */
const WorkoutDashboard = (() => {
  // Private variables
  const config = {
    // apiEndpoint: '/api/workouts', // Keep if needed for other dashboard actions
    homePath: "/dashboard", // Path to navigate home
  };

  /**
   * Initialize the workout dashboard page
   */
  const initialize = () => {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("Workout Dashboard Module initializing...");

      // Check dependencies
      if (typeof CalendarModule === "undefined") {
        console.error("Required module CalendarModule not found!");
        // return; // Allow partial functionality if calendar fails
      }
      if (typeof WorkoutModule === "undefined") {
        console.error("Required module WorkoutModule not found!");
        alert("Error: Workout functionality failed to load."); // Critical dependency
        return;
      }

      // Initialize calendar (if available)
      if (
        typeof CalendarModule !== "undefined" &&
        CalendarModule.initializeCalendar
      ) {
        // Pass a callback to the calendar to load workout when date changes
        CalendarModule.initializeCalendar((dateString) => {
          if (WorkoutModule.loadWorkout) {
            WorkoutModule.loadWorkout(dateString);
          }
        });
      } else {
        console.warn("Calendar module not fully initialized.");
      }

      // Initial load for today's workout
      const today = new Date().toISOString().split("T")[0];
      if (WorkoutModule.loadWorkout) {
        WorkoutModule.loadWorkout(today);
      } else {
        console.error(
          "WorkoutModule.loadWorkout is not available for initial load.",
        );
      }

      // Set today's date as the default workout date input value (redundant if loadWorkout works, but safe)
      const workoutDateInput = document.getElementById("workoutDate");
      if (workoutDateInput) {
        workoutDateInput.value = today;
      }

      // Initialize event listeners for buttons
      initializeEventListeners();

      console.log("Workout Dashboard initialized.");
    });
  };

  /**
   * Initialize all event listeners for the workout page buttons
   */
  const initializeEventListeners = () => {
    // Home button
    const homeBtn = document.getElementById("homeButton");
    if (homeBtn) {
      homeBtn.addEventListener("click", () => {
        window.location.href = config.homePath; // Navigate home
      });
    } else {
      console.warn("Home button not found.");
    }

    // Get Recommendations button
    const recommendationsBtn = document.getElementById("getRecommendationsBtn");
    if (recommendationsBtn) {
      recommendationsBtn.addEventListener("click", () => {
        if (WorkoutModule.getRecommendations) {
          WorkoutModule.getRecommendations();
        } else {
          console.error("WorkoutModule.getRecommendations not found");
          alert("Error: Could not get recommendations.");
        }
      });
    } else {
      console.warn("Get Recommendations button not found.");
    }

    // Reset Day button
    const resetBtn = document.getElementById("resetDayBtn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        if (WorkoutModule.resetDayWorkout) {
          // Ask for confirmation before resetting
          if (
            confirm(
              "Are you sure you want to clear the workout for this day? Unsaved changes will be lost.",
            )
          ) {
            WorkoutModule.resetDayWorkout(true); // Pass true to reload after reset
          }
        } else {
          console.error("WorkoutModule.resetDayWorkout not found");
          alert("Error: Could not reset workout.");
        }
      });
    } else {
      console.warn("Reset Day button not found.");
    }

    // Workout type buttons
    const workoutTypeBtns = document.querySelectorAll(".workout-type-btn");
    if (workoutTypeBtns.length > 0) {
      workoutTypeBtns.forEach((btn) => {
        const workoutType = btn.dataset.workoutType; // Get type from data attribute
        if (workoutType) {
          btn.addEventListener("click", () => {
            if (WorkoutModule.generateWorkout) {
              // Optional: Confirm before overwriting existing workout
              // if (WorkoutModule.getCurrentWorkout().exercises.length > 0 && !confirm("Generate a new workout? This will replace the current exercises.")) {
              //     return;
              // }
              WorkoutModule.generateWorkout(workoutType);
            } else {
              console.error("WorkoutModule.generateWorkout not found");
              alert("Error: Could not generate workout.");
            }
          });
        } else {
          console.warn(
            "Workout type button found without data-workout-type attribute:",
            btn,
          );
        }
      });
    } else {
      console.warn("No workout type buttons found.");
    }

    // Save Workout button
    const saveBtn = document.getElementById("saveWorkoutBtn");
    if (saveBtn) {
      saveBtn.addEventListener("click", () => {
        if (WorkoutModule.saveWorkout) {
          WorkoutModule.saveWorkout(); // Delegate saving logic to WorkoutModule
        } else {
          console.error("WorkoutModule.saveWorkout not found");
          alert("Error: Could not save workout.");
        }
      });
    } else {
      console.warn("Save Workout button not found.");
    }

    // Listen for changes in duration/notes inputs to update state (optional, but good practice)
    const workoutDurationInput = document.getElementById("workoutDuration");
    const workoutNotesInput = document.getElementById("workoutNotes");

    if (workoutDurationInput) {
      workoutDurationInput.addEventListener("change", (e) => {
        // Optionally update WorkoutModule state immediately, or rely on getCurrentWorkout reading it
        // console.log('Duration changed:', e.target.value);
      });
    }
    if (workoutNotesInput) {
      workoutNotesInput.addEventListener("change", (e) => {
        // Optionally update WorkoutModule state immediately
        // console.log('Notes changed:', e.target.value);
      });
    }
  };

  // Public API
  return {
    initialize,
  };
})();

// Initialize the module when the script loads
WorkoutDashboard.initialize();
