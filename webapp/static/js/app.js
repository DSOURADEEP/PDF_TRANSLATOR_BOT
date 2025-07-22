// Main JavaScript for PDF Translation Bot

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });

    // File input enhancements
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            updateFileInputLabel(e.target);
        });
    });

    // Initialize drag and drop for file inputs
    initializeDragAndDrop();
});

// Update file input labels to show selected files
function updateFileInputLabel(input) {
    const files = input.files;
    const label = input.nextElementSibling;
    
    if (files.length > 0) {
        if (files.length === 1) {
            label.textContent = files[0].name;
        } else {
            label.textContent = `${files.length} files selected`;
        }
        label.classList.add('text-success');
    } else {
        label.textContent = 'Choose file(s)';
        label.classList.remove('text-success');
    }
}

// Initialize drag and drop functionality
function initializeDragAndDrop() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const container = input.closest('.card-body') || input.parentElement;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            container.addEventListener(eventName, () => {
                container.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            container.addEventListener(eventName, () => {
                container.classList.remove('dragover');
            }, false);
        });

        container.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            input.files = files;
            updateFileInputLabel(input);
            
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
        }, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Utility functions
const Utils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Format time duration
    formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    // Show loading state
    showLoading: function(element, text = 'Loading...') {
        element.classList.add('loading');
        element.setAttribute('data-original-text', element.textContent);
        element.textContent = text;
        element.disabled = true;
    },

    // Hide loading state
    hideLoading: function(element) {
        element.classList.remove('loading');
        element.textContent = element.getAttribute('data-original-text') || 'Submit';
        element.disabled = false;
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Validate file type
    validateFileType: function(file, allowedTypes = ['.pdf']) {
        const fileName = file.name.toLowerCase();
        return allowedTypes.some(type => fileName.endsWith(type.toLowerCase()));
    },

    // Validate file size
    validateFileSize: function(file, maxSizeBytes = 50 * 1024 * 1024) {
        return file.size <= maxSizeBytes;
    }
};

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    Utils.showToast('An unexpected error occurred. Please try again.', 'danger');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled Promise Rejection:', e.reason);
    Utils.showToast('An unexpected error occurred. Please try again.', 'danger');
});

// Export Utils for use in other scripts
window.Utils = Utils;
