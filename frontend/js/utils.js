/**
 * utils.js
 * Utility functions for COACH application
 *
 * This file contains reusable utility functions that can be used across the application.
 */

// COACH Utilities Module
const CoachUtils = (() => {
  /**
   * Sends a POST request to the database and redirects to another page
   * @param {string} endpoint - API endpoint to send data to
   * @param {Object} data - Data to send in the request body
   * @param {string} redirectUrl - URL to redirect to after successful request
   * @param {Function} onSuccess - Optional callback function to run on success
   * @param {Function} onError - Optional callback function to run on error
   */
  const sendPostAndRedirect = async (
    endpoint,
    data,
    redirectUrl,
    onSuccess = null,
    onError = null,
  ) => {
    try {
      // Show loading indicator
      const loadingIndicator = document.createElement("div");
      loadingIndicator.className =
        "fixed top-0 left-0 w-full h-1 bg-red-600 animate-pulse z-50";
      document.body.appendChild(loadingIndicator);

      // Send the POST request
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      // Process the response
      if (response.ok) {
        const result = await response.json();
        console.log("Request successful:", result);

        // Call success callback if provided
        if (onSuccess && typeof onSuccess === "function") {
          onSuccess(result);
        }

        // Show success message
        showNotification("Success! Redirecting...", "success");

        // Redirect to the specified URL after a short delay
        setTimeout(() => {
          window.location.href = redirectUrl;
        }, 1000);
      } else {
        const error = await response.json();
        console.error("Request failed:", error);

        // Call error callback if provided
        if (onError && typeof onError === "function") {
          onError(error);
        }

        // Show error message
        showNotification(
          error.message || "An error occurred. Please try again.",
          "error",
        );

        // Remove loading indicator
        document.body.removeChild(loadingIndicator);
      }
    } catch (error) {
      console.error("Network error:", error);

      // Call error callback if provided
      if (onError && typeof onError === "function") {
        onError(error);
      }

      // Show error message
      showNotification(
        "Network error. Please check your connection and try again.",
        "error",
      );

      // Remove loading indicator if it exists
      const indicator = document.querySelector(
        ".fixed.top-0.left-0.w-full.h-1",
      );
      if (indicator) {
        document.body.removeChild(indicator);
      }
    }
  };

  /**
   * Shows a notification message
   * @param {string} message - Message to display
   * @param {string} type - Type of notification (success, error, warning, info)
   * @param {number} duration - Duration in milliseconds to show the notification
   */
  const showNotification = (message, type = "info", duration = 3000) => {
    // Create notification element
    const notification = document.createElement("div");

    // Set classes based on notification type
    let bgColor, textColor;
    switch (type) {
      case "success":
        bgColor = "bg-green-600";
        textColor = "text-white";
        break;
      case "error":
        bgColor = "bg-red-600";
        textColor = "text-white";
        break;
      case "warning":
        bgColor = "bg-yellow-500";
        textColor = "text-gray-900";
        break;
      default:
        bgColor = "bg-blue-600";
        textColor = "text-white";
    }

    // Set notification styles
    notification.className = `fixed top-4 right-4 ${bgColor} ${textColor} px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in`;
    notification.textContent = message;

    // Add animation styles
    const style = document.createElement("style");
    style.textContent = `
            @keyframes fade-in {
                from { opacity: 0; transform: translateY(-20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes fade-out {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(-20px); }
            }
            .animate-fade-in {
                animation: fade-in 0.3s ease forwards;
            }
            .animate-fade-out {
                animation: fade-out 0.3s ease forwards;
            }
        `;
    document.head.appendChild(style);

    // Add notification to the DOM
    document.body.appendChild(notification);

    // Remove notification after duration
    setTimeout(() => {
      notification.classList.remove("animate-fade-in");
      notification.classList.add("animate-fade-out");

      setTimeout(() => {
        if (notification.parentNode) {
          document.body.removeChild(notification);
        }
      }, 300);
    }, duration);
  };

  /**
   * Adds click event to a button that sends POST request and redirects
   * @param {string} buttonId - ID of the button to attach the event to
   * @param {string} endpoint - API endpoint to send data to
   * @param {Object|Function} data - Data to send or function that returns data
   * @param {string} redirectUrl - URL to redirect to after successful request
   */
  const setupButtonWithPostAndRedirect = (
    buttonId,
    endpoint,
    data,
    redirectUrl,
  ) => {
    const button = document.getElementById(buttonId);

    if (!button) {
      console.error(`Button with ID "${buttonId}" not found`);
      return;
    }

    button.addEventListener("click", async (e) => {
      e.preventDefault();

      // Disable button to prevent multiple clicks
      button.disabled = true;
      const originalText = button.textContent;
      button.textContent = "Processing...";

      // Get data (either static object or from function)
      const postData = typeof data === "function" ? data() : data;

      // Send POST request and redirect
      await sendPostAndRedirect(
        endpoint,
        postData,
        redirectUrl,
        null, // Success callback
        () => {
          // Error callback - re-enable button
          button.disabled = false;
          button.textContent = originalText;
        },
      );
    });
  };

  // Return public methods
  return {
    sendPostAndRedirect,
    showNotification,
    setupButtonWithPostAndRedirect,
  };
})();

// Add to window for global access
window.CoachUtils = CoachUtils;

