import { g as getLocaleFromNavigator, l as localeStore, a as auth } from "../../chunks/darkMode.js";
import "../../chunks/toast.js";
function getInitialLocale() {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("locale");
    if (saved && ["en", "es"].includes(saved)) {
      return saved;
    }
    const navigatorLang = getLocaleFromNavigator();
    if (navigatorLang?.startsWith("es")) {
      return "es";
    }
  }
  return "en";
}
const ssr = false;
const prerender = false;
async function load() {
  if (typeof window !== "undefined") {
    const initialLocale = getInitialLocale();
    localeStore.set(initialLocale);
    await auth.init();
  }
}
export {
  load,
  prerender,
  ssr
};
