

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.CI3BXWXN.js","_app/immutable/chunks/B0_CwMAY.js","_app/immutable/chunks/CghEat_A.js","_app/immutable/chunks/o_LrLlzt.js","_app/immutable/chunks/CoBfGNFO.js","_app/immutable/chunks/Cjbk7AEg.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/BbzYe6Lu.js","_app/immutable/chunks/IB96V3yf.js","_app/immutable/chunks/-Y2xyFGo.js","_app/immutable/chunks/DxL-TVfg.js","_app/immutable/chunks/6jB-w2Mt.js","_app/immutable/chunks/BzoGNyBT.js","_app/immutable/chunks/CifIxeBc.js","_app/immutable/chunks/BvQ9-R2M.js","_app/immutable/chunks/CAi28Mlc.js","_app/immutable/chunks/B26qZVl3.js","_app/immutable/chunks/DxSqyA4w.js","_app/immutable/chunks/Cuf4QOiP.js","_app/immutable/chunks/ixDJpjHw.js","_app/immutable/chunks/Hucv-hWW.js","_app/immutable/chunks/w20Psy19.js","_app/immutable/chunks/BPDiRxxD.js","_app/immutable/chunks/CxQLkYDx.js","_app/immutable/chunks/QRpyFf3K.js","_app/immutable/chunks/BYg-XvhW.js","_app/immutable/chunks/Bs5MkIw-.js"];
export const stylesheets = ["_app/immutable/assets/Spinner.CINJVoiM.css","_app/immutable/assets/0.Ci2Zcjbq.css"];
export const fonts = [];
