/**
 * dashboard.js - Main JavaScript for the COACH dashboard
 * Handles dashboard initialization, chart rendering, and UI interactions
 */

// dashboard.js

let currentDate = new Date();

document.addEventListener("DOMContentLoaded", () => {
  setupMonthYearPickers();
  renderCalendar(currentDate);

  document.getElementById("prevMonth").onclick = () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar(currentDate);
  };

  document.getElementById("nextMonth").onclick = () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar(currentDate);
  };
   document.getElementById("todayBtn").onclick = () => {
    currentDate = new Date();
    renderCalendar(currentDate);
  };
});

function setupMonthYearPickers() {
  const months = [...Array(12).keys()].map(m => new Date(0, m).toLocaleString('default', { month: 'long' }));
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

  monthBtn.onclick = () => dropdown.classList.toggle("show");

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

  yearBtn.onclick = () => yearDropdown.classList.toggle("show");
}

function renderCalendar(date) {
  const calendarGrid = document.getElementById("calendar-grid");
  const monthBtn = document.getElementById("monthBtn");
  const yearBtn = document.getElementById("yearBtn");

  const year = date.getFullYear();
  const month = date.getMonth();
  const monthName = date.toLocaleString('default', { month: 'long' });

  monthBtn.textContent = monthName;
  yearBtn.textContent = year;
  calendarGrid.innerHTML = "";

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = firstDay + daysInMonth;
  const rows = Math.ceil(totalCells / 7);
  calendarGrid.style.gridTemplateRows = `repeat(${rows}, minmax(0, 1fr))`;

  for (let i = 0; i < firstDay; i++) {
    calendarGrid.appendChild(createEmptyCell());
  }

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

