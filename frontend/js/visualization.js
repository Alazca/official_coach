/**
 * COACH Data Visualization Module
 * Handles all data visualization and charting functionality
 */
const DataVisualizationModule = (() => {
  // Private variables
  let charts = {};

  /**
   * Initialize the data visualization dashboard
   */
  const initialize = () => {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("Data Visualization Module initializing...");

      // Initialize all charts
      initializeCharts();

      // Set up event listeners
      setupEventListeners();

      // Load initial data
      loadData();
    });
  };

  /**
   * Initialize all chart objects
   */
  const initializeCharts = () => {
    // Set up volume chart
    const volumeCtx = document.getElementById("volumeChart")?.getContext("2d");
    if (volumeCtx) {
      charts.volume = new Chart(volumeCtx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Volume (kg)",
              data: [],
              borderColor: "#ef4444",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              tension: 0.3,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: "#2c2d25",
              },
            },
          },
          scales: {
            x: {
              grid: {
                color: "rgba(30, 30, 30, 0.57)",
              },
              ticks: {
                color: "#717780",
              },
            },
            y: {
              grid: {
                color: "rgba(30, 30, 30, 0.57)",
              },
              ticks: {
                color: "#717780",
              },
            },
          },
        },
      });
    }

    // Set up nutrition chart
    const nutritionCtx = document
      .getElementById("nutritionChart")
      ?.getContext("2d");
    if (nutritionCtx) {
      charts.nutrition = new Chart(nutritionCtx, {
        type: "bar",
        data: {
          labels: [],
          datasets: [
            {
              label: "Calories",
              data: [],
              backgroundColor: "#ef4444",
              borderColor: "#dc2626",
              borderWidth: 1,
            },
            {
              label: "Protein (g)",
              data: [],
              backgroundColor: "#3b82f6",
              borderColor: "#2563eb",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                color: "#2c2d25",
              },
            },
          },
          scales: {
            x: {
              grid: {
                color: "rgba(30, 30, 30, 0.57)",
              },
              ticks: {
                color: "#717780",
              },
            },
            y: {
              grid: {
                color: "rgba(30, 30, 30, 0.57)",
              },
              ticks: {
                color: "#717780",
              },
            },
          },
        },
      });
    }

    // Initialize other charts similarly
    // ... weight chart, exercise chart, etc.
  };

  /**
   * Set up all event listeners
   */
  const setupEventListeners = () => {
    // Update charts button
    const updateBtn = document.getElementById("updateCharts");
    if (updateBtn) {
      updateBtn.addEventListener("click", refreshCharts);
    }

    // Home button
    const homeBtn = document.getElementById("homeButton");
    if (homeBtn) {
      homeBtn.addEventListener("click", () => {
        window.location.href = "../../index.html";
      });
    }

    // Time range selector
    const timeRangeSelect = document.getElementById("timeRange");
    if (timeRangeSelect) {
      timeRangeSelect.addEventListener("change", refreshCharts);
    }
  };

  /**
   * Load data from API or local storage
   */
  const loadData = () => {
    // Placeholder for API data loading
    // In a real implementation, this would fetch data from an API
    // For now, we'll use mock data

    refreshCharts();
  };

  /**
   * Refresh all charts with new data
   */
  const refreshCharts = () => {
    const timeRange = document.getElementById("timeRange")?.value || "7";
    console.log(`Refreshing charts for time range: ${timeRange} days`);

    // Generate mock data based on the selected time range
    const mockData = generateMockData(parseInt(timeRange));

    // Update charts with the new data
    updateCharts(mockData);

    // Update summary statistics
    updateSummaryStats(mockData);
  };

  /**
   * Generate mock data for testing
   */
  const generateMockData = (days) => {
    const data = {
      dates: [],
      volume: [],
      calories: [],
      protein: [],
      weight: [],
      distance: [],
      pace: [],
      heartRate: [],
    };

    const today = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);

      data.dates.push(
        date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      );
      data.volume.push(Math.floor(Math.random() * 1000) + 5000);
      data.calories.push(Math.floor(Math.random() * 500) + 1800);
      data.protein.push(Math.floor(Math.random() * 50) + 120);
      data.weight.push(80 - Math.random() * 2);
      data.distance.push(Math.floor(Math.random() * 5) + 2);
      data.pace.push(Math.floor(Math.random() * 60) + 300);
      data.heartRate.push(Math.floor(Math.random() * 30) + 140);
    }

    return data;
  };

  /**
   * Update all charts with new data
   */
  const updateCharts = (data) => {
    // Update volume chart
    if (charts.volume) {
      charts.volume.data.labels = data.dates;
      charts.volume.data.datasets[0].data = data.volume;
      charts.volume.update();
    }

    // Update nutrition chart
    if (charts.nutrition) {
      charts.nutrition.data.labels = data.dates;
      charts.nutrition.data.datasets[0].data = data.calories;
      charts.nutrition.data.datasets[1].data = data.protein;
      charts.nutrition.update();
    }

    // Update other charts similarly
    // ... weight chart, exercise chart, etc.
  };

  /**
   * Update summary statistics
   */
  const updateSummaryStats = (data) => {
    // Calculate totals and averages
    const totalVolume = data.volume.reduce((sum, val) => sum + val, 0);
    const avgCalories = Math.round(
      data.calories.reduce((sum, val) => sum + val, 0) / data.calories.length,
    );
    const weightChange = data.weight[data.weight.length - 1] - data.weight[0];

    // Update UI elements
    document.getElementById("totalVolume").textContent =
      `${totalVolume.toLocaleString()} kg`;
    document.getElementById("avgCalories").textContent =
      avgCalories.toLocaleString();
    document.getElementById("weightChange").textContent =
      `${weightChange.toFixed(1)} kg`;
    document.getElementById("workoutCount").textContent = data.dates.length;

    // Update running stats
    const totalDistance = data.distance.reduce((sum, val) => sum + val, 0);
    const avgPace = Math.round(
      data.pace.reduce((sum, val) => sum + val, 0) / data.pace.length,
    );
    const avgHeartRate = Math.round(
      data.heartRate.reduce((sum, val) => sum + val, 0) / data.heartRate.length,
    );

    document.getElementById("totalDistance").textContent =
      `${totalDistance.toFixed(1)} km`;
    document.getElementById("avgPace").textContent = formatPace(avgPace);
    document.getElementById("totalTime").textContent =
      `${((totalDistance * avgPace) / 60).toFixed(1)} hrs`;
    document.getElementById("avgHeartRate").textContent = `${avgHeartRate} bpm`;
  };

  /**
   * Format pace value (seconds) to MM:SS format
   */
  const formatPace = (paceInSeconds) => {
    const minutes = Math.floor(paceInSeconds / 60);
    const seconds = paceInSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")} /km`;
  };

  // Public API
  return {
    initialize,
    refreshCharts,
  };
})();

// Initialize the module when loaded
DataVisualizationModule.initialize();

