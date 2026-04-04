import { redirect } from "@sveltejs/kit";
import { g as get } from "../../../chunks/index.js";
import { b as authReady, i as isAuthenticated } from "../../../chunks/darkMode.js";
import "../../../chunks/toast.js";
const ssr = false;
async function load() {
  await authReady;
  const authed = get(isAuthenticated);
  if (!authed) {
    redirect(302, "/login");
  }
}
export {
  load,
  ssr
};
