document.addEventListener('DOMContentLoaded', function() {
    // Get all steps and buttons
    const steps = document.querySelectorAll('.step');
    const continueButtons = document.querySelectorAll('.continue-btn');
    const backButtons = document.querySelectorAll('.back-btn');
    const progressBar = document.getElementById('progress-bar');
    const stepIndicator = document.getElementById('step-indicator');
    const progressPercentage = document.getElementById('progress-percentage');
    let currentStep = 1;

    // Function to show a specific step
    function showStep(stepNumber) {
        steps.forEach(step => step.classList.remove('active'));
        document.getElementById(`step-${stepNumber}`).classList.add('active');
        
        // Update progress
        const progress = ((stepNumber - 1) / (steps.length - 1)) * 100;
        progressBar.style.width = `${progress}%`;
        stepIndicator.textContent = `Step ${stepNumber} of ${steps.length}`;
        progressPercentage.textContent = `${Math.round(progress)}%`;
        currentStep = stepNumber;
    }

    // Handle continue button clicks
    continueButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Validate current step
            const currentStepElement = document.getElementById(`step-${currentStep}`);
            const requiredInputs = currentStepElement.querySelectorAll('input[required]');
            let isValid = true;

            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('form-error');
                    const errorDiv = input.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('error-message')) {
                        errorDiv.textContent = 'This field is required';
                    }
                } else {
                    input.classList.remove('form-error');
                    const errorDiv = input.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('error-message')) {
                        errorDiv.textContent = '';
                    }
                }
            });

            if (isValid) {
                if (currentStep < steps.length) {
                    showStep(currentStep + 1);
                } else {
                    // Submit the form
                    submitForm();
                }
            }
        });
    });

    // Handle back button clicks
    backButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentStep > 1) {
                showStep(currentStep - 1);
            }
        });
    });

    // Function to submit the form
    function submitForm() {
        const formData = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            gender: document.getElementById('gender').value,
            dob: document.getElementById('dob').value,
            height: document.getElementById('height').value,
            weight: document.getElementById('weight').value,
            initialActivityLevel: document.getElementById('activity-level').value
        };

        fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Registration successful
                window.location.href = '/login';
            } else {
                // Show error message
                alert(data.error || 'Registration failed. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }
}); 