

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(public)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(public)/+layout.ts";
export const imports = ["_app/immutable/nodes/4.DZXKI2dO.js","_app/immutable/chunks/Do5B4ou-.js","_app/immutable/chunks/DuWWigTJ.js","_app/immutable/chunks/DuwbnCK8.js","_app/immutable/chunks/Au2gfsmC.js"];
export const stylesheets = [];
export const fonts = [];
