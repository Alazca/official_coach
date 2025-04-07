/**
 * Authentication Service - Handles login requests and token management
 * 
 * This module provides functionality to authenticate users against the backend API,
 * store access tokens securely, and manage the authentication state throughout
 * the user session.
 */

// Configuration
const API_BASE_URL = '/api'; // Base URL for API endpoints

/**
 * Attempts to log in a user with the provided credentials
 * @param {string} email - The user's email address
 * @param {string} password - The user's password
 * @returns {Promise} A promise that resolves with the login result
 */

async function login(email, password) {
  try {
    // Prepare the request with proper headers and body
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    // Parse the JSON response
    const data = await response.json();

    // Check if the request was successful
    if (!response.ok) {
      // Handle error responses with appropriate messaging
      throw new Error(data.error || 'Login failed');
    }

    // Important: Extract the access token created by the backend
    const accessToken = data['access token'];
    
    // Store the access token for the user session
    saveToken(accessToken);
    
    // Log successful authentication (for debugging)
    console.log('Authentication successful, token received and stored');

    // Return the successful response
    return {
      success: true,
      message: data.message,
      token: accessToken
    };
  } catch (error) {
    // Log the error for debugging purposes
    console.error('Login error:', error);

    // Return a structured error response
    return {
      success: false,
      message: error.message || 'An unexpected error occurred during login',
    };
  }
}

/**
 * Saves the access token to session storage
 * @param {string} token - The access token to save
 */
function saveToken(token) {
  // Store the token in sessionStorage for this session only
  sessionStorage.setItem('accessToken', token);
}

/**
 * Retrieves the current access token from storage
 * @returns {string|null} The access token or null if not found
 */
function getToken() {
  return sessionStorage.getItem('accessToken');
}

/**
 * Checks if the user is currently authenticated
 * @returns {boolean} True if the user has a valid token, false otherwise
 */
function isAuthenticated() {
  // Using double negation to convert to boolean
  return !!getToken();
}

/**
 * Logs out the current user by removing the stored token
 */
function logout() {
  sessionStorage.removeItem('accessToken');
}

/**
 * Adds the authorization header to API requests
 * @param {Object} headers - The existing headers object to modify
 * @returns {Object} The headers object with authorization added (if available)
 */
function addAuthHeader(headers = {}) {
  const token = getToken();
  if (token) {
    return {
      ...headers,
      'Authorization': `Bearer ${token}`
    };
  }
  return headers;
}

// Export the authentication functions as a module
export const AuthService = {
  login,
  logout,
  getToken,
  isAuthenticated,
  addAuthHeader
};
