/**
 * calendar.js
 * Calendar functionality for date selection
 */

const CalendarModule = (function() {
    // Current date being displayed in the calendar
    let currentCalendarDate = new Date();
    
    /**
     * Initialize calendar component on the page
     */
    function initializeCalendar() {
        const currentMonth = document.getElementById('currentMonth');
        const calendarDays = document.getElementById('calendarDays');
        
        if (!currentMonth || !calendarDays) return;
        
        // Add month navigation
        document.getElementById('prevMonth').addEventListener('click', () => {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
            renderCalendar();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
            renderCalendar();
        });
        
        // Initial render
        renderCalendar();
        
        // Set selected date display
        const selectedDateElement = document.getElementById('selectedDate');
        if (selectedDateElement) {
            selectedDateElement.textContent = new Date().toLocaleDateString();
        }
    }

    /**
     * Render calendar for current month
     */
    function renderCalendar() {
        const currentMonth = document.getElementById('currentMonth');
        const calendarDays = document.getElementById('calendarDays');
        
        if (!currentMonth || !calendarDays) return;
        
        const year = currentCalendarDate.getFullYear();
        const month = currentCalendarDate.getMonth();
        
        // Set month and year header
        currentMonth.textContent = `${currentCalendarDate.toLocaleString('default', { month: 'long' })} ${year}`;
        calendarDays.innerHTML = '';
        
        // Add day labels
        ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
            const dayLabel = document.createElement('div');
            dayLabel.className = 'text-center text-gray-400 text-sm';
            dayLabel.textContent = day;
            calendarDays.appendChild(dayLabel);
        });
        
        // Add empty cells for days before start of month
        const firstDay = new Date(year, month, 1).getDay();
        for (let i = 0; i < firstDay; i++) {
            const emptyDay = document.createElement('div');
            calendarDays.appendChild(emptyDay);
        }
        
        // Add days of month
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            dayElement.textContent = day;
            
            // Highlight today
            if (new Date().toDateString() === new Date(year, month, day).toDateString()) {
                dayElement.style.border = '2px solid #ef4444';
            }
            
            dayElement.addEventListener('click', () => {
                // Remove previous selection
                document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
                dayElement.classList.add('selected');
                
                const selectedDate = new Date(year, month, day);
                document.getElementById('selectedDate').textContent = selectedDate.toLocaleDateString();
                
                // Call appropriate function based on current page
                if (window.location.pathname.endsWith('workout_of_the_day.html')) {
                    WorkoutModule.loadWorkout(selectedDate);
                } else if (window.location.pathname.endsWith('log_food.html')) {
                    NutritionModule.loadMeals(selectedDate);
                }
            });
            
            calendarDays.appendChild(dayElement);
        }
    }

    /**
     * Initialize page-specific calendar functionality
     */
    function initializePageCalendar() {
        const currentDate = new Date();
        const selectedDateElement = document.getElementById('selectedDate');
        if (selectedDateElement) {
            selectedDateElement.textContent = currentDate.toLocaleDateString();
        }

        const calendarDays = document.getElementById('calendarDays');
        if (!calendarDays) return;

        // Add click handlers to calendar days
        const dayElements = calendarDays.getElementsByClassName('calendar-day');
        Array.from(dayElements).forEach(day => {
            day.onclick = (e) => {
                document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('selected'));
                e.target.classList.add('selected');
                
                const date = currentCalendarDate;
                const selectedDate = new Date(
                    date.getFullYear(),
                    date.getMonth(),
                    Number(e.target.textContent)
                );
                selectedDateElement.textContent = selectedDate.toLocaleDateString();
                
                // Load appropriate data based on page
                if (window.location.pathname.endsWith('workout_of_the_day.html')) {
                    WorkoutModule.loadWorkout(selectedDate);
                } else if (window.location.pathname.endsWith('log_food.html')) {
                    NutritionModule.loadMeals(selectedDate);
                }
            };
        });
    }

    /**
     * Get the currently selected date
     * @returns {Date} - Current selected date
     */
    function getSelectedDate() {
        const selectedDateElement = document.getElementById('selectedDate');
        if (selectedDateElement) {
            return new Date(selectedDateElement.textContent);
        }
        return new Date();
    }

    // Public API
    return {
        initializeCalendar,
        initializePageCalendar,
        getSelectedDate
    };
})();