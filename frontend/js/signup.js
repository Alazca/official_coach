/**
 * COACH User Registration Module
 * Handles the registration process with clean separation of concerns
 */
const CoachSignup = (() => {
    // Private configuration
    const config = {
      apiEndpoint: '/api/register',
      formId: 'signupForm',
      redirectPath: '../../index.html'
    };
  
    /**
     * Validates email format
     * @param {string} email - Email to validate
     * @returns {boolean} Whether email is valid
     */
    const isValidEmail = (email) => {
      const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      return re.test(email.toLowerCase());
    };
  
    /**
     * Shows error message for a specific input
     * @param {string} inputId - ID of the input with error
     * @param {string} message - Error message to display
     */
    const showError = (inputId, message) => {
      const input = document.getElementById(inputId);
      const errorDiv = document.createElement('div');
      errorDiv.className = 'text-red-500 text-sm mt-1';
      errorDiv.textContent = message;
  
      // Add error class to input
      input.classList.add('border-red-500');
  
      // Add error message after input
      input.parentNode.appendChild(errorDiv);
  
      // Shake animation
      input.classList.add('animate-shake');
      setTimeout(() => input.classList.remove('animate-shake'), 500);
    };
  
    /**
     * Clears all error messages
     */
    const clearErrors = () => {
      document.querySelectorAll('.text-red-500.text-sm').forEach(el => el.remove());
      document.querySelectorAll('input, select').forEach(input => {
        input.classList.remove('border-red-500');
      });
    };
  
    /**
     * Shows success message
     * @param {string} message - Success message to display
     */
    const showSuccessMessage = (message) => {
      const successDiv = document.createElement('div');
      successDiv.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      successDiv.textContent = message;
      document.body.appendChild(successDiv);
    };
  
    /**
     * Sets button to loading state
     * @param {HTMLElement} button - Button element
     * @param {boolean} isLoading - Whether to show loading state
     * @returns {string} Original button text
     */
    const setButtonLoading = (button, isLoading) => {
      const originalText = button.innerHTML;
      
      if (isLoading) {
        button.innerHTML = '<span class="inline-block animate-spin mr-2">↻</span> Creating Account...';
        button.disabled = true;
      } else {
        button.disabled = false;
      }
      
      return originalText;
    };
  
    /**
     * Validates all form inputs
     * @param {Object} formData - Form data to validate
     * @returns {boolean} Whether validation passed
     */
    const validateForm = (formData) => {
      let isValid = true;
  
      // Name validation
      if (formData.name === '' || formData.name.split(' ').filter(word => word.length > 0).length < 2) {
        showError('name', 'Please enter your full name (first and last name)');
        isValid = false;
      }
  
      // Email validation
      if (!isValidEmail(formData.email)) {
        showError('email', 'Please enter a valid email address');
        isValid = false;
      }
  
      // Password validation
      if (formData.password.length < 8) {
        showError('password', 'Password must be at least 8 characters long');
        isValid = false;
      } else if (!/\d/.test(formData.password)) {
        showError('password', 'Password must contain at least one number');
        isValid = false;
      } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) {
        showError('password', 'Password must contain at least one special character');
        isValid = false;
      }
  
      // Password confirmation
      if (formData.password !== formData.confirmPassword) {
        showError('confirmPassword', 'Passwords do not match');
        isValid = false;
      }
  
      // Date of birth validation
      if (!formData.dob) {
        showError('dob', 'Please enter your date of birth');
        isValid = false;
      }
  
      // Gender validation
      if (!formData.gender) {
        showError('gender', 'Please select your gender');
        isValid = false;
      }
  
      // Height validation
      if (isNaN(formData.height) || formData.height <= 0) {
        showError('height', 'Please enter a valid height');
        isValid = false;
      }
  
      // Weight validation
      if (isNaN(formData.weight) || formData.weight <= 0) {
        showError('weight', 'Please enter a valid weight');
        isValid = false;
      }
  
      // Activity level validation
      if (!formData.activityLevel) {
        showError('activityLevel', 'Please select an activity level');
        isValid = false;
      }
  
      // Terms validation
      if (!formData.termsChecked) {
        showError('terms', 'You must agree to the Terms of Service and Privacy Policy');
        isValid = false;
      }
  
      return isValid;
    };
  
    /**
     * Collects form data from the signup form
     * @returns {Object} Form data object
     */
    const collectFormData = () => {
      const form = document.getElementById(config.formId);
      
      return {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        confirmPassword: document.getElementById('confirmPassword').value,
        dob: document.getElementById('dob').value,
        gender: document.getElementById('gender').value,
        height: parseFloat(document.getElementById('height').value),
        weight: parseFloat(document.getElementById('weight').value),
        activityLevel: document.getElementById('activityLevel').value,
        termsChecked: document.getElementById('terms').checked
      };
    };
  
    /**
     * Submits registration data to the API
     * @param {Object} userData - User data to submit
     * @param {HTMLElement} submitButton - Submit button element
     * @returns {Promise} Promise resolving to the API response
     */
    const submitRegistration = async (userData, submitButton) => {
      // Format the data according to API requirements
      const apiData = {
        name: userData.name,
        email: userData.email,
        password: userData.password,
        dob: userData.dob,
        gender: userData.gender,
        height: userData.height,
        weight: userData.weight,
        initialActivityLevel: userData.activityLevel
      };
  
      try {
        // Set button to loading state
        const originalButtonText = setButtonLoading(submitButton, true);
        
        // Make the API request
        const response = await fetch(config.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(apiData)
        });
  
        // Parse the JSON response
        const data = await response.json();
  
        // Handle successful registration
        if (data.message) {
          showSuccessMessage('Account created successfully! Redirecting to dashboard...');
          setTimeout(() => {
            window.location.href = config.redirectPath;
          }, 1500);
          return { success: true };
        } 
        // Handle API errors
        else {
          const errorMessage = data.error || 
                              data["Database error"] || 
                              data["Validation error"] ||
                              'Registration failed.';
          showError('email', errorMessage);
          return { success: false, error: errorMessage };
        }
      } catch (error) {
        console.error('Error:', error);
        showError('email', 'An error occurred. Please try again later.');
        return { success: false, error: 'Connection error' };
      } finally {
        // Reset button state
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
      }
    };
  
    /**
     * Initializes the signup form handlers
     */
    const initialize = () => {
      // Wait for DOM to be fully loaded
      document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById(config.formId);
        
        if (form) {
          form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Clear any previous errors
            clearErrors();
            
            // Collect form data
            const formData = collectFormData();
            
            // Validate form inputs
            if (validateForm(formData)) {
              // Submit registration if validation passes
              const submitButton = form.querySelector('button[type="submit"]');
              await submitRegistration(formData, submitButton);
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
      validateForm,   // Exposed for testing
      submitRegistration // Exposed for testing or external usage
    };
  })();
  
  // Initialize the signup form
  CoachSignup.initialize();
