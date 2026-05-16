/**
 * Initializes a command-menu style filter for categories.
 * This function finds all necessary child elements by their ID suffixes and sets up event listeners.
 * @param {string} containerId The ID of the main container element for the filter.
 */
function initCategoryFilter(containerId) {
    const commandContainer = document.getElementById(containerId);
    if (!commandContainer) return;

    // Use querySelector to find elements within the specific container
    const searchInput = commandContainer.querySelector('#category-filter-search');
    const menu = commandContainer.querySelector('#category-filter-menu');
    const hiddenId = commandContainer.querySelector('#hidden-category-id');
    const options = commandContainer.querySelectorAll('.category-option');
    const noFound = commandContainer.querySelector('#no-category-found');

    if (!searchInput || !menu || !hiddenId || !options.length || !noFound) {
        console.warn(`Could not find all required elements for the category filter inside '${containerId}'. Initialization aborted.`);
        return;
    }

    let currentSelectedName = searchInput.value;

    const openMenu = () => {
        menu.classList.remove('hidden');
        searchInput.select();
    };

    const closeMenu = () => {
        menu.classList.add('hidden');
        searchInput.value = currentSelectedName; // Restore if closed without selection
    };

    searchInput.addEventListener('focus', openMenu);

    document.addEventListener('click', (e) => {
        if (!commandContainer.contains(e.target)) {
            closeMenu();
        }
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const firstVisible = Array.from(options).find(opt => !opt.classList.contains('hidden'));
            if (firstVisible) firstVisible.click();
        }
        if (e.key === 'Escape') {
            closeMenu();
        }
    });

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        let hasResults = false;
        options.forEach(opt => {
            const name = (opt.dataset.name || 'todas as categorias').toLowerCase();
            if (name.includes(query)) {
                opt.classList.remove('hidden');
                hasResults = true;
            } else {
                opt.classList.add('hidden');
            }
        });
        noFound.classList.toggle('hidden', hasResults);
    });

    options.forEach(opt => {
        opt.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = opt.dataset.id;
            const name = opt.dataset.name || 'Todas as Categorias';

            hiddenId.value = id;
            currentSelectedName = id ? name : '';
            searchInput.value = currentSelectedName;

            closeMenu();
            commandContainer.closest('form').submit();
        });
    });
}


/**
 * Renders simple sparkline charts in SVG elements with a `.sparkline` class.
 * It reads numeric data from a `data-values` attribute on the SVG element.
 */
function initSparklines() {
    document.querySelectorAll('.sparkline').forEach(svg => {
        try {
            svg.innerHTML = ''; // Clear previous renderings

            const data = JSON.parse(svg.dataset.values);
            if (!data || data.length < 2) return;

            const width = svg.clientWidth || 128;
            const height = svg.clientHeight || 32;
            const max = Math.max(...data);
            const min = Math.min(...data);
            const range = max - min || 1;
            const padding = 2;
            const drawHeight = height - (padding * 2);

            const points = data.map((val, index) => {
                const x = (index / (data.length - 1)) * width;
                const y = height - padding - ((val - min) / range) * drawHeight;
                return `${x.toFixed(2)},${y.toFixed(2)}`;
            }).join(' ');

            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', points);
            polyline.setAttribute('fill', 'none');
            polyline.setAttribute('stroke', 'currentColor');
            polyline.setAttribute('stroke-width', '2');
            polyline.setAttribute('stroke-linecap', 'round');
            polyline.setAttribute('stroke-linejoin', 'round');
            svg.appendChild(polyline);
        } catch (e) {
            console.error("Error drawing sparkline on element:", svg, e);
        }
    });
}

/**
 * Basic masking utilities for Brazilian formats
 */
const Masks = {
    cpf: (value) => {
        return value
            .replace(/\D/g, '')
            .replace(/(\d{3})(\d)/, '$1.$2')
            .replace(/(\d{3})(\d)/, '$1.$2')
            .replace(/(\d{3})(\d{1,2})/, '$1-$2')
            .replace(/(-\d{2})\d+?$/, '$1');
    },
    cnpj: (value) => {
        return value
            .replace(/\D/g, '')
            .replace(/(\d{2})(\d)/, '$1.$2')
            .replace(/(\d{3})(\d)/, '$1.$3')
            .replace(/(\d{3})(\d)/, '$1/$2')
            .replace(/(\d{4})(\d)/, '$1-$2')
            .replace(/(-\d{2})\d+?$/, '$1');
    },
    phone: (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 10) {
            return numbers
                .replace(/(\d{2})(\d)/, '($1) $2')
                .replace(/(\d{4})(\d)/, '$1-$2')
                .replace(/(-\d{4})\d+?$/, '$1');
        } else {
            return numbers
                .replace(/(\d{2})(\d)/, '($1) $2')
                .replace(/(\d{5})(\d)/, '$1-$2')
                .replace(/(-\d{4})\d+?$/, '$1');
        }
    },
    email: (value) => {
        return value.toLowerCase().replace(/\s/g, '');
    }
};

/**
 * Initializes masks for specific inputs
 */
function initMasks() {
    const cpfInput = document.getElementById('id_cpf');
    const cnpjInput = document.getElementById('id_cnpj');
    const phoneInput = document.getElementById('id_phone');
    const emailInput = document.getElementById('id_email');

    if (cpfInput) {
        cpfInput.addEventListener('input', (e) => {
            e.target.value = Masks.cpf(e.target.value);
        });
        if (cpfInput.value) cpfInput.value = Masks.cpf(cpfInput.value);
    }

    if (cnpjInput) {
        cnpjInput.addEventListener('input', (e) => {
            e.target.value = Masks.cnpj(e.target.value);
        });
        if (cnpjInput.value) cnpjInput.value = Masks.cnpj(cnpjInput.value);
    }

    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            e.target.value = Masks.phone(e.target.value);
        });
        if (phoneInput.value) phoneInput.value = Masks.phone(phoneInput.value);
    }

    if (emailInput) {
        emailInput.addEventListener('input', (e) => {
            e.target.value = Masks.email(e.target.value);
        });
    }
}

// Run initializations on initial page load
document.addEventListener('DOMContentLoaded', () => {
    initSparklines();
    initMasks();
});

// Also re-run after HTMX swaps
document.body.addEventListener('htmx:afterSwap', () => {
    initSparklines();
    initMasks();
});
