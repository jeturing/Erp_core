import { w as writable } from "./index.js";
function createToastStore() {
  const { subscribe, update } = writable([]);
  function addToast(message, variant = "info", duration = 5e3) {
    const id = Math.random().toString(36).slice(2, 9);
    const toast = { id, message, variant, duration };
    update((toasts2) => [...toasts2, toast]);
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration);
    }
    return id;
  }
  function removeToast(id) {
    update((toasts2) => toasts2.filter((t) => t.id !== id));
  }
  return {
    subscribe,
    success: (message, duration) => addToast(message, "success", duration),
    error: (message, duration) => addToast(message, "error", duration ?? 8e3),
    warning: (message, duration) => addToast(message, "warning", duration),
    info: (message, duration) => addToast(message, "info", duration),
    remove: removeToast
  };
}
const toasts = createToastStore();
export {
  toasts as t
};
