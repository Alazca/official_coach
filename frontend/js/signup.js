/**
 * COACH User Registration Module
 * Handles the registration process with clean separation of concerns
 */
const CoachSignup = (() => {
  // Private configuration
  const config = {
    apiEndpoint: "/api/register",
    formId: "signupForm",
    redirectPath: "/../index.html",
  };

  /**
   * Validates email format
   * @param {string} email - Email to validate
   * @returns {boolean} Whether email is valid
   */
  const isValidEmail = (email) => {
    const re =
      /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email.toLowerCase());
  };

  /**
   * Shows error message for a specific input
   * @param {HTMLElement} input - Input element with error
   * @param {string} message - Error message to display
   */
  const showError = (input, message) => {
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains("error-message")) {
      errorDiv.textContent = message;
      input.classList.add("border-red-500");
    }
  };

  /**
   * Clears error message for a specific input
   * @param {HTMLElement} input - Input element to clear error
   */
  const clearError = (input) => {
    const errorDiv = input.nextElementSibling;
    if (errorDiv && errorDiv.classList.contains("error-message")) {
      errorDiv.textContent = "";
      input.classList.remove("border-red-500");
    }
  };

  /**
   * Clears all error messages
   */
  const clearErrors = () => {
    document.querySelectorAll(".error-message").forEach((el) => {
      el.textContent = "";
    });
    document.querySelectorAll("input, select").forEach((el) => {
      el.classList.remove("border-red-500");
    });
  };

  /**
   * Validates a specific step in the multi-step form
   * @param {number} step - Step number to validate
   * @returns {boolean} Whether step is valid
   */
  const validateStep = (step) => {
    let isValid = true;
    const errorMessages = {
      name: "Please enter your full name",
      email: "Please enter a valid email address",
      password:
        "Password must be at least 8 characters with one number and one special character",
      dob: "Please enter your date of birth",
      gender: "Please select your gender",
      height: "Please enter a valid height",
      weight: "Please enter a valid weight",
      activityLevel: "Please select your activity level",
      goal: "Please select your fitness goal",
    };

    // Clear all error messages first
    document.querySelectorAll(".error-message").forEach((el) => {
      el.textContent = "";
    });

    switch (step) {
      case 1:
        // Validate name
        const name = document.getElementById("name");
        if (!name.value.trim()) {
          showError(name, errorMessages.name);
          isValid = false;
        }

        // Validate email
        const email = document.getElementById("email");
        if (!isValidEmail(email.value)) {
          showError(email, errorMessages.email);
          isValid = false;
        }

        // Validate password
        const password = document.getElementById("password");
        if (!validatePassword(password.value)) {
          showError(password, errorMessages.password);
          isValid = false;
        }

        // Validate confirm password
        const confirmPassword = document.getElementById("confirmPassword");
        if (password.value !== confirmPassword.value) {
          showError(confirmPassword, "Passwords do not match");
          isValid = false;
        }
        break;

      case 2:
        // Validate date of birth
        const dob = document.getElementById("dob");
        if (!dob.value) {
          showError(dob, errorMessages.dob);
          isValid = false;
        }

        // Validate gender
        const gender = document.getElementById("gender");
        if (!gender.value) {
          showError(gender, errorMessages.gender);
          isValid = false;
        }

        // Validate height
        const height = document.getElementById("height");
        if (!height.value || parseFloat(height.value) <= 0) {
          showError(height, errorMessages.height);
          isValid = false;
        }

        // Validate weight
        const weight = document.getElementById("weight");
        if (!weight.value || parseFloat(weight.value) <= 0) {
          showError(weight, errorMessages.weight);
          isValid = false;
        }
        break;

      case 3:
        // Validate activity level
        const activityLevel = document.getElementById("activityLevel");
        if (!activityLevel.value) {
          showError(activityLevel, errorMessages.activityLevel);
          isValid = false;
        }

        // Validate goal
        const goal = document.getElementById("goal");
        if (!goal.value) {
          showError(goal, errorMessages.goal);
          isValid = false;
        }

        // Validate terms checkbox
        const terms = document.getElementById("terms");
        if (!terms.checked) {
          showError(terms, "You must agree to the terms and conditions");
          isValid = false;
        }
        break;
    }

    return isValid;
  };

  /**
   * Collects all form data from the signup form
   * @returns {Object} Form data object
   */
  const collectFormData = () => {
    // Collect basic form data
    const formData = {
      name: document.getElementById("name")?.value.trim() || "",
      email: document.getElementById("email")?.value.trim() || "",
      password: document.getElementById("password")?.value || "",
      dob: document.getElementById("dob")?.value || "",
      gender: document.getElementById("gender")?.value || "Other",
      height: parseFloat(document.getElementById("height")?.value) || 0,
      weight: parseFloat(document.getElementById("weight")?.value) || 0,
      initialActivityLevel:
        document.getElementById("activityLevel")?.value || "Sedentary",
      goal: document.getElementById("goal")?.value || "Default",
    };

    // Convert empty strings to null for required fields
    Object.keys(formData).forEach((key) => {
      if (formData[key] === "") {
        formData[key] = null;
      }
    });

    // Ensure goal is one of the valid GoalType values
    const validGoals = [
      "Strength",
      "Endurance",
      "Weight-Loss",
      "Performance",
      "Default",
    ];
    if (!validGoals.includes(formData.goal)) {
      formData.goal = "Default";
    }

    // Ensure activity level is one of the valid ActivityLevel values
    const validActivityLevels = [
      "Sedentary",
      "Casual",
      "Moderate",
      "Active",
      "Intense",
    ];
    if (!validActivityLevels.includes(formData.initialActivityLevel)) {
      formData.initialActivityLevel = "Sedentary";
    }

    // Ensure gender is one of the valid Gender values
    const validGenders = ["Male", "Female", "Other"];
    if (!validGenders.includes(formData.gender)) {
      formData.gender = "Other";
    }

    // Convert height and weight to numbers
    formData.height = Number(formData.height);
    formData.weight = Number(formData.weight);

    // Ensure height and weight are positive numbers
    if (formData.height <= 0) formData.height = null;
    if (formData.weight <= 0) formData.weight = null;

    return formData;
  };

  /**
   * Shows success message and handles redirection
   */
  const showSuccessMessage = () => {
    const modal = document.getElementById("success-modal");
    if (modal) {
      modal.classList.remove("hidden");
      setTimeout(() => {
        modal.classList.add("hidden");
      }, 3000);
    }
  };

  /**
   * Initializes the multi-step form navigation
   */
  const initializeMultiStepForm = () => {
    const steps = [
      document.getElementById("step-1"),
      document.getElementById("step-2"),
      document.getElementById("step-3"),
    ];
    const progressBar = document.getElementById("progress-bar");
    const stepIndicator = document.getElementById("step-indicator");
    const progressPercentage = document.getElementById("progress-percentage");

    let currentStep = 0;

    // Go to specific step function
    const goToStep = (stepIndex) => {
      steps[currentStep].classList.remove("active");
      currentStep = stepIndex;
      steps[currentStep].classList.add("active");

      // Update progress bar
      const progress = (currentStep / (steps.length - 1)) * 100;
      progressBar.style.width = `${progress}%`;
      stepIndicator.textContent = `Step ${currentStep + 1} of ${steps.length}`;
      progressPercentage.textContent = `${Math.round(progress)}%`;
    };

    // Next buttons
    document.getElementById("next-1")?.addEventListener("click", function () {
      if (validateStep(1)) goToStep(1);
    });

    document.getElementById("next-2")?.addEventListener("click", function () {
      if (validateStep(2)) goToStep(2);
    });

    // Previous buttons
    document.getElementById("prev-2")?.addEventListener("click", function () {
      goToStep(0);
    });

    document.getElementById("prev-3")?.addEventListener("click", function () {
      goToStep(1);
    });

    // Initialize fitness goal option highlighting
    document.querySelectorAll(".fitness-goal-option").forEach((option) => {
      const checkbox = option.querySelector('input[type="checkbox"]');
      if (checkbox) {
        checkbox.addEventListener("change", function () {
          if (this.checked) {
            option.classList.add("border-red-500");
            option.classList.remove("border-gray-600");
          } else {
            option.classList.remove("border-red-500");
            option.classList.add("border-gray-600");
          }
        });
      }
    });
  };

  /**
   * Initializes the signup form handlers
   */
  const initialize = () => {
    document.addEventListener("DOMContentLoaded", () => {
      const form = document.getElementById(config.formId);

      if (form) {
        // Initialize multi-step form
        initializeMultiStepForm();

        // Handle form submission
        form.addEventListener("submit", handleSubmit);
      } else {
        console.error(`Signup form with ID "${config.formId}" not found`);
      }
    });
  };

  const validateEmail = (email) => {
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password) => {
    // Password must be at least 8 characters
    if (password.length < 8) {
      return false;
    }

    // Must contain at least one letter
    if (!/[a-zA-Z]/.test(password)) {
      return false;
    }

    // Must contain at least one number
    if (!/\d/.test(password)) {
      return false;
    }

    // Must contain at least one special character
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate the final step
    if (!validateStep(3)) {
      return;
    }

    // Collect form data
    const formData = collectFormData();

    // Validate required fields
    const requiredFields = [
      "name",
      "email",
      "password",
      "dob",
      "gender",
      "height",
      "weight",
      "initialActivityLevel",
      "goal",
    ];
    const missingFields = requiredFields.filter((field) => !formData[field]);

    if (missingFields.length > 0) {
      showNotification(
        `Please fill in all required fields: ${missingFields.join(", ")}`,
        "error",
      );
      return;
    }

    // Send registration request
    try {
      if (typeof window.CoachUtils === "undefined") {
        throw new Error(
          "CoachUtils is not loaded. Please refresh the page and try again.",
        );
      }

      await window.CoachUtils.sendPostAndRedirect(
        "/api/register",
        formData,
        "/dashboard",
        (result) => {
          console.log("Registration successful:", result);
          showSuccessMessage();
        },
        (error) => {
          console.error("Registration failed:", error);
          showNotification(
            error.message || "Registration failed. Please try again.",
            "error",
          );
        },
      );
    } catch (error) {
      console.error("Registration error:", error);
      showNotification(
        "An error occurred during registration. Please try again.",
        "error",
      );
    }
  };

  const showNotification = (message, type = "info") => {
    if (typeof window.CoachUtils !== "undefined") {
      window.CoachUtils.showNotification(message, type);
    } else {
      // Fallback notification if CoachUtils is not available
      alert(message);
    }
  };

  // Public API
  return {
    initialize,
    validateStep,
    collectFormData,
    showSuccessMessage,
  };
})();

// Initialize the signup module
CoachSignup.initialize();
