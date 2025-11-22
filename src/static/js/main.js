// Main JavaScript for Inventory Management System - v2.0

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFlashMessages();
    initDeleteConfirmations();
    initFormValidation();
    initTooltips();
    initPopovers();
    initSmoothScroll();
    initScrollReveal();
    initAnimations();
    initNumberFormatting();

    // Auto-hide flash messages after 5 seconds with animation
    function initFlashMessages() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach((alert, index) => {
            // Stagger animation
            alert.style.animationDelay = `${index * 0.1}s`;
            
            setTimeout(() => {
                alert.classList.add('animate-fade-out');
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 300);
            }, 5000);
        });
    }

    // Enhanced delete confirmations with modal
    function initDeleteConfirmations() {
        const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const itemName = this.dataset.itemName || 'this item';
                
                if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                    // If button is in a form, submit it
                    const form = this.closest('form');
                    if (form) {
                        form.submit();
                    } else if (this.href) {
                        window.location.href = this.href;
                    }
                }
            });
        });
    }

    // Enhanced form validation with custom messages
    function initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Focus first invalid field
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.classList.add('animate-shake');
                        setTimeout(() => firstInvalid.classList.remove('animate-shake'), 500);
                    }
                }
                form.classList.add('was-validated');
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    if (this.checkValidity()) {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    } else {
                        this.classList.remove('is-valid');
                        this.classList.add('is-invalid');
                    }
                });
            });
        });
    }

    // Initialize Bootstrap tooltips with modern styling
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                animation: true,
                delay: { show: 300, hide: 100 }
            });
        });
    }

    // Initialize Bootstrap popovers
    function initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl, {
                trigger: 'focus',
                animation: true
            });
        });
    }

    // Smooth scroll for anchor links
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Scroll reveal animations
    function initScrollReveal() {
        const revealElements = document.querySelectorAll('.scroll-reveal');
        
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        revealElements.forEach(el => revealObserver.observe(el));
    }

    // Stagger animations for items in a container
    function initAnimations() {
        const staggerContainers = document.querySelectorAll('.stagger-container');
        staggerContainers.forEach(container => {
            const items = container.querySelectorAll('.stagger-item');
            items.forEach((item, index) => {
                item.style.animationDelay = `${index * 0.1}s`;
                item.classList.add('animate-fade-in-up');
            });
        });
    }

    // Number input formatting
    function initNumberFormatting() {
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value && this.step !== "1") {
                    this.value = parseFloat(this.value).toFixed(2);
                }
            });
        });
    }

// AJAX helper function
function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options)
        .then(response => response.json())
        .catch(error => {
            console.error('Error:', error);
            throw error;
        });
}

// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = '<div class="spinner-border text-light" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}
