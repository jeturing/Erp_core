import { writable } from 'svelte/store';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
  duration: number;
}

function createToastStore() {
  const { subscribe, update, set } = writable<ToastItem[]>([]);
  let nextId = 1;

  function removeToast(id: number) {
    update((items) => items.filter((item) => item.id !== id));
  }

  function addToast(message: string, variant: ToastVariant = 'info', duration = 3500) {
    const id = nextId++;
    const toast: ToastItem = { id, message, variant, duration };

    update((items) => [...items, toast]);

    if (duration > 0) {
      window.setTimeout(() => removeToast(id), duration);
    }

    return id;
  }

  return {
    subscribe,
    addToast,
    removeToast,
    clear: () => set([]),
  };
}

export const toast = createToastStore();
export const addToast = toast.addToast;
export const removeToast = toast.removeToast;
