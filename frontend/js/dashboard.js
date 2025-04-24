/**
 * dashboard.js - Main JavaScript for the COACH dashboard
 * Handles dashboard initialization, chart rendering, and UI interactions
 */

// dashboard.js

document.addEventListener("DOMContentLoaded", () => {
  renderCalendar(new Date());
});

function renderCalendar(date) {
  const calendarGrid = document.getElementById("calendar-grid");
  const calendarTitle = document.getElementById("calendarTitle");

  const year = date.getFullYear();
  const month = date.getMonth(); // 0-indexed
  const monthName = date.toLocaleString('default', { month: 'long' });

  // Update header
  calendarTitle.textContent = `${monthName} ${year}`;
  calendarGrid.innerHTML = ""; // Clear previous

  // Get start day and number of days
  const firstDay = new Date(year, month, 1).getDay(); // 0 = Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = firstDay + daysInMonth;
  const rows = Math.ceil(totalCells / 7);

  // Set grid rows dynamically
  calendarGrid.style.gridTemplateRows = `repeat(${rows}, minmax(0, 1fr))`;

  // Fill leading empty cells
  for (let i = 0; i < firstDay; i++) {
    calendarGrid.appendChild(createEmptyCell());
  }

  // Fill actual days
  for (let day = 1; day <= daysInMonth; day++) {
    calendarGrid.appendChild(createDayCell(day));
  }
}

function createEmptyCell() {
  const div = document.createElement("div");
  div.className = "bg-gray-900 border border-gray-700";
  return div;
}

function createDayCell(day) {
  const div = document.createElement("div");
  div.className = "bg-gray-900 border border-gray-700 p-2 flex flex-col justify-between text-sm";
  div.innerHTML = `
    <div class="text-gray-400 font-semibold">${day}</div>
    <div class="text-xs text-gray-500 italic">No events</div>
  `;
  return div;
}

