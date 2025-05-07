/**
 * credentials.js
 * Manages JWT tokens and authentication status
 */
const Credentials = (function () {
  const TOKEN_KEY = "access_token";

  // Helper to decode JWT payload
  function parseJwt(token) {
    try {
      const base64Url = token.split(".")[1];
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      return JSON.parse(window.atob(base64));
    } catch (e) {
      return null;
    }
  }

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

    // Check if user is logged in with a non-expired token
    isAuthenticated: function () {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) return false;

      // Check if token is expired
      const payload = parseJwt(token);
      if (!payload) return false;

      // JWT exp is in seconds since epoch
      const expiry = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < expiry;
    },

    // Get user info from token
    getUserInfo: function () {
      const token = this.getToken();
      if (!token) return null;
      return parseJwt(token);
    },
  };
})();