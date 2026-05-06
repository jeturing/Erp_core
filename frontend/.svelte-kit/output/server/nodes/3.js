

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(portal)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(portal)/+layout.ts";
export const imports = ["_app/immutable/nodes/3.DWi8OTpU.js","_app/immutable/chunks/hp4PFHFv.js","_app/immutable/chunks/BUApaBEI.js","_app/immutable/chunks/B8PiG4Jo.js","_app/immutable/chunks/Cd1PIuZZ.js","_app/immutable/chunks/DV7c0Axe.js","_app/immutable/chunks/7NXRvnOD.js","_app/immutable/chunks/B48B7wKa.js","_app/immutable/chunks/DMDWgDVq.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/CJ-aSdha.js","_app/immutable/chunks/B-6i1c7b.js","_app/immutable/chunks/BrAPmWx5.js","_app/immutable/chunks/BsDZnmIP.js"];
export const stylesheets = [];
export const fonts = [];
