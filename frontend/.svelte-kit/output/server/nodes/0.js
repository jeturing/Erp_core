

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.B6YWXY8z.js","_app/immutable/chunks/CMr6kB8e.js","_app/immutable/chunks/Cdb7CLZ3.js","_app/immutable/chunks/BsyhDQkw.js","_app/immutable/chunks/B_gXe2LV.js","_app/immutable/chunks/B7sJSLtT.js","_app/immutable/chunks/nsE_ZyL2.js","_app/immutable/chunks/DZH4FEPn.js","_app/immutable/chunks/BukGMgQs.js","_app/immutable/chunks/BVnmgpgR.js","_app/immutable/chunks/B26qZVl3.js","_app/immutable/chunks/V_l6fzOs.js","_app/immutable/chunks/CDKX-IT8.js","_app/immutable/chunks/ixDJpjHw.js","_app/immutable/chunks/CTlsi_M-.js","_app/immutable/chunks/1U3-xvSt.js","_app/immutable/chunks/oeZQXk1L.js","_app/immutable/chunks/Cqvy47ul.js","_app/immutable/chunks/CvP5SqjB.js","_app/immutable/chunks/HQkmSzia.js","_app/immutable/chunks/Cl4oOEoP.js","_app/immutable/chunks/BVmHtMrx.js","_app/immutable/chunks/sWoF3895.js","_app/immutable/chunks/CoBfGNFO.js","_app/immutable/chunks/BmTRDpZN.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/CXc-U5-s.js"];
export const stylesheets = ["_app/immutable/assets/Spinner.CINJVoiM.css","_app/immutable/assets/0.DivqMZb0.css"];
export const fonts = [];
