

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(public)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false
};
export const universal_id = "src/routes/(public)/+layout.ts";
export const imports = ["_app/immutable/nodes/4.B-EOCi32.js","_app/immutable/chunks/CMr6kB8e.js","_app/immutable/chunks/Cdb7CLZ3.js","_app/immutable/chunks/nsE_ZyL2.js","_app/immutable/chunks/B7sJSLtT.js"];
export const stylesheets = [];
export const fonts = [];
