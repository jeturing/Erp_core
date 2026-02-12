/**
 * Global Search Component
 * Búsqueda global con resultados en tiempo real
 */

class GlobalSearch {
    constructor(inputSelector = '#searchInput') {
        this.input = document.querySelector(inputSelector);
        this.results = null;
        this.searchTimeout = null;
        this.isOpen = false;
        this.selectedIndex = -1;
        this.cache = new Map();
        
        if (this.input) {
            this.init();
        }
    }

    init() {
        // Crear contenedor de resultados
        this.createResultsContainer();
        
        // Event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('focus', () => this.handleFocus());
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Cerrar al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.close();
            }
        });

        // Atajo de teclado global (Ctrl+K o Cmd+K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.input.focus();
            }
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    createResultsContainer() {
        // Buscar contenedor padre del input
        const parent = this.input.parentElement;
        parent.style.position = 'relative';

        this.results = document.createElement('div');
        this.results.id = 'search-results';
        this.results.className = `
            absolute top-full left-0 right-0 mt-2 
            bg-white dark:bg-slate-800 
            border border-slate-200 dark:border-slate-700 
            rounded-xl shadow-2xl shadow-slate-900/20 dark:shadow-black/40
            overflow-hidden z-50 hidden
            max-h-96 overflow-y-auto
        `;
        parent.appendChild(this.results);
    }

    handleInput(e) {
        const query = e.target.value.trim();
        
        clearTimeout(this.searchTimeout);
        
        if (query.length < 2) {
            this.close();
            return;
        }

        // Debounce de 300ms
        this.searchTimeout = setTimeout(() => {
            this.search(query);
        }, 300);
    }

    handleFocus() {
        const query = this.input.value.trim();
        if (query.length >= 2 && this.results.innerHTML) {
            this.open();
        }
    }

    handleKeydown(e) {
        if (!this.isOpen) return;

        const items = this.results.querySelectorAll('.search-result-item');
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                this.updateSelection(items);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelection(items);
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    items[this.selectedIndex].click();
                }
                break;
            case 'Escape':
                this.close();
                break;
        }
    }

    updateSelection(items) {
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('bg-slate-100', 'dark:bg-slate-700');
            } else {
                item.classList.remove('bg-slate-100', 'dark:bg-slate-700');
            }
        });
    }

    async search(query) {
        // Verificar cache
        if (this.cache.has(query)) {
            this.renderResults(this.cache.get(query), query);
            return;
        }

        // Mostrar loading
        this.results.innerHTML = `
            <div class="p-4 text-center">
                <div class="animate-spin inline-block w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full"></div>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-2">Buscando...</p>
            </div>
        `;
        this.open();

        try {
            // Buscar en múltiples fuentes en paralelo
            const [tenants] = await Promise.all([
                this.searchTenants(query)
            ]);

            const results = {
                tenants: tenants || [],
                query: query
            };

            // Cachear resultados
            this.cache.set(query, results);

            this.renderResults(results, query);
        } catch (error) {
            console.error('Search error:', error);
            this.results.innerHTML = `
                <div class="p-4 text-center">
                    <span class="material-symbols-outlined text-rose-500 text-3xl">error</span>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-2">Error en la búsqueda</p>
                </div>
            `;
        }
    }

    async searchTenants(query) {
        try {
            const response = await fetch('/api/tenants', { credentials: 'same-origin' });
            if (!response.ok) return [];
            
            const data = await response.json();
            const items = data.items || [];
            const q = query.toLowerCase();
            
            return items.filter(t => 
                t.company_name?.toLowerCase().includes(q) ||
                t.subdomain?.toLowerCase().includes(q) ||
                t.email?.toLowerCase().includes(q)
            ).slice(0, 5);
        } catch {
            return [];
        }
    }

    renderResults(results, query) {
        const { tenants } = results;
        const total = tenants.length;

        if (total === 0) {
            this.results.innerHTML = `
                <div class="p-6 text-center">
                    <span class="material-symbols-outlined text-slate-400 text-4xl">search_off</span>
                    <p class="text-sm font-medium text-slate-600 dark:text-slate-400 mt-2">No se encontraron resultados</p>
                    <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Intenta con otro término de búsqueda</p>
                </div>
            `;
            this.open();
            return;
        }

        let html = '';

        // Sección de tenants
        if (tenants.length > 0) {
            html += `
                <div class="px-4 py-2 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                    <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                        Tenants (${tenants.length})
                    </p>
                </div>
            `;
            
            tenants.forEach(tenant => {
                const statusColor = tenant.status === 'active' ? 'bg-emerald-500' : 
                                   tenant.status === 'suspended' ? 'bg-rose-500' : 'bg-amber-500';
                html += `
                    <a href="/admin/tenants?highlight=${tenant.subdomain}" 
                       class="search-result-item flex items-center gap-3 px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors cursor-pointer border-b border-slate-100 dark:border-slate-700/50 last:border-0">
                        <div class="size-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                            ${tenant.company_name?.charAt(0)?.toUpperCase() || 'T'}
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-slate-900 dark:text-white truncate">
                                ${this.highlight(tenant.company_name, query)}
                            </p>
                            <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
                                ${this.highlight(tenant.subdomain, query)}.sajet.us • ${tenant.email || ''}
                            </p>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="size-2 rounded-full ${statusColor}"></span>
                            <span class="text-xs text-slate-400">${tenant.plan || 'basic'}</span>
                        </div>
                    </a>
                `;
            });
        }

        // Footer con acciones
        html += `
            <div class="px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
                <p class="text-xs text-slate-500 dark:text-slate-400">
                    <kbd class="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-[10px]">↑↓</kbd> navegar
                    <kbd class="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-[10px] ml-1">Enter</kbd> seleccionar
                    <kbd class="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-[10px] ml-1">Esc</kbd> cerrar
                </p>
                <button onclick="globalSearch.close()" class="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
                    Cerrar
                </button>
            </div>
        `;

        this.results.innerHTML = html;
        this.selectedIndex = -1;
        this.open();
    }

    highlight(text, query) {
        if (!text || !query) return text || '';
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-500/30 text-inherit rounded px-0.5">$1</mark>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    open() {
        this.results.classList.remove('hidden');
        this.isOpen = true;
    }

    close() {
        this.results.classList.add('hidden');
        this.isOpen = false;
        this.selectedIndex = -1;
    }

    clear() {
        this.input.value = '';
        this.close();
        this.cache.clear();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.globalSearch = new GlobalSearch('#searchInput');
});
