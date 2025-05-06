/**
 * COACH User Registration Module - Simplified robust version
 */
const CoachSignup = (() => {
  // Configuration
  const config = {
    apiEndpoint: "/api/register",
    formId: "signupForm",
    redirectPath: "/dashboard",
    debug: true,
  };

  // Debug logger
  const log = (message, ...data) => {
    if (config.debug) {
      console.log(`[Signup] ${message}`, ...(data || []));
    }
  };

  // Email validation
  const isValidEmail = (email) => {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.toLowerCase());
  };

  // Display error message
  const showError = (input, message) => {
    if (!input) return;

    input.classList.add("border-red-500");

    const errorElement = input.nextElementSibling;
    if (errorElement && errorElement.classList.contains("error-message")) {
      errorElement.textContent = message;
      errorElement.classList.add("text-red-500", "text-sm", "mt-1");
    }

    input.classList.add("form-error");
    setTimeout(() => input.classList.remove("form-error"), 500);
  };

  // Clear errors
  const clearErrors = () => {
    document.querySelectorAll(".error-message").forEach((el) => {
      el.textContent = "";
      el.classList.remove("text-red-500");
    });

    document.querySelectorAll("input, select").forEach((input) => {
      input.classList.remove("border-red-500");
      input.classList.remove("form-error");
    });
  };

  // Form validation
  const validateStep = (step) => {
    let isValid = true;
    clearErrors();

    try {
      if (step === 1) {
        // Account Details validation
        const name = document.getElementById("name");
        const email = document.getElementById("email");
        const password = document.getElementById("password");
        const confirmPassword = document.getElementById("confirmPassword");

        if (!name || !name.value.trim()) {
          showError(name, "Please enter your name");
          isValid = false;
        }

        if (!email || !email.value.trim()) {
          showError(email, "Please enter your email address");
          isValid = false;
        } else if (!isValidEmail(email.value)) {
          showError(email, "Please enter a valid email address");
          isValid = false;
        }

        if (!password || !password.value) {
          showError(password, "Please enter a password");
          isValid = false;
        } else if (password.value.length < 8) {
          showError(password, "Password must be at least 8 characters long");
          isValid = false;
        }

        if (!confirmPassword || password.value !== confirmPassword.value) {
          showError(confirmPassword, "Passwords do not match");
          isValid = false;
        }
      } else if (step === 2) {
        // Personal Details validation
        const dob = document.getElementById("dob");
        const gender = document.getElementById("gender");
        const height = document.getElementById("height");
        const weight = document.getElementById("weight");

        if (!dob || !dob.value) {
          showError(dob, "Please enter your date of birth");
          isValid = false;
        }

        if (!gender || !gender.value) {
          showError(gender, "Please select your gender");
          isValid = false;
        }

        if (!height || !height.value) {
          showError(height, "Please enter a valid height");
          isValid = false;
        }

        if (!weight || !weight.value) {
          showError(weight, "Please enter a valid weight");
          isValid = false;
        }
      } else if (step === 3) {
        // Fitness Profile validation
        const activityLevel = document.getElementById("activityLevel");
        const terms = document.getElementById("terms");

        if (!activityLevel || !activityLevel.value) {
          showError(activityLevel, "Please select your activity level");
          isValid = false;
        }

        if (!terms || !terms.checked) {
          showError(
            terms,
            "You must agree to the Terms of Service and Privacy Policy",
          );
          isValid = false;
        }
      }
    } catch (error) {
      log("Validation error:", error);
      isValid = false;
    }

    return isValid;
  };

  // Collect form data
  const collectFormData = () => {
    const formData = {
      name: document.getElementById("name")?.value.trim() || "",
      email: document.getElementById("email")?.value.trim() || "",
      password: document.getElementById("password")?.value || "",
      dob: document.getElementById("dob")?.value || "",
      gender: document.getElementById("gender")?.value || "",
      height: parseFloat(document.getElementById("height")?.value) || 0,
      weight: parseFloat(document.getElementById("weight")?.value) || 0,
      initialActivityLevel:
        document.getElementById("activityLevel")?.value || "",
      fitnessGoals: [],
    };

    document
      .querySelectorAll('input[name="fitnessGoals"]:checked')
      .forEach((checkbox) => {
        formData.fitnessGoals.push(checkbox.value);
      });

    return formData;
  };

  // Success message and redirect
  const showSuccessMessage = () => {
    const successModal = document.getElementById("success-modal");
    if (successModal) {
      successModal.classList.remove("hidden");

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
      alert("Account created successfully! Redirecting to dashboard...");
      setTimeout(() => {
        window.location.href = config.redirectPath;
      }, 1500);
    }
  };

  // API submission
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
      log("API submission error:", error);
      alert("An error occurred during registration. Please try again.");
      return false;
    }
  };

  // Main initialization function
  const initialize = () => {
    // Execute when DOM is fully loaded
    window.addEventListener("DOMContentLoaded", () => {
      const form = document.getElementById(config.formId);
      if (!form) {
        log(`Form with ID "${config.formId}" not found`);
        return;
      }

      // Get step elements
      const steps = [
        document.getElementById("step-1"),
        document.getElementById("step-2"),
        document.getElementById("step-3"),
      ];

      if (!steps[0] || !steps[1] || !steps[2]) {
        log("One or more form steps not found");
        return;
      }

      const progressBar = document.getElementById("progress-bar");
      const stepIndicator = document.getElementById("step-indicator");
      const progressPercentage = document.getElementById("progress-percentage");

      // Function to navigate between steps
      const goToStep = (stepNumber) => {
        // Hide all steps
        steps.forEach((step) => step.classList.remove("active"));

        // Show the current step
        steps[stepNumber - 1].classList.add("active");

        // Update progress indicators
        const progress = ((stepNumber - 1) / 2) * 100;
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (stepIndicator)
          stepIndicator.textContent = `Step ${currentStep} of 3`;
        if (progressPercentage)
          progressPercentage.textContent = `${Math.round(progress)}%`;
      };

      // Current step tracker
      let currentStep = 1;

      // Set up navigation buttons
      const next1 = document.getElementById("next-1");
      if (next1) {
        next1.addEventListener("click", () => {
          if (validateStep(1)) goToStep(2);
        });
      }

      const next2 = document.getElementById("next-2");
      if (next2) {
        next2.addEventListener("click", () => {
          if (validateStep(2)) goToStep(3);
        });
      }

      const prev2 = document.getElementById("prev-2");
      if (prev2) {
        prev2.addEventListener("click", () => {
          goToStep(1);
        });
      }

      const prev3 = document.getElementById("prev-3");
      if (prev3) {
        prev3.addEventListener("click", () => {
          goToStep(2);
        });
      }

      // Form submission handler
      form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (validateStep(3)) {
          const submitBtn = document.getElementById("submit-form");
          if (submitBtn) submitBtn.disabled = true;

          const formData = collectFormData();
          await submitFormData(formData);

          if (submitBtn) submitBtn.disabled = false;
        }
      });

      // Set up fitness goal styling
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
    });

    // Fallback initialization
    window.addEventListener("load", function () {
      // Direct click handler for Continue button
      const next1Button = document.getElementById("next-1");
      if (next1Button) {
        // Add a direct click handler as fallback
        next1Button.onclick = function () {
          const step1 = document.getElementById("step-1");
          const step2 = document.getElementById("step-2");

          if (step1 && step2) {
            step1.classList.remove("active");
            step2.classList.add("active");

            const progressBar = document.getElementById("progress-bar");
            const stepIndicator = document.getElementById("step-indicator");
            const progressPercentage = document.getElementById(
              "progress-percentage",
            );

            if (progressBar) progressBar.style.width = "66%";
            if (stepIndicator) stepIndicator.textContent = "Step 2 of 3";
            if (progressPercentage) progressPercentage.textContent = "66%";
          }
        };
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

// Initialize the module
CoachSignup.initialize();
