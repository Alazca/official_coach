// login.js

// Assumes credentials.js is loaded first, so `Credentials` is available globally.
// Also assumes you have defined API_URL somewhere (e.g. in credentials.js or a separate config file).

document.addEventListener('DOMContentLoaded', () => {
    const loginForm     = document.getElementById('loginForm');
    const emailInput    = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginMessage  = document.getElementById('loginMessage');
    const submitButton  = loginForm.querySelector('button[type="submit"]');
  
    // If already logged in, send straight to dashboard
    if (Credentials.isAuthenticated()) {
      window.location.href = 'dashboard.html';
      return;
    }
  
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginMessage.textContent = '';
      submitButton.disabled   = true;
      submitButton.textContent = 'Logging in…';
  
      const email    = emailInput.value.trim();
      const password = passwordInput.value;
  
      if (!email || !password) {
        loginMessage.textContent = 'Please enter both email and password.';
        resetButton();
        return;
      }
  
      try {
        const res = await fetch(`${API_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
  
        const data = await res.json();
        if (!res.ok) {
          loginMessage.textContent = data.message || 'Login failed. Check your credentials.';
          resetButton();
          return;
        }
  
        // Use your Credentials helper to save the token
        Credentials.saveToken(data.token);
  

        // Redirect to your protected page
        window.location.href = 'dashboard.html';
  
      } catch (err) {
        console.error('Login error:', err);
        loginMessage.textContent = 'Network error. Please try again.';
        resetButton();
      }
    });
  
    function resetButton() {
      submitButton.disabled   = false;
      submitButton.textContent = 'Log In';
    }
  });
  