/**
 * readiness.js
 * User readiness tracking and visualization
 */

const ReadinessModule = (function() {
    /**
     * Show modal for daily check-in
     */
    function showCheckInModal() {
        console.log('Opening Daily Check-In modal');
        // Prevent multiple modals
        if (document.querySelector('.check-in-modal')) {
            console.warn('Check-In modal already open');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'check-in-modal fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full text-white">
                <h3 class="text-2xl font-bold mb-6">Daily Check-In</h3>
                <form id="checkInForm" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium mb-2">Weight (kg)</label>
                        <input type="number" id="weight" step="0.1" min="0" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Sleep Quality (1-10)</label>
                        <input type="number" id="sleep" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Stress Level (1-10)</label>
                        <input type="number" id="stress" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Energy Level (1-10)</label>
                        <input type="number" id="energy" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Muscle Soreness (1-10)</label>
                        <input type="number" id="soreness" min="1" max="10" class="w-full p-2 border rounded-lg bg-gray-700 text-white" required>
                    </div>
                    <div class="flex gap-4">
                        <button type="submit" class="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">Save</button>
                        <button type="button" onclick="this.closest('.check-in-modal').remove()" class="flex-1 bg-gray-700 text-white py-2 rounded-lg hover:bg-gray-600">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById('checkInForm').onsubmit = (e) => {
            e.preventDefault();
            console.log('Submitting Daily Check-In form');
            
            // Gather form data
            const data = {
                weight: Number(document.getElementById('weight').value),
                sleep: Number(document.getElementById('sleep').value),
                stress: Number(document.getElementById('stress').value),
                energy: Number(document.getElementById('energy').value),
                soreness: Number(document.getElementById('soreness').value),
                date: new Date().toLocaleDateString(),
                timestamp: new Date().getTime()
            };

            // Calculate readiness score
            const readiness = calculateReadiness(data);
            data.readiness = readiness;

            // Save check-in data
            console.log('Saving check-in data:', data);
            StorageModule.addToArray('checkIns', data);

            // Update readiness display
            updateReadinessDisplay(data);

            // Show success message
            showToast('Check-in saved successfully!');
            modal.remove();
        };
    }

    /**
     * Calculate readiness score based on check-in data
     * @param {Object} data - Check-in data
     * @returns {number} - Readiness score (0-100)
     */
    function calculateReadiness(data) {
        try {
            const stressScore = 11 - data.stress;
            
            const weights = {
                sleep: 0.35,
                stress: 0.25,
                energy: 0.25,
                soreness: 0.15
            };

            // Validate input data
            if (!validateReadinessData(data)) {
                throw new Error('Invalid readiness data');
            }

            const score = (
                (data.sleep * weights.sleep) +
                (stressScore * weights.stress) +
                (data.energy * weights.energy) +
                ((11 - data.soreness) * weights.soreness)
            ) * 10;

            return Math.min(100, Math.max(0, Math.round(score)));
        } catch (error) {
            console.error('Error calculating readiness:', error);
            return 0;
        }
    }

    function validateReadinessData(data) {
        return data.sleep >= 1 && data.sleep <= 10 &&
               data.stress >= 1 && data.stress <= 10 &&
               data.energy >= 1 && data.energy <= 10 &&
               data.soreness >= 1 && data.soreness <= 10;
    }

    /**
     * Update readiness display with check-in data
     * @param {Object} data - Check-in data
     */
    function updateReadinessDisplay(data) {
        const activityLog = document.getElementById('activityLog');
        if (!activityLog) return;

        // Get recommendation based on readiness score
        const recommendation = getRecommendation(data.readiness);
        const readinessColor = data.readiness >= 70 ? 'text-green-500' : 
                              data.readiness >= 50 ? 'text-yellow-500' : 
                              'text-red-500';

        activityLog.innerHTML = `
            <div class="p-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold">Today's Readiness Score</h3>
                    <span class="text-3xl font-bold ${readinessColor}">${data.readiness}%</span>
                </div>
                <div class="grid grid-cols-4 gap-4 mb-4">
                    <div class="text-center">
                        <div class="text-sm text-gray-400">Sleep</div>
                        <div class="text-lg font-bold">${data.sleep}/10</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-400">Stress</div>
                        <div class="text-lg font-bold">${data.stress}/10</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-400">Energy</div>
                        <div class="text-lg font-bold">${data.energy}/10</div>
                    </div>
                    <div class="text-center">
                        <div class="text-sm text-gray-400">Soreness</div>
                        <div class="text-lg font-bold">${data.soreness}/10</div>
                    </div>
                </div>
                <div class="bg-gray-700 p-4 rounded-lg">
                    <p class="text-sm">${recommendation}</p>
                </div>
            </div>
        `;
    }

    /**
     * Get recommendation based on readiness score
     * @param {number} readiness - Readiness score
     * @returns {string} - Recommendation text
     */
    function getRecommendation(readiness) {
        if (readiness >= 80) {
            return "You're in great shape! This is an excellent day for high-intensity training or pushing your limits.";
        } else if (readiness >= 60) {
            return "Good readiness levels. Proceed with your planned workout but monitor your body's response.";
        } else if (readiness >= 40) {
            return "Consider reducing workout intensity today. Focus on technique and mobility work.";
        } else {
            return "Your body needs recovery. Consider taking a rest day or doing light activity only.";
        }
    }

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type (success/error)
     */
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 z-50 ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        } text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Initialize readiness chart
     */
    function initializeReadinessChart() {
        const ctx = document.getElementById('readinessChart');
        if (!ctx) return;
        
        const chartCtx = ctx.getContext('2d');
        window.readinessChart = new Chart(chartCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Readiness Score',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#9CA3AF' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: { 
                            color: '#9CA3AF',
                            callback: value => `${value}%`
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: { color: '#9CA3AF' }
                    }
                }
            }
        });
        updateReadinessChart();
    }

    /**
     * Update readiness chart with latest data
     */
    function updateReadinessChart() {
        if (!window.readinessChart) return;

        const checkIns = StorageModule.getItem('checkIns', []);
        
        // Get last 7 days of data
        const last7Days = checkIns
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .slice(-7);

        // Update chart data
        window.readinessChart.data.labels = last7Days.map(day => {
            const date = new Date(day.date);
            return date.toLocaleDateString('en-US', { weekday: 'short' });
        });
        window.readinessChart.data.datasets[0].data = last7Days.map(day => day.readiness);
        
        // Add gradient background
        const ctx = document.getElementById('readinessChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.2)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0)');
        window.readinessChart.data.datasets[0].backgroundColor = gradient;
        
        window.readinessChart.update();
    }

    // Public API
    return {
        showCheckInModal,
        updateReadinessDisplay,
        initializeReadinessChart,
        updateReadinessChart
    };
})();