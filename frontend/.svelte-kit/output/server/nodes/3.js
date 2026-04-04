

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(portal)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(portal)/+layout.ts";
export const imports = ["_app/immutable/nodes/3.B_iO-9xT.js","_app/immutable/chunks/hp4PFHFv.js","_app/immutable/chunks/BUApaBEI.js","_app/immutable/chunks/DvT3a-yk.js","_app/immutable/chunks/1CMrBNY0.js","_app/immutable/chunks/CQ_MvSdQ.js","_app/immutable/chunks/CoBfGNFO.js","_app/immutable/chunks/KuCOPjgL.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/B2YKRsUz.js","_app/immutable/chunks/C7OHRjE9.js","_app/immutable/chunks/CME_gfcK.js","_app/immutable/chunks/SJhR3enE.js"];
export const stylesheets = [];
export const fonts = [];
