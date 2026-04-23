

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(portal)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(portal)/+layout.ts";
export const imports = ["_app/immutable/nodes/3.C5pYHNq1.js","_app/immutable/chunks/hp4PFHFv.js","_app/immutable/chunks/BUApaBEI.js","_app/immutable/chunks/B8PiG4Jo.js","_app/immutable/chunks/Cd1PIuZZ.js","_app/immutable/chunks/C-hHWX6z.js","_app/immutable/chunks/rdIrDFrD.js","_app/immutable/chunks/p9HdTgwj.js","_app/immutable/chunks/DMDWgDVq.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/CJ-aSdha.js","_app/immutable/chunks/B-6i1c7b.js","_app/immutable/chunks/BrAPmWx5.js","_app/immutable/chunks/BsDZnmIP.js"];
export const stylesheets = [];
export const fonts = [];
