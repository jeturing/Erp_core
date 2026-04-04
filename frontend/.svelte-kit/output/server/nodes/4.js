

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(public)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(public)/+layout.ts";
export const imports = ["_app/immutable/nodes/4.CIU1ZIJy.js","_app/immutable/chunks/C7OHRjE9.js","_app/immutable/chunks/1CMrBNY0.js","_app/immutable/chunks/CME_gfcK.js","_app/immutable/chunks/SJhR3enE.js"];
export const stylesheets = [];
export const fonts = [];
