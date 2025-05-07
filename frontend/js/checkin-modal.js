/**
 * check-in-modal.js - Handles check-in modal functionality
 * This module manages the user check-in process, form submission, and API interactions
 */

// Global variables for check-in functionality
let activeCheckInDate = null;

// Initialize check-in modal functionality
function initCheckInModal() {
  // Get modal elements
  const modal = document.getElementById("checkinModal");
  const closeBtn = document.getElementById("closeModal");
  const form = document.getElementById("checkinForm");

  // Hide modal by default
  if (modal) {
    modal.style.display = "none";
  }

  // Close modal button handler
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }

  // Close when clicking outside modal content
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
  }

  // Replace the form's submit handler with our direct implementation
  if (form) {
    form.onsubmit = handleCheckInSubmit;
  }

  // Add "Check In" button to the UI
  addCheckInButton();

  // Modify today's cell click behavior
  modifyTodayCellClickBehavior();
}

// Add a "Check In" button to the calendar header
function addCheckInButton() {
  // Find the Today button
  const todayBtn = document.getElementById("todayBtn");

  if (todayBtn && todayBtn.parentElement) {
    // Create the check-in button
    const checkInBtn = document.createElement("button");
    checkInBtn.id = "checkInBtn";
    checkInBtn.className =
      "text-sm bg-red-700 hover:bg-red-800 px-4 py-2 rounded-md shadow";
    checkInBtn.textContent = "Check In";

    // Add click event
    checkInBtn.onclick = function () {
      openCheckInModal(new Date());
    };

    // Insert the button after Today
    todayBtn.parentElement.appendChild(checkInBtn);
    console.log("Check-in button added to header");
  }
}

// Modify the click behavior of today's cell
function modifyTodayCellClickBehavior() {
  // We need to override the createDayCell function to modify today's cell behavior
  if (typeof window.createDayCell === "function") {
    const originalCreateDayCell = window.createDayCell;

    window.createDayCell = function (day, isToday, hasEvent, date) {
      // Get the original cell
      const cell = originalCreateDayCell(day, isToday, hasEvent, date);

      // If this is today's cell, modify its click behavior
      if (isToday) {
        // Store the original click event
        const originalClickEvent = cell.onclick;

        // Override the click event
        cell.onclick = function (e) {
          // Remove any existing menus first
          const existingMenu = document.getElementById("today-cell-menu");
          if (existingMenu) {
            document.body.removeChild(existingMenu);
          }

          // Create a mini menu for check-in option
          const miniMenu = document.createElement("div");
          miniMenu.id = "today-cell-menu";
          miniMenu.className =
            "fixed bg-gray-800 border border-red-600 rounded-lg shadow-lg z-50 p-2";

          // Get the cell dimensions and position
          const cellRect = cell.getBoundingClientRect();

          // Set menu width to match cell width
          miniMenu.style.width = cellRect.width + "px";

          // Add check-in option
          const checkInOption = document.createElement("div");
          checkInOption.className =
            "py-2 px-3 hover:bg-red-700 cursor-pointer rounded text-white flex items-center";
          checkInOption.innerHTML =
            '<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Check In';

          checkInOption.onclick = function (evt) {
            evt.stopPropagation();
            document.body.removeChild(miniMenu);
            openCheckInModal(new Date(date));
          };

          miniMenu.appendChild(checkInOption);

          // Add view data option if there's event data
          if (hasEvent) {
            const viewOption = document.createElement("div");
            viewOption.className =
              "py-2 px-3 hover:bg-red-700 cursor-pointer rounded text-white flex items-center mt-1";
            viewOption.innerHTML =
              '<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg> View Data';

            viewOption.onclick = function (evt) {
              evt.stopPropagation();
              document.body.removeChild(miniMenu);
              // Call original click to show data
              if (originalClickEvent) originalClickEvent.call(cell, e);
            };

            miniMenu.appendChild(viewOption);
          }

          // Add close option
          const closeOption = document.createElement("div");
          closeOption.className =
            "py-2 px-3 hover:bg-red-700 cursor-pointer rounded text-white flex items-center mt-1";
          closeOption.innerHTML =
            '<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg> Close';

          closeOption.onclick = function (evt) {
            evt.stopPropagation();
            document.body.removeChild(miniMenu);
          };

          miniMenu.appendChild(closeOption);

          // Position the menu directly over the cell
          document.body.appendChild(miniMenu);
          miniMenu.style.position = "fixed";
          miniMenu.style.left = cellRect.left + "px";
          miniMenu.style.top = cellRect.top + "px";

          // Add click outside to close
          setTimeout(() => {
            const closeMenuOnClickOutside = function (evt) {
              if (!miniMenu.contains(evt.target) && evt.target !== cell) {
                if (document.body.contains(miniMenu)) {
                  document.body.removeChild(miniMenu);
                }
                document.removeEventListener("click", closeMenuOnClickOutside);
              }
            };
            document.addEventListener("click", closeMenuOnClickOutside);
          }, 100);

          // Stop propagation to prevent other handlers
          e.stopPropagation();
        };
      }

      return cell;
    };

    // Force a calendar refresh to apply our changes
    if (typeof window.renderCalendar === "function") {
      window.renderCalendar(new Date());
    }
  }
}

// Simple, direct form submission that guarantees values
async function handleCheckInSubmit(e) {
  e.preventDefault();
  console.log("Form submitted");

  // Get form elements directly
  const weightInput = document.getElementById("weight");
  const sleepSelect = document.getElementById("sleep");
  const energySelect = document.getElementById("energy");
  const stressSelect = document.getElementById("stress");
  const sorenessSelect = document.getElementById("soreness");
  const dateInput = document.getElementById("checkinDate");

  // Get and validate form values directly
  const weight = parseInt(weightInput.value) || 180; // Default weight if empty
  const sleep = parseInt(sleepSelect.value) || 5; // Default to middle value
  const energy = parseInt(energySelect.value) || 5; // Default to middle value
  const stress = parseInt(stressSelect.value) || 5; // Default to middle value
  const soreness = parseInt(sorenessSelect.value) || 5; // Default to middle value
  const checkInDate = dateInput.value || new Date().toISOString().split("T")[0];

  // Log all values to see what we're getting
  console.log("Direct form values:", {
    weight,
    sleep,
    energy,
    stress,
    soreness,
    check_in_date: checkInDate,
  });

  // Create data object with guaranteed values
  const checkInData = {
    weight: weight,
    sleep: sleep,
    energy: energy,
    stress: stress,
    soreness: soreness,
    check_in_date: checkInDate,
  };

  console.log("Data being sent to API:", checkInData);
  console.log("JSON string being sent:", JSON.stringify(checkInData));

  try {
    // Get authentication token
    const token = Credentials.getToken();

    // Send data to API
    const response = await fetch("/api/check-in", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(checkInData),
    });

    // Log the raw response status
    console.log("Response status:", response.status);

    // Get response as text
    const responseText = await response.text();
    console.log("Raw response:", responseText);

    // Check if response is successful
    if (!response.ok) {
      let errorMessage = "Failed to submit check-in";
      try {
        const errorData = JSON.parse(responseText);
        errorMessage =
          errorData.error || errorData["Validation error"] || errorMessage;
      } catch (e) {
        console.error("Error parsing error response:", e);
      }
      throw new Error(errorMessage);
    }

    // Success! Store additional UI data
    const workoutInput = document.getElementById("workout");
    const nutritionInput = document.getElementById("nutrition");

    const additionalData = {
      workout: workoutInput.value || "",
      nutrition: parseInt(nutritionInput.value) || 0,
    };

    // Update local events data
    updateLocalEventsData({
      ...checkInData,
      ...additionalData,
    });

    // Close modal
    const modal = document.getElementById("checkinModal");
    if (modal) modal.style.display = "none";

    // Reload events data and refresh calendar
    await loadEventsForMonth(
      activeCheckInDate.getFullYear(),
      activeCheckInDate.getMonth(),
    );

    renderCalendar(new Date(activeCheckInDate));
    updateSidebar(activeCheckInDate);

    // Show success notification
    showNotification("Check-in submitted successfully!");
  } catch (err) {
    console.error("Error submitting check-in:", err);
    // Show error notification
    showNotification("Failed to submit check-in: " + err.message, "error");
  }
}

// Simplify the openCheckInModal function as well
function openCheckInModal(date) {
  console.log("Opening check-in modal for date:", date);

  // Set active date for form submission
  activeCheckInDate = date;

  // Format date for display
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  // Get the modal
  const modal = document.getElementById("checkinModal");
  if (!modal) {
    console.error("Check-in modal not found");
    return;
  }

  // Update modal title
  const modalTitle = modal.querySelector("h2");
  if (modalTitle) {
    modalTitle.textContent = `Daily Check-In: ${formattedDate}`;
  }

  // Format date for API (YYYY-MM-DD)
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const formattedDateForAPI = `${year}-${month}-${day}`;

  // Set the date input directly
  const dateInput = document.getElementById("checkinDate");
  if (dateInput) {
    dateInput.value = formattedDateForAPI;
  }

  // Reset form and set defaults
  const form = document.getElementById("checkinForm");
  if (form) {
    // Reset the form first
    form.reset();

    // Then set default values for all fields
    document.getElementById("weight").value = "180";
    document.getElementById("sleep").value = "5";
    document.getElementById("energy").value = "5";
    document.getElementById("stress").value = "5";
    document.getElementById("soreness").value = "5";

    // Set date again after reset
    dateInput.value = formattedDateForAPI;
  }

  // Try to pre-populate with existing data if available
  const yearKey = date.getFullYear();
  const monthKey = date.getMonth();
  const dayKey = date.getDate();

  if (
    events[yearKey] &&
    events[yearKey][monthKey] &&
    events[yearKey][monthKey][dayKey]
  ) {
    const eventData = events[yearKey][monthKey][dayKey];

    // Set form values directly
    if (eventData.weight)
      document.getElementById("weight").value = eventData.weight;
    if (eventData.sleep)
      document.getElementById("sleep").value = eventData.sleep;
    if (eventData.energy)
      document.getElementById("energy").value = eventData.energy;
    if (eventData.stress)
      document.getElementById("stress").value = eventData.stress;
    if (eventData.soreness)
      document.getElementById("soreness").value = eventData.soreness;
    if (eventData.workout)
      document.getElementById("workout").value = eventData.workout;
    if (eventData.nutrition)
      document.getElementById("nutrition").value = eventData.nutrition;
  }

  // Show the modal
  modal.style.display = "flex";
}

// Update local events data with check-in info
function updateLocalEventsData(checkInData) {
  // Parse the date
  const date = new Date(checkInData.check_in_date);
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();

  // Initialize event structure if not exists
  if (!events[year]) events[year] = {};
  if (!events[year][month]) events[year][month] = {};
  if (!events[year][month][day]) events[year][month][day] = {};

  // Calculate readiness score based on sleep, energy, stress, and soreness
  // Sleep and energy are positive factors (higher is better)
  // Stress and soreness are negative factors (higher is worse)
  // Convert 1-10 scale to a percentage (0-100)
  const readiness = Math.round(
    ((parseInt(checkInData.sleep) +
      parseInt(checkInData.energy) +
      (11 - parseInt(checkInData.stress)) +
      (11 - parseInt(checkInData.soreness))) /
      40) *
      100,
  );

  // Update event data
  events[year][month][day] = {
    ...events[year][month][day], // Keep any existing data
    ...checkInData, // Add new check-in data
    readiness: Math.max(0, Math.min(100, readiness)), // Ensure readiness is between 0-100
  };
}

// Helper function to set input value safely
function setInputValue(inputId, value) {
  const input = document.getElementById(inputId);
  if (input && value !== undefined && value !== null) {
    input.value = value;
  }
}

// Helper function to set select dropdown value
function setSelectValue(selectId, value) {
  const select = document.getElementById(selectId);
  if (select && value !== undefined && value !== null) {
    for (let i = 0; i < select.options.length; i++) {
      if (select.options[i].value == value) {
        // Using == instead of === for type coercion
        select.selectedIndex = i;
        break;
      }
    }
  }
}

// Show a notification message
function showNotification(message, type = "success") {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `fixed bottom-4 right-4 p-4 rounded-lg text-white ${
    type === "success" ? "bg-green-600" : "bg-red-600"
  } shadow-lg z-50 transition-opacity duration-500`;
  notification.textContent = message;

  // Add to document
  document.body.appendChild(notification);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = "0";
    setTimeout(() => notification.remove(), 500);
  }, 3000);
}

// Initialize check-in functionality when document is loaded
document.addEventListener("DOMContentLoaded", function () {
  console.log("Document loaded, initializing check-in module");

  // Wait for calendar to be fully rendered
  setTimeout(function () {
    initCheckInModal();
  }, 500);
});
