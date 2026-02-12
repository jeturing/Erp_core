/**
 * Toast Notification System
 * Sistema de notificaciones elegante para reemplazar alert()
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Crear contenedor si no existe
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed top-4 right-4 z-[9999] flex flex-col gap-3 pointer-events-none';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    /**
     * Mostrar toast
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo: success, error, warning, info
     * @param {number} duration - Duración en ms (default 4000)
     * @param {object} options - Opciones adicionales {title, action, actionText}
     */
    show(message, type = 'info', duration = 4000, options = {}) {
        const toast = document.createElement('div');
        const id = `toast-${Date.now()}`;
        toast.id = id;
        
        // Configuración por tipo
        const config = {
            success: {
                icon: 'check_circle',
                bg: 'bg-emerald-500/95',
                border: 'border-emerald-400/50',
                iconColor: 'text-white',
                shadow: 'shadow-emerald-500/30'
            },
            error: {
                icon: 'error',
                bg: 'bg-rose-500/95',
                border: 'border-rose-400/50',
                iconColor: 'text-white',
                shadow: 'shadow-rose-500/30'
            },
            warning: {
                icon: 'warning',
                bg: 'bg-amber-500/95',
                border: 'border-amber-400/50',
                iconColor: 'text-white',
                shadow: 'shadow-amber-500/30'
            },
            info: {
                icon: 'info',
                bg: 'bg-blue-500/95',
                border: 'border-blue-400/50',
                iconColor: 'text-white',
                shadow: 'shadow-blue-500/30'
            }
        };

        const cfg = config[type] || config.info;
        const title = options.title || this.getDefaultTitle(type);

        toast.className = `
            pointer-events-auto max-w-sm w-full ${cfg.bg} ${cfg.border} border
            backdrop-blur-xl rounded-2xl shadow-2xl ${cfg.shadow}
            transform translate-x-full opacity-0 transition-all duration-300 ease-out
        `;

        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start gap-3">
                    <span class="material-symbols-outlined ${cfg.iconColor} text-[24px] flex-shrink-0 mt-0.5">${cfg.icon}</span>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-semibold text-white">${title}</p>
                        <p class="text-sm text-white/90 mt-0.5">${message}</p>
                        ${options.action ? `
                            <button onclick="${options.action}" class="mt-2 text-sm font-semibold text-white/80 hover:text-white underline underline-offset-2">
                                ${options.actionText || 'Ver más'}
                            </button>
                        ` : ''}
                    </div>
                    <button onclick="toast.dismiss('${id}')" class="flex-shrink-0 text-white/60 hover:text-white transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>
            </div>
            <div class="toast-progress h-1 ${cfg.bg.replace('/95', '')} rounded-b-2xl opacity-60">
                <div class="h-full bg-white/40 rounded-b-2xl transition-all ease-linear" style="width: 100%; transition-duration: ${duration}ms;"></div>
            </div>
        `;

        this.container.appendChild(toast);

        // Animar entrada
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
            
            // Iniciar progreso
            const progressBar = toast.querySelector('.toast-progress > div');
            if (progressBar) {
                requestAnimationFrame(() => {
                    progressBar.style.width = '0%';
                });
            }
        });

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }

        return id;
    }

    dismiss(id) {
        const toast = document.getElementById(id);
        if (!toast) return;

        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }

    getDefaultTitle(type) {
        const titles = {
            success: '¡Éxito!',
            error: 'Error',
            warning: 'Advertencia',
            info: 'Información'
        };
        return titles[type] || 'Notificación';
    }

    // Métodos de conveniencia
    success(message, options = {}) {
        return this.show(message, 'success', options.duration || 4000, options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', options.duration || 6000, options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options.duration || 5000, options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options.duration || 4000, options);
    }

    // Toast de carga (no se auto-cierra)
    loading(message, options = {}) {
        const toast = document.createElement('div');
        const id = `toast-loading-${Date.now()}`;
        toast.id = id;

        toast.className = `
            pointer-events-auto max-w-sm w-full bg-slate-800/95 border border-slate-600/50
            backdrop-blur-xl rounded-2xl shadow-2xl shadow-slate-900/30
            transform translate-x-full opacity-0 transition-all duration-300 ease-out
        `;

        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-center gap-3">
                    <div class="flex-shrink-0">
                        <svg class="animate-spin h-5 w-5 text-cyan-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-white">${options.title || 'Procesando...'}</p>
                        <p class="text-sm text-slate-300 mt-0.5">${message}</p>
                    </div>
                </div>
            </div>
        `;

        this.container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        });

        return id;
    }

    // Actualizar toast de carga a éxito/error
    update(id, message, type = 'success', options = {}) {
        this.dismiss(id);
        return this.show(message, type, options.duration || 4000, options);
    }
}

// Instancia global
const toast = new ToastManager();

// Compatibilidad con código existente - reemplazar alert
window.showToast = (message, type = 'info') => toast.show(message, type);
window.showSuccess = (message) => toast.success(message);
window.showError = (message) => toast.error(message);
window.showWarning = (message) => toast.warning(message);
window.showInfo = (message) => toast.info(message);
