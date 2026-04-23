

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(public)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(public)/+layout.ts";
export const imports = ["_app/immutable/nodes/4.CjHCd1p1.js","_app/immutable/chunks/B-6i1c7b.js","_app/immutable/chunks/Cd1PIuZZ.js","_app/immutable/chunks/BrAPmWx5.js","_app/immutable/chunks/BsDZnmIP.js"];
export const stylesheets = [];
export const fonts = [];
