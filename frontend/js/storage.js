/**
 * storage.js
 * LocalStorage abstraction for data persistence
 */

const StorageModule = (function() {
    /**
     * Get an item from localStorage with default value if not found
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} - Parsed data or default value
     */
    function getItem(key, defaultValue = null) {
        const storedData = localStorage.getItem(key);
        if (storedData === null) {
            return defaultValue;
        }
        try {
            return JSON.parse(storedData);
        } catch (e) {
            console.error(`Error parsing data for key ${key}:`, e);
            return defaultValue;
        }
    }

    /**
     * Set an item in localStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store (will be stringified)
     */
    function setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error(`Error storing data for key ${key}:`, e);
        }
    }

    /**
     * Add an item to an array in localStorage
     * @param {string} key - Storage key for the array
     * @param {*} item - Item to add to the array
     */
    function addToArray(key, item) {
        const array = getItem(key, []);
        array.push(item);
        setItem(key, array);
    }

    /**
     * Remove items from an array in localStorage based on a filter function
     * @param {string} key - Storage key for the array
     * @param {Function} filterFn - Filter function that returns true for items to keep
     */
    function filterArray(key, filterFn) {
        const array = getItem(key, []);
        const filtered = array.filter(filterFn);
        setItem(key, filtered);
    }

    // Public API
    return {
        getItem,
        setItem,
        addToArray,
        filterArray
    };
})();