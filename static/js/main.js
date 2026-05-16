function closeToast(button) {
    const toast = button.closest('.toast');
    if (!toast) return;
    toast.classList.add('animate-out', 'fade-out', 'slide-out-to-right-full', 'duration-500');
    setTimeout(() => toast.remove(), 500);
}

function toggleLogoutModal(show) {
    const modal = document.getElementById('logoutModal');
    if (!modal) return;
    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function togglePasswordVisibility(button) {
    const input = button.parentElement.querySelector('input');
    const iconEye = button.querySelector('[data-lucide="eye"]');
    const iconEyeOff = button.querySelector('[data-lucide="eye-off"]');

    if (!input || !iconEye || !iconEyeOff) return;

    if (input.type === 'password') {
        input.type = 'text';
        iconEye.classList.add('hidden');
        iconEyeOff.classList.remove('hidden');
    } else {
        input.type = 'password';
        iconEye.classList.remove('hidden');
        iconEyeOff.classList.add('hidden');
    }
}

function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

// --- Initializers ---

// Initialize global scripts on first page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize lucide icons
    lucide.createIcons();

    // Auto-hide existing toasts that are present on page load
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            // Check if toast is still in the DOM
            if (toast.parentElement) {
                toast.classList.add('animate-out', 'fade-out', 'slide-out-to-right-full', 'duration-500');
                setTimeout(() => toast.remove(), 500);
            }
        }, 6000);
    });
});


// Pass CSRF token on all HTMX requests (required for hx-post/hx-put/hx-delete)
document.body.addEventListener('htmx:configRequest', (e) => {
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrf) {
        e.detail.headers['X-CSRFToken'] = csrf;
    }
});

// Re-initialize icons after AJAX content swaps
document.body.addEventListener('htmx:afterSwap', function () {
    lucide.createIcons();
});

// Add global keyboard shortcut for closing modals via Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    document.querySelectorAll('.theme-sun, .theme-moon').forEach(el => {
        el.classList.toggle('hidden');
    });
    lucide.createIcons();
}

function setViewMode(context, mode) {
    document.querySelectorAll('[data-view-mode="true"]').forEach(btn => {
        const isActive = btn.dataset.mode === mode;
        btn.classList.toggle('bg-background', isActive);
        btn.classList.toggle('shadow-sm', isActive);
        btn.classList.toggle('text-foreground', isActive);
        btn.classList.toggle('text-muted-foreground', !isActive);
    });

    const grid = document.getElementById('view-grid');
    const table = document.getElementById('view-table');
    if (grid) grid.classList.toggle('hidden', mode !== 'grid');
    if (table) table.classList.toggle('hidden', mode !== 'table');

    const container = document.getElementById('product-list-container');
    if (container) container.dataset.viewMode = mode;

    lucide.createIcons();
}
