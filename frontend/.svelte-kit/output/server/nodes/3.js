

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(portal)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(portal)/+layout.ts";
export const imports = ["_app/immutable/nodes/3.DKDeTC5V.js","_app/immutable/chunks/hp4PFHFv.js","_app/immutable/chunks/BUApaBEI.js","_app/immutable/chunks/B_gHqzB-.js","_app/immutable/chunks/DuWWigTJ.js","_app/immutable/chunks/DoiHRS6C.js","_app/immutable/chunks/CoBfGNFO.js","_app/immutable/chunks/DDc_ZsX7.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/Cel9aHPQ.js","_app/immutable/chunks/Do5B4ou-.js","_app/immutable/chunks/DuwbnCK8.js","_app/immutable/chunks/Au2gfsmC.js"];
export const stylesheets = [];
export const fonts = [];
