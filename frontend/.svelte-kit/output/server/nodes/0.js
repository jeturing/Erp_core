

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "prerender": false,
  "load": null
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.DUwV4Wv2.js","_app/immutable/chunks/DoiHRS6C.js","_app/immutable/chunks/B_gHqzB-.js","_app/immutable/chunks/DuWWigTJ.js","_app/immutable/chunks/CoBfGNFO.js","_app/immutable/chunks/DDc_ZsX7.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/Cel9aHPQ.js","_app/immutable/chunks/DQiEKq5i.js","_app/immutable/chunks/Do5B4ou-.js","_app/immutable/chunks/DuwbnCK8.js","_app/immutable/chunks/Au2gfsmC.js","_app/immutable/chunks/C44dcGQ9.js","_app/immutable/chunks/-SC1U9EO.js","_app/immutable/chunks/GISHIjFi.js","_app/immutable/chunks/DWNdrKHs.js","_app/immutable/chunks/BFgis2yR.js","_app/immutable/chunks/B7YGyOTP.js","_app/immutable/chunks/ixDJpjHw.js","_app/immutable/chunks/D8NF_Zdb.js","_app/immutable/chunks/RpkTUpfy.js","_app/immutable/chunks/zLZgLFC2.js","_app/immutable/chunks/Cduyk_Qq.js","_app/immutable/chunks/B7uMneuC.js","_app/immutable/chunks/xO0jFlEd.js","_app/immutable/chunks/BG3OV5kx.js"];
export const stylesheets = ["_app/immutable/assets/Spinner.CINJVoiM.css","_app/immutable/assets/0.BbrC4nMj.css"];
export const fonts = [];
