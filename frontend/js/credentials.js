/**
 * credentials.js
 * Manages JWT tokens and authentication status
 */

const Credentials = (function () {
  const TOKEN_KEY = "jwt_token";

  return {
    // Save JWT to localStorage
    saveToken: function (token) {
      localStorage.setItem(TOKEN_KEY, token);
    },

    // Retrieve JWT from localStorage
    getToken: function () {
      return localStorage.getItem(TOKEN_KEY);
    },

    // Remove JWT (on logout)
    clearToken: function () {
      localStorage.removeItem(TOKEN_KEY);
    },

    // Check if user is logged in
    isAuthenticated: function () {
      return !!localStorage.getItem(TOKEN_KEY);
    },
  };
})();
