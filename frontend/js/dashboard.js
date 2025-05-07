/**
 * dashboard.js - Main JavaScript for the COACH dashboard
 * Handles dashboard initialization, chart rendering, and UI interactions
 */

// Check if logged in, redirect if not - with a small delay to ensure token is available
document.addEventListener("DOMContentLoaded", () => {
  // Add a small delay to check authentication to allow for token processing
  setTimeout(() => {
    if (!Credentials.isAuthenticated()) {
      window.location.href = "../index.html";
    }
  }, 500); // 500ms delay gives time for token to be properly set
});

// Global variables
let currentDate = new Date();
let events = {};

// Functionality for logout button
document.getElementById("logoutBtn").addEventListener("click", () => {
  Credentials.clearToken(); // Clears JWT from localStorage
  window.location.href = "/"; // Redirect to front page
});

// Load actual event data
async function loadEventsForMonth(year, month) {
  try {
    const token = Credentials.getToken();

    const [workoutRes, checkinRes] = await Promise.all([
      fetch(`/api/workouts?year=${year}&month=${month + 1}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`/api/check-ins?year=${year}&month=${month + 1}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ]);

    const [workoutData, checkinData] = await Promise.all([
      workoutRes.json(),
      checkinRes.json(),
    ]);

    if (!workoutRes.ok || !checkinRes.ok) {
      console.error(
        "Error loading events:",
        workoutData.error || checkinData.error,
      );
      events = {};
      return;
    }

    // 🧠 Merge logic
    events = {};

    const mergeSource = [workoutData, checkinData];
    for (const source of mergeSource) {
      for (const yearKey in source) {
        if (!events[yearKey]) events[yearKey] = {};
        for (const monthKey in source[yearKey]) {
          if (!events[yearKey][monthKey]) events[yearKey][monthKey] = {};
          for (const dayKey in source[yearKey][monthKey]) {
            if (!events[yearKey][monthKey][dayKey])
              events[yearKey][monthKey][dayKey] = {};

            Object.assign(
              events[yearKey][monthKey][dayKey],
              source[yearKey][monthKey][dayKey],
            );
          }
        }
      }
    }
    console.log("Merged events:", events);
  } catch (err) {
    console.error("Network error loading events:", err);
    events = {};
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Calendar: Load events for the month
  loadEventsForMonth(currentDate.getFullYear(), currentDate.getMonth()).then(
    () => {
      renderCalendar(currentDate);
      updateSidebar(new Date());
    },
  );

  // Set up month/year pickers and render calendar
  setupMonthYearPickers();
  renderCalendar(currentDate);
  updateSidebar(new Date()); // Show today's data in sidebar

  // Previous/Next month handlers
  document.getElementById("prevMonth").onclick = () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    loadEventsForMonth(currentDate.getFullYear(), currentDate.getMonth()).then(
      () => {
        renderCalendar(currentDate);
      },
    );
  };

  document.getElementById("nextMonth").onclick = () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    loadEventsForMonth(currentDate.getFullYear(), currentDate.getMonth()).then(
      () => {
        renderCalendar(currentDate);
      },
    );
  };

  document.getElementById("todayBtn").onclick = () => {
    currentDate = new Date();
    loadEventsForMonth(currentDate.getFullYear(), currentDate.getMonth()).then(
      () => {
        renderCalendar(currentDate);
      },
    );
    updateSidebar(currentDate);
  };

  // Close dropdowns when clicking outside
  document.addEventListener("click", (event) => {
    const monthDropdown = document.getElementById("monthDropdown");
    const yearDropdown = document.getElementById("yearDropdown");
    const monthBtn = document.getElementById("monthBtn");
    const yearBtn = document.getElementById("yearBtn");

    if (
      !monthBtn.contains(event.target) &&
      !monthDropdown.contains(event.target)
    ) {
      monthDropdown.classList.remove("show");
    }

    if (
      !yearBtn.contains(event.target) &&
      !yearDropdown.contains(event.target)
    ) {
      yearDropdown.classList.remove("show");
    }
  });

  // Close modal box
  document.getElementById("closeModal").onclick = () => {
    document.getElementById("dayModal").classList.add("hidden");
  };
  window.addEventListener("click", (e) => {
    const modal = document.getElementById("dayModal");
    if (e.target === modal) modal.classList.add("hidden");
  });
});

// Set up the month/year dropdown pickers
function setupMonthYearPickers() {
  // Setup month picker
  const months = [...Array(12).keys()].map((m) =>
    new Date(0, m).toLocaleString("default", { month: "long" }),
  );
  const monthList = document.querySelector("#monthDropdown ul");
  const monthBtn = document.getElementById("monthBtn");
  const dropdown = document.getElementById("monthDropdown");

  months.forEach((name, index) => {
    const li = document.createElement("li");
    li.textContent = name;
    li.className = "px-4 py-2 hover:bg-red-700 cursor-pointer";
    li.onclick = () => {
      currentDate.setMonth(index);
      renderCalendar(currentDate);
      dropdown.classList.remove("show");
    };
    monthList.appendChild(li);
  });

  monthBtn.onclick = (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  };

  // Setup year picker
  const yearList = document.querySelector("#yearDropdown ul");
  const yearBtn = document.getElementById("yearBtn");
  const yearDropdown = document.getElementById("yearDropdown");
  const thisYear = new Date().getFullYear();

  for (let y = thisYear - 10; y <= thisYear + 10; y++) {
    const li = document.createElement("li");
    li.textContent = y;
    li.className = "px-4 py-2 hover:bg-red-700 cursor-pointer";
    li.onclick = () => {
      currentDate.setFullYear(y);
      renderCalendar(currentDate);
      yearDropdown.classList.remove("show");
    };
    yearList.appendChild(li);
  }

  yearBtn.onclick = (e) => {
    e.stopPropagation();
    yearDropdown.classList.toggle("show");
  };
}

// Render the calendar grid for a given month
function renderCalendar(date) {
  const calendarGrid = document.getElementById("calendar-grid");
  const monthBtn = document.getElementById("monthBtn");
  const yearBtn = document.getElementById("yearBtn");

  const year = date.getFullYear();
  const month = date.getMonth();
  const monthName = date.toLocaleString("default", { month: "long" });
  const today = new Date();

  monthBtn.textContent = monthName;
  yearBtn.textContent = year;
  calendarGrid.innerHTML = "";

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = firstDay + daysInMonth;
  const rows = Math.ceil(totalCells / 7);
  calendarGrid.style.gridTemplateRows = `repeat(${rows}, minmax(0, 1fr))`;

  // Create empty cells for days before the 1st of the month
  for (let i = 0; i < firstDay; i++) {
    calendarGrid.appendChild(createEmptyCell());
  }

  // Create cells for each day of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday =
      today.getDate() === day &&
      today.getMonth() === month &&
      today.getFullYear() === year;

    const hasEvent =
      events[year] && events[year][month] && events[year][month][day];

    const cellDate = new Date(year, month, day);
    const cell = createDayCell(day, isToday, hasEvent, cellDate);

    calendarGrid.appendChild(cell);
  }
}

// Create an empty cell for days before/after the month
function createEmptyCell() {
  const div = document.createElement("div");
  div.className = "calendar-cell";
  return div;
}

// Create a day cell with event indicators
function createDayCell(day, isToday, hasEvent, date) {
  const div = document.createElement("div");

  // Add base classes
  div.className = `
    relative calendar-cell p-2 text-sm
    transition-all duration-300 ease-in-out
    rounded-lg cursor-pointer flex flex-col justify-between
    hover:scale-105 hover:z-30 hover:shadow-[0_0_20px_rgba(91,92,69,0.3)]
  `;

  // Mark as today
  if (isToday) {
    div.classList.add(
      "bg-[var(--button)]",
      "text-[var(--bg-alt)]",
      "border",
      "border-[var(--primary)]",
    );
    div.dataset.today = "true"; // used to retain styling after click
  } else {
    div.classList.add("bg-[var(--bg-light)]", "text-[var(--button)]"); // fallback bg and text
  }

  div.innerHTML = `
    <div class="day-number font-semibold text-base">${day}</div>
    <div class="click-hint text-xs text-[var(--text-secondary)]">${hasEvent ? "Click to view" : ""}</div>
  `;

  if (isToday && hasEvent) {
    div.querySelector(".click-hint").classList.add("text-white");
  }

  // Indicator
  if (hasEvent) {
    const eventData = events[date.getFullYear()][date.getMonth()][day];
    const indicator = document.createElement("div");
    indicator.className = eventData.isScheduled
      ? "absolute top-1 right-1 w-2 h-2 rounded-full bg-blue-500"
      : "absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500";
    div.appendChild(indicator);
  }

  // Click to show modal and highlight
  div.addEventListener("click", () => {
    updateSidebar(date);

    // Clean up preview if it exists
    const existingPreview = div.querySelector(".event-preview");
    if (existingPreview) existingPreview.remove();

    // Hide the click hint (if it's still there)
    const hint = div.querySelector(".click-hint");
    if (hint) hint.style.display = "none";

    document
      .querySelectorAll("#calendar-grid .calendar-cell")
      .forEach((cell) => {
        cell.classList.remove(
          "bg-[var(--background)]",
          "border-[var(--primary)]",
          "text-[var(--text)]",
        );
        if (cell.dataset.today === "true") {
          cell.classList.add("bg-[var(--button)]", "text-[var(--bg-alt)]");
        } else {
          cell.classList.add("bg-[var(--bg-light)]", "text-[var(--button)]");
        }
      });

    div.classList.remove("bg-[var(--bg-light)]", "text-[var(--button)]");
    div.classList.add(
      "bg-[var(--background)]",
      "border",
      "border-[var(--primary)]",
      "text-[var(--text)]",
    );

    // Show modal
    const modal = document.getElementById("dayModal");
    const modalContent = document.getElementById("modalContent");
    const d = date.getDate();
    const eventData = hasEvent
      ? events[date.getFullYear()][date.getMonth()][d]
      : null;
    modalContent.innerHTML = eventData
      ? `
        <p><strong>Workout:</strong> ${eventData.workout}</p>
        <p><strong>Nutrition:</strong> ${eventData.nutrition}</p>
        <p><strong>Sleep:</strong> ${eventData.sleep}</p>
        <p><strong>Energy:</strong> ${eventData.energy}</p>
        <p><strong>Readiness:</strong> ${eventData.readiness}%</p>
      `
      : `<p>No data available for this day.</p>`;
    modal.classList.remove("hidden");
  });

  // Hover preview
  div.addEventListener("mouseenter", () => {
    if (hasEvent) {
      const year = date.getFullYear();
      const month = date.getMonth();
      const dayNum = date.getDate();
      const eventData = events[year]?.[month]?.[dayNum];

      if (!eventData) return; // Exit early if no data


      const hint = div.querySelector(".click-hint");
      if (hint) hint.style.display = "none";

      const preview = document.createElement("div");
      preview.className = `event-preview mt-1 text-xs font-semibold`;

      // Check if it's today by class or dataset
      const isToday = div.classList.contains("bg-[var(--button)]");

      // Set text color based on background
      preview.classList.add(isToday ? "text-white" : "text-gray-500");

      preview.innerHTML = `
        💤 ${eventData.sleep || "N/A"}<br>
        ⚡ ${eventData.energy || "N/A"}<br>
        🏋️ ${eventData.workout || "Not logged"}
      `;
      div.appendChild(preview);
    }
  });

  div.addEventListener("mouseleave", () => {
    const preview = div.querySelector(".event-preview");
    if (preview) preview.remove();

    const hint = div.querySelector(".click-hint");
    if (hint && !div.classList.contains("selected")) {
      hint.style.display = "block";
    }
  });

  return div;
}

// Update the sidebar with the selected date's information
function updateSidebar(date) {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();

  // Get aside elements
  const strengthSection = document.querySelector("aside div:nth-child(1)");
  const nutritionSection = document.querySelector("aside div:nth-child(2)");
  const coachSection = document.querySelector("aside div:nth-child(3)");

  // Format date for display
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  // Check if we have data for this date
  if (events[year] && events[year][month] && events[year][month][day]) {
    const eventData = events[year][month][day];

    // Update Strength & Conditioning section
    strengthSection.innerHTML = `
      <h3 class="side-header text-lg font-bold">Strength & Conditioning</h3>
      <p class="mt-2 text-sm">
        <span class="block mb-1">${formattedDate}</span>
        <span class="block mb-1">Workout: ${eventData.workout}</span>
        <span class="block">Readiness: ${eventData.readiness}%</span>
      </p>
    `;

    // Update Nutrition section
    nutritionSection.innerHTML = `
      <h3 class="side-header text-lg font-bold">Nutrition</h3>
      <p class="mt-2 text-sm">
        <span class="block mb-1">Calories: ${eventData.nutrition}</span>
        <span class="block">Hydration: 3.2L</span>
      </p>
    `;

    // Update Head Coach section
    let coachMessage =
      "Great job sticking to your program! Keep up the good work.";

    if (eventData.isScheduled) {
      coachMessage =
        "This is your upcoming plan. Make sure to prepare for your workout.";
    } else if (eventData.readiness < 80) {
      coachMessage =
        "Your recovery indicators suggest you might need more rest.";
    }

    coachSection.innerHTML = `
      <h3 class="side-header text-lg font-bold">Head Coach</h3>
      <p class="mt-2 text-sm">"${coachMessage}"</p>
    `;
  } else {
    // No data for this date
    strengthSection.innerHTML = `
      <h3 class="side-header text-lg font-bold">Strength & Conditioning</h3>
      <p class="mt-2 text-sm">
        <span class="block mb-1">${formattedDate}</span>
        <span class="block mb-1">No workout data</span>
        <span class="block">Add a workout to track your progress</span>
      </p>
    `;

    nutritionSection.innerHTML = `
      <h3 class="side-header text-lg font-bold">Nutrition</h3>
      <p class="mt-2 text-sm">
        <span class="block mb-1">No nutrition data</span>
        <span class="block">Log your meals to track calories</span>
      </p>
    `;

    coachSection.innerHTML = `
      <h3 class="text-[var(--primary)] text-lg font-bold">Head Coach</h3>
      <p class="mt-2 text-sm">"Select a date with data or add new activity to see your personalized advice."</p>
    `;
  }
}
