

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(public)/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/(public)/+layout.ts";
export const imports = ["_app/immutable/nodes/4.Dsck2WxA.js","_app/immutable/chunks/-Y2xyFGo.js","_app/immutable/chunks/o_LrLlzt.js","_app/immutable/chunks/DxL-TVfg.js","_app/immutable/chunks/6jB-w2Mt.js"];
export const stylesheets = [];
export const fonts = [];
