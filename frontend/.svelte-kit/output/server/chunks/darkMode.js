import { d as derived, w as writable } from "./index.js";
import { a as api } from "./client.js";
import deepmerge from "deepmerge";
import { IntlMessageFormat } from "intl-messageformat";
const dashboardApi = {
  async getMetrics() {
    return api.get("/api/dashboard/metrics");
  },
  async getAll() {
    return api.get("/api/dashboard/all");
  },
  async getOverview() {
    return api.get("/api/reports/overview");
  }
};
let _authReadyResolve;
let _authInitialized = false;
const authReady = new Promise((resolve) => {
  _authReadyResolve = resolve;
});
function createAuthStore() {
  const { subscribe, set: set2, update } = writable({
    user: null,
    isLoading: true,
    error: null
  });
  return {
    subscribe,
    init: async () => {
      try {
        const user = await api.get("/api/auth/me");
        update((state) => ({ ...state, user, isLoading: false, error: null }));
      } catch {
        update((state) => ({ ...state, user: null, isLoading: false }));
      } finally {
        if (!_authInitialized) {
          _authInitialized = true;
          _authReadyResolve();
        }
      }
    },
    login: async (usernameOrEmail, password) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const result = await api.login({ username: usernameOrEmail, password });
        if (result.requires_totp) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_totp: true };
        }
        if (result.requires_email_verify) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_email_verify: true, message: result.message };
        }
        if (result.access_token) {
          api.setToken(result.access_token);
        }
        const user = await api.get("/api/auth/me");
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Error de autenticacion";
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },
    loginWithTotp: async (usernameOrEmail, password, totpCode) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const result = await api.post("/api/auth/login", {
          email: usernameOrEmail,
          password,
          totp_code: totpCode
        });
        if (result.requires_email_verify) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_email_verify: true, message: result.message };
        }
        if (result.access_token) {
          api.setToken(result.access_token);
        }
        const user = await api.get("/api/auth/me");
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Codigo TOTP invalido";
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },
    loginWithEmailVerify: async (usernameOrEmail, password, emailVerifyCode, totpCode) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const payload = {
          email: usernameOrEmail,
          password,
          email_verify_code: emailVerifyCode
        };
        if (totpCode) payload.totp_code = totpCode;
        const result = await api.post("/api/auth/login", payload);
        if (result.access_token) {
          api.setToken(result.access_token);
        }
        const user = await api.get("/api/auth/me");
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : "Código de verificación inválido";
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },
    setError: (message) => {
      update((state) => ({ ...state, error: message }));
    },
    logout: async () => {
      await api.logout();
      set2({ user: null, isLoading: false, error: null });
    },
    clearError: () => {
      update((state) => ({ ...state, error: null }));
    }
  };
}
const auth = createAuthStore();
const isAuthenticated = derived(auth, ($auth) => !!$auth.user);
const currentUser = derived(auth, ($auth) => $auth.user);
function createDashboardStore() {
  const { subscribe, set: set2, update } = writable({
    data: null,
    report: null,
    isLoading: false,
    error: null,
    lastUpdated: null
  });
  let refreshInterval = null;
  const refreshData = async () => {
    const [data, report] = await Promise.all([
      dashboardApi.getMetrics(),
      dashboardApi.getOverview().catch(() => null)
    ]);
    update((state) => ({
      ...state,
      data,
      report: report ?? state.report,
      lastUpdated: /* @__PURE__ */ new Date()
    }));
  };
  return {
    subscribe,
    load: async () => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        await refreshData();
        update((state) => ({ ...state, isLoading: false }));
      } catch (err) {
        const message = err instanceof Error ? err.message : "No se pudo cargar el dashboard";
        update((state) => ({ ...state, error: message, isLoading: false }));
      }
    },
    refresh: async () => {
      try {
        await refreshData();
      } catch {
      }
    },
    startAutoRefresh: (intervalMs = 3e4) => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
      refreshInterval = window.setInterval(async () => {
        try {
          await refreshData();
        } catch {
        }
      }, intervalMs);
    },
    stopAutoRefresh: () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
      }
    },
    reset: () => {
      set2({
        data: null,
        report: null,
        isLoading: false,
        error: null,
        lastUpdated: null
      });
    }
  };
}
const dashboard = createDashboardStore();
function createDomainsStore() {
  const { subscribe, set: set2, update } = writable({
    items: [],
    total: 0,
    loading: false,
    error: null,
    selectedDomain: null
  });
  return {
    subscribe,
    async load(params) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const queryParams = new URLSearchParams();
        if (params?.customer_id) queryParams.set("customer_id", String(params.customer_id));
        if (params?.status) queryParams.set("status", params.status);
        if (params?.is_active !== void 0) queryParams.set("is_active", String(params.is_active));
        if (params?.limit) queryParams.set("limit", String(params.limit));
        if (params?.offset) queryParams.set("offset", String(params.offset));
        const query = queryParams.toString();
        const response = await api.get(`/api/domains${query ? `?${query}` : ""}`);
        update((s) => ({
          ...s,
          items: response.items,
          total: response.total,
          loading: false
        }));
        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error cargando dominios";
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },
    async get(domainId) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.get(`/api/domains/${domainId}`);
        update((s) => ({
          ...s,
          selectedDomain: response.domain,
          loading: false
        }));
        return response.domain;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error obteniendo dominio";
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },
    async create(data) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.post("/api/domains", data);
        if (response.success && response.domain) {
          update((s) => ({
            ...s,
            items: [response.domain, ...s.items],
            total: s.total + 1,
            loading: false
          }));
        }
        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error creando dominio";
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },
    async update(domainId, data) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.put(`/api/domains/${domainId}`, data);
        if (response.success && response.domain) {
          update((s) => ({
            ...s,
            items: s.items.map((d) => d.id === domainId ? response.domain : d),
            selectedDomain: s.selectedDomain?.id === domainId ? response.domain : s.selectedDomain,
            loading: false
          }));
        }
        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error actualizando dominio";
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },
    async delete(domainId) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.delete(`/api/domains/${domainId}`);
        if (response.success) {
          update((s) => ({
            ...s,
            items: s.items.filter((d) => d.id !== domainId),
            total: Math.max(0, s.total - 1),
            selectedDomain: s.selectedDomain?.id === domainId ? null : s.selectedDomain,
            loading: false
          }));
        }
        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error eliminando dominio";
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },
    async configureCloudflare(domainId) {
      const response = await api.post(
        `/api/domains/${domainId}/configure-cloudflare`
      );
      if (response.success) {
        await this.get(domainId);
      }
      return response;
    },
    async verify(domainId) {
      const response = await api.post(`/api/domains/${domainId}/verify`);
      update((s) => ({
        ...s,
        items: s.items.map(
          (d) => d.id === domainId ? {
            ...d,
            verification_status: response.status,
            is_active: response.success
          } : d
        )
      }));
      return response;
    },
    async activate(domainId) {
      const response = await api.post(`/api/domains/${domainId}/activate`);
      if (response.success) {
        update((s) => ({
          ...s,
          items: s.items.map((d) => d.id === domainId ? { ...d, is_active: true, verification_status: "verified" } : d)
        }));
      }
      return response;
    },
    async deactivate(domainId) {
      const response = await api.post(`/api/domains/${domainId}/deactivate`);
      if (response.success) {
        update((s) => ({
          ...s,
          items: s.items.map((d) => d.id === domainId ? { ...d, is_active: false } : d)
        }));
      }
      return response;
    },
    select(domain) {
      update((s) => ({ ...s, selectedDomain: domain }));
    },
    clearError() {
      update((s) => ({ ...s, error: null }));
    },
    reset() {
      set2({
        items: [],
        total: 0,
        loading: false,
        error: null,
        selectedDomain: null
      });
    }
  };
}
const domainsStore = createDomainsStore();
derived(domainsStore, ($store) => $store.items.filter((d) => d.is_active));
derived(
  domainsStore,
  ($store) => $store.items.filter((d) => d.verification_status === "pending")
);
const domainStats = derived(domainsStore, ($store) => ({
  total: $store.total,
  active: $store.items.filter((d) => d.is_active).length,
  pending: $store.items.filter((d) => d.verification_status === "pending").length,
  verified: $store.items.filter((d) => d.verification_status === "verified").length,
  failed: $store.items.filter((d) => d.verification_status === "failed").length
}));
function delve(obj, fullKey) {
  if (fullKey == null)
    return void 0;
  if (fullKey in obj) {
    return obj[fullKey];
  }
  const keys = fullKey.split(".");
  let result = obj;
  for (let p = 0; p < keys.length; p++) {
    if (typeof result === "object") {
      if (p > 0) {
        const partialKey = keys.slice(p, keys.length).join(".");
        if (partialKey in result) {
          result = result[partialKey];
          break;
        }
      }
      result = result[keys[p]];
    } else {
      result = void 0;
    }
  }
  return result;
}
const lookupCache = {};
const addToCache = (path, locale, message) => {
  if (!message)
    return message;
  if (!(locale in lookupCache))
    lookupCache[locale] = {};
  if (!(path in lookupCache[locale]))
    lookupCache[locale][path] = message;
  return message;
};
const lookup = (path, refLocale) => {
  if (refLocale == null)
    return void 0;
  if (refLocale in lookupCache && path in lookupCache[refLocale]) {
    return lookupCache[refLocale][path];
  }
  const locales = getPossibleLocales(refLocale);
  for (let i = 0; i < locales.length; i++) {
    const locale = locales[i];
    const message = getMessageFromDictionary(locale, path);
    if (message) {
      return addToCache(path, refLocale, message);
    }
  }
  return void 0;
};
let dictionary;
const $dictionary = writable({});
function getLocaleDictionary(locale) {
  return dictionary[locale] || null;
}
function hasLocaleDictionary(locale) {
  return locale in dictionary;
}
function getMessageFromDictionary(locale, id) {
  if (!hasLocaleDictionary(locale)) {
    return null;
  }
  const localeDictionary = getLocaleDictionary(locale);
  const match = delve(localeDictionary, id);
  return match;
}
function getClosestAvailableLocale(refLocale) {
  if (refLocale == null)
    return void 0;
  const relatedLocales = getPossibleLocales(refLocale);
  for (let i = 0; i < relatedLocales.length; i++) {
    const locale = relatedLocales[i];
    if (hasLocaleDictionary(locale)) {
      return locale;
    }
  }
  return void 0;
}
function addMessages(locale, ...partials) {
  delete lookupCache[locale];
  $dictionary.update((d) => {
    d[locale] = deepmerge.all([d[locale] || {}, ...partials]);
    return d;
  });
}
derived(
  [$dictionary],
  ([dictionary2]) => Object.keys(dictionary2)
);
$dictionary.subscribe((newDictionary) => dictionary = newDictionary);
const queue = {};
function removeLoaderFromQueue(locale, loader) {
  queue[locale].delete(loader);
  if (queue[locale].size === 0) {
    delete queue[locale];
  }
}
function getLocaleQueue(locale) {
  return queue[locale];
}
function getLocalesQueues(locale) {
  return getPossibleLocales(locale).map((localeItem) => {
    const localeQueue = getLocaleQueue(localeItem);
    return [localeItem, localeQueue ? [...localeQueue] : []];
  }).filter(([, localeQueue]) => localeQueue.length > 0);
}
function hasLocaleQueue(locale) {
  if (locale == null)
    return false;
  return getPossibleLocales(locale).some(
    (localeQueue) => {
      var _a;
      return (_a = getLocaleQueue(localeQueue)) == null ? void 0 : _a.size;
    }
  );
}
function loadLocaleQueue(locale, localeQueue) {
  const allLoadersPromise = Promise.all(
    localeQueue.map((loader) => {
      removeLoaderFromQueue(locale, loader);
      return loader().then((partial) => partial.default || partial);
    })
  );
  return allLoadersPromise.then((partials) => addMessages(locale, ...partials));
}
const activeFlushes = {};
function flush(locale) {
  if (!hasLocaleQueue(locale)) {
    if (locale in activeFlushes) {
      return activeFlushes[locale];
    }
    return Promise.resolve();
  }
  const queues = getLocalesQueues(locale);
  activeFlushes[locale] = Promise.all(
    queues.map(
      ([localeName, localeQueue]) => loadLocaleQueue(localeName, localeQueue)
    )
  ).then(() => {
    if (hasLocaleQueue(locale)) {
      return flush(locale);
    }
    delete activeFlushes[locale];
  });
  return activeFlushes[locale];
}
const defaultFormats = {
  number: {
    scientific: { notation: "scientific" },
    engineering: { notation: "engineering" },
    compactLong: { notation: "compact", compactDisplay: "long" },
    compactShort: { notation: "compact", compactDisplay: "short" }
  },
  date: {
    short: { month: "numeric", day: "numeric", year: "2-digit" },
    medium: { month: "short", day: "numeric", year: "numeric" },
    long: { month: "long", day: "numeric", year: "numeric" },
    full: { weekday: "long", month: "long", day: "numeric", year: "numeric" }
  },
  time: {
    short: { hour: "numeric", minute: "numeric" },
    medium: { hour: "numeric", minute: "numeric", second: "numeric" },
    long: {
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      timeZoneName: "short"
    },
    full: {
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      timeZoneName: "short"
    }
  }
};
const defaultOptions = {
  fallbackLocale: null,
  loadingDelay: 200,
  formats: defaultFormats,
  warnOnMissingMessages: true,
  handleMissingMessage: void 0,
  ignoreTag: true
};
const options = defaultOptions;
function getOptions() {
  return options;
}
const $isLoading = writable(false);
var __defProp$1 = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols$1 = Object.getOwnPropertySymbols;
var __hasOwnProp$1 = Object.prototype.hasOwnProperty;
var __propIsEnum$1 = Object.prototype.propertyIsEnumerable;
var __defNormalProp$1 = (obj, key, value) => key in obj ? __defProp$1(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues$1 = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp$1.call(b, prop))
      __defNormalProp$1(a, prop, b[prop]);
  if (__getOwnPropSymbols$1)
    for (var prop of __getOwnPropSymbols$1(b)) {
      if (__propIsEnum$1.call(b, prop))
        __defNormalProp$1(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
let current;
const internalLocale = writable(null);
function getSubLocales(refLocale) {
  return refLocale.split("-").map((_, i, arr) => arr.slice(0, i + 1).join("-")).reverse();
}
function getPossibleLocales(refLocale, fallbackLocale = getOptions().fallbackLocale) {
  const locales = getSubLocales(refLocale);
  if (fallbackLocale) {
    return [.../* @__PURE__ */ new Set([...locales, ...getSubLocales(fallbackLocale)])];
  }
  return locales;
}
function getCurrentLocale() {
  return current != null ? current : void 0;
}
internalLocale.subscribe((newLocale) => {
  current = newLocale != null ? newLocale : void 0;
  if (typeof window !== "undefined" && newLocale != null) {
    document.documentElement.setAttribute("lang", newLocale);
  }
});
const set = (newLocale) => {
  if (newLocale && getClosestAvailableLocale(newLocale) && hasLocaleQueue(newLocale)) {
    const { loadingDelay } = getOptions();
    let loadingTimer;
    if (typeof window !== "undefined" && getCurrentLocale() != null && loadingDelay) {
      loadingTimer = window.setTimeout(
        () => $isLoading.set(true),
        loadingDelay
      );
    } else {
      $isLoading.set(true);
    }
    return flush(newLocale).then(() => {
      internalLocale.set(newLocale);
    }).finally(() => {
      clearTimeout(loadingTimer);
      $isLoading.set(false);
    });
  }
  return internalLocale.set(newLocale);
};
const $locale = __spreadProps(__spreadValues$1({}, internalLocale), {
  set
});
const getLocaleFromNavigator = () => {
  if (typeof window === "undefined")
    return null;
  return window.navigator.language || window.navigator.languages[0];
};
const monadicMemoize = (fn) => {
  const cache = /* @__PURE__ */ Object.create(null);
  const memoizedFn = (arg) => {
    const cacheKey = JSON.stringify(arg);
    if (cacheKey in cache) {
      return cache[cacheKey];
    }
    return cache[cacheKey] = fn(arg);
  };
  return memoizedFn;
};
var __defProp = Object.defineProperty;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __objRest = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
const getIntlFormatterOptions = (type, name) => {
  const { formats } = getOptions();
  if (type in formats && name in formats[type]) {
    return formats[type][name];
  }
  throw new Error(`[svelte-i18n] Unknown "${name}" ${type} format.`);
};
const createNumberFormatter = monadicMemoize(
  (_a) => {
    var _b = _a, { locale, format } = _b, options2 = __objRest(_b, ["locale", "format"]);
    if (locale == null) {
      throw new Error('[svelte-i18n] A "locale" must be set to format numbers');
    }
    if (format) {
      options2 = getIntlFormatterOptions("number", format);
    }
    return new Intl.NumberFormat(locale, options2);
  }
);
const createDateFormatter = monadicMemoize(
  (_c) => {
    var _d = _c, { locale, format } = _d, options2 = __objRest(_d, ["locale", "format"]);
    if (locale == null) {
      throw new Error('[svelte-i18n] A "locale" must be set to format dates');
    }
    if (format) {
      options2 = getIntlFormatterOptions("date", format);
    } else if (Object.keys(options2).length === 0) {
      options2 = getIntlFormatterOptions("date", "short");
    }
    return new Intl.DateTimeFormat(locale, options2);
  }
);
const createTimeFormatter = monadicMemoize(
  (_e) => {
    var _f = _e, { locale, format } = _f, options2 = __objRest(_f, ["locale", "format"]);
    if (locale == null) {
      throw new Error(
        '[svelte-i18n] A "locale" must be set to format time values'
      );
    }
    if (format) {
      options2 = getIntlFormatterOptions("time", format);
    } else if (Object.keys(options2).length === 0) {
      options2 = getIntlFormatterOptions("time", "short");
    }
    return new Intl.DateTimeFormat(locale, options2);
  }
);
const getNumberFormatter = (_g = {}) => {
  var _h = _g, {
    locale = getCurrentLocale()
  } = _h, args = __objRest(_h, [
    "locale"
  ]);
  return createNumberFormatter(__spreadValues({ locale }, args));
};
const getDateFormatter = (_i = {}) => {
  var _j = _i, {
    locale = getCurrentLocale()
  } = _j, args = __objRest(_j, [
    "locale"
  ]);
  return createDateFormatter(__spreadValues({ locale }, args));
};
const getTimeFormatter = (_k = {}) => {
  var _l = _k, {
    locale = getCurrentLocale()
  } = _l, args = __objRest(_l, [
    "locale"
  ]);
  return createTimeFormatter(__spreadValues({ locale }, args));
};
const getMessageFormatter = monadicMemoize(
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  (message, locale = getCurrentLocale()) => new IntlMessageFormat(message, locale, getOptions().formats, {
    ignoreTag: getOptions().ignoreTag
  })
);
const formatMessage = (id, options2 = {}) => {
  var _a, _b, _c, _d;
  let messageObj = options2;
  if (typeof id === "object") {
    messageObj = id;
    id = messageObj.id;
  }
  const {
    values,
    locale = getCurrentLocale(),
    default: defaultValue
  } = messageObj;
  if (locale == null) {
    throw new Error(
      "[svelte-i18n] Cannot format a message without first setting the initial locale."
    );
  }
  let message = lookup(id, locale);
  if (!message) {
    message = (_d = (_c = (_b = (_a = getOptions()).handleMissingMessage) == null ? void 0 : _b.call(_a, { locale, id, defaultValue })) != null ? _c : defaultValue) != null ? _d : id;
  } else if (typeof message !== "string") {
    console.warn(
      `[svelte-i18n] Message with id "${id}" must be of type "string", found: "${typeof message}". Gettin its value through the "$format" method is deprecated; use the "json" method instead.`
    );
    return message;
  }
  if (!values) {
    return message;
  }
  let result = message;
  try {
    result = getMessageFormatter(message, locale).format(values);
  } catch (e) {
    if (e instanceof Error) {
      console.warn(
        `[svelte-i18n] Message "${id}" has syntax error:`,
        e.message
      );
    }
  }
  return result;
};
const formatTime = (t, options2) => {
  return getTimeFormatter(options2).format(t);
};
const formatDate = (d, options2) => {
  return getDateFormatter(options2).format(d);
};
const formatNumber = (n, options2) => {
  return getNumberFormatter(options2).format(n);
};
const getJSON = (id, locale = getCurrentLocale()) => {
  return lookup(id, locale);
};
const $format = derived([$locale, $dictionary], () => formatMessage);
derived([$locale], () => formatTime);
derived([$locale], () => formatDate);
derived([$locale], () => formatNumber);
derived([$locale, $dictionary], () => getJSON);
function createLocaleStore() {
  const { subscribe, set: set2 } = writable("en");
  return {
    subscribe,
    set: (locale) => {
      if (typeof window !== "undefined") {
        localStorage.setItem("locale", locale);
      }
      $locale.set(locale);
      set2(locale);
    },
    toggle: () => {
      let current2 = "en";
      const unsubscribe = subscribe((value) => {
        current2 = value;
      });
      unsubscribe();
      const newLocale = current2 === "en" ? "es" : "en";
      $locale.set(newLocale);
      set2(newLocale);
      if (typeof window !== "undefined") {
        localStorage.setItem("locale", newLocale);
      }
    }
  };
}
const localeStore = createLocaleStore();
const STORAGE_KEY = "sajet_dark_mode";
function readPreference() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) return saved === "true";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  } catch {
    return false;
  }
}
function applyClass(dark) {
  try {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  } catch {
  }
}
function createDarkMode() {
  const { subscribe, set: set2, update } = writable(false);
  return {
    subscribe,
    init() {
      const dark = readPreference();
      set2(dark);
      applyClass(dark);
    },
    toggle() {
      update((current2) => {
        const next = !current2;
        applyClass(next);
        try {
          localStorage.setItem(STORAGE_KEY, String(next));
        } catch {
        }
        return next;
      });
    },
    setDark(value) {
      set2(value);
      applyClass(value);
      try {
        localStorage.setItem(STORAGE_KEY, String(value));
      } catch {
      }
    }
  };
}
const darkMode = createDarkMode();
export {
  $format as $,
  auth as a,
  authReady as b,
  currentUser as c,
  dashboard as d,
  domainsStore as e,
  domainStats as f,
  getLocaleFromNavigator as g,
  darkMode as h,
  isAuthenticated as i,
  $locale as j,
  localeStore as l
};
