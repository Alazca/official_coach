/**
 * COACH User Registration Module
 * Handles the registration process with clean separation of concerns
 */
const CoachSignup = (() => {
  // Private configuration
  const config = {
    apiEndpoint: "/api/register",
    formId: "signupForm",
    redirectPath: "/dashboard",
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
    input.classList.add("border-red-500");
    const errorElement = input.nextElementSibling;
    if (errorElement && errorElement.classList.contains("error-message")) {
      errorElement.textContent = message;
      errorElement.classList.add("text-red-500", "text-sm", "mt-1");
    }

    // Add shake animation
    input.classList.add("form-error");
    setTimeout(() => input.classList.remove("form-error"), 500);
  };

  /**
   * Clears all error messages
   */
  const clearErrors = () => {
    document.querySelectorAll(".error-message").forEach((el) => {
      el.textContent = "";
      el.classList.remove("text-red-500");
    });

    document.querySelectorAll("input, select").forEach((input) => {
      input.classList.remove("border-red-500");
    });
  };

  /**
   * Validates a specific step in the multi-step form
   * @param {number} step - Step number to validate
   * @returns {boolean} Whether step is valid
   */
  const validateStep = (step) => {
    let isValid = true;

    // Clear previous errors
    clearErrors();

    if (step === 1) {
      // Step 1: Account Details
      const name = document.getElementById("name");
      const email = document.getElementById("email");
      const password = document.getElementById("password");
      const confirmPassword = document.getElementById("confirmPassword");

      // Name validation
      if (
        name.value.trim() === "" ||
        name.value.split(" ").filter((word) => word.length > 0).length < 2
      ) {
        showError(name, "Please enter your full name (first and last name)");
        isValid = false;
      }

      // Email validation
      if (!isValidEmail(email.value)) {
        showError(email, "Please enter a valid email address");
        isValid = false;
      }

      // Password validation
      if (password.value.length < 8) {
        showError(password, "Password must be at least 8 characters long");
        isValid = false;
      } else if (!/\d/.test(password.value)) {
        showError(password, "Password must contain at least one number");
        isValid = false;
      } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(password.value)) {
        showError(
          password,
          "Password must contain at least one special character",
        );
        isValid = false;
      }

      // Confirm password
      if (password.value !== confirmPassword.value) {
        showError(confirmPassword, "Passwords do not match");
        isValid = false;
      }
    } else if (step === 2) {
      // Step 2: Personal Details
      const dob = document.getElementById("dob");
      const gender = document.getElementById("gender");
      const height = document.getElementById("height");
      const weight = document.getElementById("weight");

      if (!dob.value) {
        showError(dob, "Please enter your date of birth");
        isValid = false;
      }

      if (!gender.value) {
        showError(gender, "Please select your gender");
        isValid = false;
      }

      if (!height.value || isNaN(height.value) || height.value <= 0) {
        showError(height, "Please enter a valid height");
        isValid = false;
      }

      if (!weight.value || isNaN(weight.value) || weight.value <= 0) {
        showError(weight, "Please enter a valid weight");
        isValid = false;
      }
    } else if (step === 3) {
      // Step 3: Fitness Profile
      const activityLevel = document.getElementById("activityLevel");
      const terms = document.getElementById("terms");

      if (!activityLevel.value) {
        showError(activityLevel, "Please select your activity level");
        isValid = false;
      }

      if (!terms.checked) {
        showError(
          terms,
          "You must agree to the Terms of Service and Privacy Policy",
        );
        isValid = false;
      }
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
      gender: document.getElementById("gender")?.value || "",
      height: parseFloat(document.getElementById("height")?.value) || 0,
      weight: parseFloat(document.getElementById("weight")?.value) || 0,
      initialActivityLevel:
        document.getElementById("activityLevel")?.value || "", // Changed to match backend model
      fitnessGoals: [],
    };

    // Collect fitness goals (multiple checkboxes)
    document
      .querySelectorAll('input[name="fitnessGoals"]:checked')
      .forEach((checkbox) => {
        formData.fitnessGoals.push(checkbox.value);
      });

    return formData;
  };

  /**
   * Shows success message and handles redirection
   */
  const showSuccessMessage = () => {
    // Show the success modal
    const successModal = document.getElementById("success-modal");
    if (successModal) {
      successModal.classList.remove("hidden");

      // Start the progress bar and countdown
      const redirectProgress = document.getElementById("redirect-progress");
      const redirectCountdown = document.getElementById("redirect-countdown");
      let count = 3;

      const countdownInterval = setInterval(() => {
        count--;
        redirectCountdown.textContent = count;
        redirectProgress.style.width = `${((3 - count) / 3) * 100}%`;

        if (count <= 0) {
          clearInterval(countdownInterval);
          window.location.href = config.redirectPath;
        }
      }, 1000);
    } else {
      // Fallback if modal not found
      alert("Account created successfully! Redirecting to dashboard...");
      setTimeout(() => {
        window.location.href = config.redirectPath;
      }, 1500);
    }
  };

  /**
   * Handles the API submission when the form is complete
   */
  const submitFormData = async (formData) => {
    try {
      const response = await fetch(config.apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        showSuccessMessage();
        return true;
      } else {
        alert(data.error || "Registration failed. Please try again.");
        return false;
      }
    } catch (error) {
      console.error("Registration error:", error);
      alert("An error occurred during registration. Please try again.");
      return false;
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

    if (!steps[0] || !steps[1] || !steps[2]) {
      console.error("One or more form steps not found");
      return;
    }

    const progressBar = document.getElementById("progress-bar");
    const stepIndicator = document.getElementById("step-indicator");
    const progressPercentage = document.getElementById("progress-percentage");

    // Fixed: Changing to 1-based indexing to match validateStep function
    let currentStep = 1;

    // Go to specific step function
    const goToStep = (stepNumber) => {
      // Hide all steps
      steps.forEach((step) => step.classList.remove("active"));

      // Show the current step (adjust for zero-based array)
      steps[stepNumber - 1].classList.add("active");

      // Update current step tracking
      currentStep = stepNumber;

      // Update progress bar
      const progress = ((currentStep - 1) / 2) * 100;
      progressBar.style.width = `${progress}%`;
      stepIndicator.textContent = `Step ${currentStep} of 3`;
      progressPercentage.textContent = `${Math.round(progress)}%`;
    };

    // Next buttons
    document.getElementById("next-1")?.addEventListener("click", function () {
      //if (validateStep(1)) goToStep(2);
      goToStep(2);
    });

    document.getElementById("next-2")?.addEventListener("click", function () {
      if (validateStep(2)) goToStep(3);
    });

    // Previous buttons
    document.getElementById("prev-2")?.addEventListener("click", function () {
      goToStep(1);
    });

    document.getElementById("prev-3")?.addEventListener("click", function () {
      goToStep(2);
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
        form.addEventListener("submit", async (e) => {
          e.preventDefault();

          if (validateStep(3)) {
            // Get submit button
            const submitBtn = document.getElementById("submit-form");
            if (submitBtn) submitBtn.disabled = true;

            // Collect all form data
            const formData = collectFormData();

            // Use our own submit function (don't rely on CoachUtils)
            await submitFormData(formData);

            // Re-enable button regardless of result
            if (submitBtn) submitBtn.disabled = false;
          }
        });
      } else {
        console.error(`Signup form with ID "${config.formId}" not found`);
      }
    });
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
