/**
 * ui.js
 * Shared UI utilities for notifications, modals, etc.
 */

const UIModule = (function() {
    /**
     * Show a modal dialog
     * @param {Object} options - Modal options
     * @param {string} options.title - Modal title
     * @param {string} options.content - Modal HTML content
     * @param {Function} options.onSubmit - Submit callback
     * @param {string} [options.className] - Additional CSS class for the modal
     * @param {string} [options.submitText] - Text for submit button
     * @param {string} [options.cancelText] - Text for cancel button
     */
    function showModal(options) {
        // Defaults
        const settings = Object.assign({
            title: 'Modal',
            content: '',
            onSubmit: () => true,
            className: '',
            submitText: 'Save',
            cancelText: 'Cancel'
        }, options);

        // Create modal element
        const modal = document.createElement('div');
        modal.className = `fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 ${settings.className}`;
        
        modal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full text-white">
                <h3 class="text-2xl font-bold mb-6">${settings.title}</h3>
                <div class="modal-content">${settings.content}</div>
                <div class="flex gap-4 mt-6">
                    <button type="button" class="modal-submit flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">
                        ${settings.submitText}
                    </button>
                    <button type="button" class="modal-cancel flex-1 bg-gray-700 text-white py-2 rounded-lg hover:bg-gray-600">
                        ${settings.cancelText}
                    </button>
                </div>
            </div>
        `;

        // Add to DOM
        document.body.appendChild(modal);

        // Event handlers
        modal.querySelector('.modal-submit').addEventListener('click', () => {
            const result = settings.onSubmit();
            if (result) {
                modal.remove();
            }
        });

        modal.querySelector('.modal-cancel').addEventListener('click', () => {
            modal.remove();
        });

        return modal;
    }

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} [type='success'] - Notification type (success/error)
     * @param {number} [duration=3000] - Duration in milliseconds
     */
    function showToast(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 z-50 ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        } text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Auto-hide after duration
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        return toast;
    }

    /**
     * Create a confirmation dialog
     * @param {string} message - Confirmation message
     * @param {Function} onConfirm - Callback when confirmed
     * @param {Function} [onCancel] - Callback when canceled
     */
    function confirmDialog(message, onConfirm, onCancel = () => {}) {
        return showModal({
            title: 'Confirm',
            content: `<p class="text-white mb-4">${message}</p>`,
            submitText: 'Confirm',
            onSubmit: () => {
                onConfirm();
                return true;
            }
        });
    }

    /**
     * Format a date in a consistent way
     * @param {Date|string} date - Date to format
     * @param {string} [format='short'] - Format type (short/long)
     * @returns {string} - Formatted date string
     */
    function formatDate(date, format = 'short') {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        if (format === 'short') {
            return dateObj.toLocaleDateString();
        } else if (format === 'long') {
            return dateObj.toLocaleDateString(undefined, { 
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
        
        return dateObj.toLocaleDateString();
    }

    /**
     * Initialize button interactions
     * @param {HTMLElement} button - Button element to initialize
     */
    function initializeButton(button) {
        if (!button) return;
        
        // Add ripple effect
        button.addEventListener('mousedown', function(e) {
            const ripple = document.createElement('div');
            const rect = button.getBoundingClientRect();
            ripple.className = 'ripple';
            ripple.style.left = `${e.clientX - rect.left}px`;
            ripple.style.top = `${e.clientY - rect.top}px`;
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });

        // Add active state
        button.addEventListener('mousedown', () => {
            button.classList.add('active');
        });
        
        button.addEventListener('mouseup', () => {
            button.classList.remove('active');
        });
    }

    /**
     * Initialize all buttons on the page
     */
    function initializeAllButtons() {
        document.querySelectorAll('button').forEach(initializeButton);
    }

    // Public API
    return {
        showModal,
        showToast,
        confirmDialog,
        formatDate,
        initializeButton,
        initializeAllButtons
    };
})();