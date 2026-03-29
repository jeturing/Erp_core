import { redirect } from "@sveltejs/kit";
import { g as get } from "../../../chunks/index.js";
import { i as isAuthenticated } from "../../../chunks/darkMode.js";
import "../../../chunks/toast.js";
const ssr = false;
function load() {
  const authed = get(isAuthenticated);
  if (!authed) {
    redirect(302, "/login");
  }
}
export {
  load,
  ssr
};
