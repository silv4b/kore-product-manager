/**
 * REWRITE DE PRODUCT_LIST.JS - VERSÃO ULTRA-ROBUSTA COM DEDUPLICAÇÃO GARANTIDA
 */

// Estado global para o modal
let currentBulkAction = null;

// Helper para pegar IDs selecionados sem duplicatas (essencial para Grid/Table sync)
function getKoreUniqueSelectedIds() {
    const checkboxes = document.querySelectorAll('.checkbox-product:checked');
    const uniqueIds = new Set();
    checkboxes.forEach(cb => {
        if (cb.value) {
            uniqueIds.add(cb.value.toString().trim());
        }
    });
    return Array.from(uniqueIds);
}

// Funções globais
window.submitBulkAction = function (action) {
    const input = document.getElementById('bulk-action-input');
    const form = document.getElementById('bulk-actions-form');
    if (!input || !form) return;

    const selectedIds = getKoreUniqueSelectedIds();
    const selectedCount = selectedIds.length;

    if (selectedCount === 0) return;

    // Armazena a ação para execução posterior
    currentBulkAction = action;

    // Abre o modal de confirmação genérico
    window.openBulkActionModal(action, selectedCount);
};

window.openBulkActionModal = function (action, count) {
    const modal = document.getElementById('bulk-action-modal');
    const title = document.getElementById('bulk-modal-title');
    const desc = document.getElementById('bulk-modal-description');
    const countDisplay = document.getElementById('bulk-modal-count');
    const warning = document.getElementById('bulk-modal-warning');
    const confirmBtn = document.getElementById('bulk-modal-confirm-btn');
    const card = document.getElementById('bulk-modal-card');
    const icon = document.getElementById('bulk-modal-icon');
    const extraInfo = document.getElementById('bulk-modal-extra-info');

    if (!modal) return;

    // Reset de estilos e conteúdos
    card.className = "card max-w-md w-full border-border shadow-2xl animate-in zoom-in-95 duration-200";
    confirmBtn.className = "btn btn-primary flex-1 sm:flex-none justify-center font-bold h-11 px-8";
    extraInfo.classList.add('hidden');
    icon.classList.remove('text-destructive', 'text-primary', 'text-muted-foreground');

    countDisplay.textContent = count;

    if (action === 'delete') {
        title.textContent = "Excluir em Massa";
        desc.textContent = "Você está prestes a remover permanentemente múltiplos itens.";
        warning.innerHTML = 'Esta ação <span class="font-bold text-destructive">não pode ser desfeita</span>. Todos os dados serão apagados.';
        card.classList.add('border-destructive/20');
        confirmBtn.className = "btn btn-ghost bg-destructive text-white hover:bg-destructive/90 flex-1 sm:flex-none justify-center font-bold h-11 px-8";
        icon.setAttribute('data-lucide', 'alert-triangle');
        icon.classList.add('text-destructive');
    } else if (action === 'make_public') {
        title.textContent = "Tornar Públicos";
        desc.textContent = "Os produtos selecionados ficarão visíveis no catálogo.";
        warning.textContent = "Isso permitirá que clientes vejam esses preços e detalhes.";
        icon.setAttribute('data-lucide', 'eye');
        icon.classList.add('text-primary');
    } else if (action === 'make_private') {
        title.textContent = "Tornar Privados";
        desc.textContent = "Os produtos selecionados serão ocultados do catálogo público.";
        warning.textContent = "Apenas usuários autenticados poderão ver estes itens.";
        icon.setAttribute('data-lucide', 'eye-off');
        icon.classList.add('text-muted-foreground');
    } else if (action === 'add_category') {
        const searchInput = document.getElementById('bulk-category-search');
        const catName = searchInput ? searchInput.value : "selecionada";
        title.textContent = "Adicionar Categoria";
        desc.textContent = "Vincular uma nova categoria aos produtos selecionados.";
        warning.textContent = "Os produtos manterão suas categorias atuais e ganharão esta nova.";
        extraInfo.innerHTML = `<p class="text-xs font-bold text-muted-foreground uppercase mb-1">Nova Categoria:</p><p class="text-sm font-bold text-primary">${catName}</p>`;
        extraInfo.classList.remove('hidden');
        icon.setAttribute('data-lucide', 'tag');
        icon.classList.add('text-primary');
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    if (window.lucide) window.lucide.createIcons();
};

window.closeBulkActionModal = function () {
    const modal = document.getElementById('bulk-action-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
};

window.confirmBulkAction = function () {
    const input = document.getElementById('bulk-action-input');
    const form = document.getElementById('bulk-actions-form');
    if (input && form && currentBulkAction) {
        input.value = currentBulkAction;
        form.submit();
    }
};

window.clearSelection = function () {
    document.querySelectorAll('.checkbox-product').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('select-all');
    if (selectAll) selectAll.checked = false;

    const searchInput = document.getElementById('bulk-category-search');
    const hiddenId = document.getElementById('bulk-category-id');
    const applyBtn = document.getElementById('bulk-apply-cat-btn');
    if (searchInput) searchInput.value = "";
    if (hiddenId) hiddenId.value = "";
    if (applyBtn) applyBtn.disabled = true;

    window.updateBulkActionBar();
};

window.updateBulkActionBar = function () {
    const container = document.getElementById('product-list-container');
    const viewMode = container ? container.dataset.viewMode : 'grid';
    const selectedCount = getKoreUniqueSelectedIds().length;
    const actionBar = document.getElementById('bulk-action-bar');
    const countBadge = document.getElementById('selected-count-badge');

    if (!actionBar) return;

    // Desabilita Bulk Actions em modo Grid (Cards) conforme pedido do usuário
    if (viewMode === 'grid') {
        actionBar.style.setProperty('display', 'none', 'important');
        return;
    }

    if (selectedCount > 0) {
        if (countBadge) countBadge.textContent = selectedCount;
        actionBar.style.setProperty('display', 'block', 'important');
        if (window.lucide) window.lucide.createIcons();
    } else {
        actionBar.style.setProperty('display', 'none', 'important');
    }
};

// Inicialização
function initKoreBulkActions() {
    const selectAllBtn = document.getElementById('select-all');

    if (selectAllBtn) {
        selectAllBtn.onclick = function () {
            const isChecked = this.checked;
            document.querySelectorAll('.checkbox-product').forEach(cb => {
                cb.checked = isChecked;
            });
            window.updateBulkActionBar();
        };
    }

    // Delegation centralizada
    document.body.addEventListener('change', function (e) {
        if (e.target && e.target.classList.contains('checkbox-product')) {
            const isChecked = e.target.checked;
            const productId = e.target.value;

            // Sincroniza Grid e Tabela
            document.querySelectorAll(`.checkbox-product[value="${productId}"]`).forEach(cb => {
                cb.checked = isChecked;
            });

            // Atualiza Select All checkbox
            if (selectAllBtn && !isChecked) {
                selectAllBtn.checked = false;
            }

            window.updateBulkActionBar();
        }
    });

    // Categoria
    const catContainer = document.getElementById('bulk-category-selector');
    if (catContainer) {
        const searchInput = document.getElementById('bulk-category-search');
        const menu = document.getElementById('bulk-category-menu');
        const hiddenId = document.getElementById('bulk-category-id');
        const applyBtn = document.getElementById('bulk-apply-cat-btn');

        if (searchInput && menu) {
            searchInput.addEventListener('focus', () => menu.classList.remove('hidden'));

            document.addEventListener('click', (e) => {
                if (!catContainer.contains(e.target)) menu.classList.add('hidden');
            });

            searchInput.addEventListener('input', () => {
                const query = searchInput.value.toLowerCase().trim();
                const options = menu.querySelectorAll('.bulk-category-option');
                options.forEach(opt => {
                    const name = opt.dataset.name.toLowerCase();
                    opt.style.display = name.includes(query) ? 'flex' : 'none';
                });
                if (query === "") {
                    hiddenId.value = "";
                    if (applyBtn) applyBtn.disabled = true;
                }
            });

            menu.addEventListener('click', (e) => {
                const opt = e.target.closest('.bulk-category-option');
                if (opt) {
                    searchInput.value = opt.dataset.name;
                    hiddenId.value = opt.dataset.id;
                    menu.classList.add('hidden');
                    if (applyBtn) applyBtn.disabled = false;
                }
            });
        }
    }

    window.updateBulkActionBar();
}

// Boot
function initProductList() {
    initKoreBulkActions();
    initCategoryFilter('category-filter-command');
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProductList);
} else {
    initProductList();
}
