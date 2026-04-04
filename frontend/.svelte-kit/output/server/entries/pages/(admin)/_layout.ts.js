import { redirect } from "@sveltejs/kit";
import { g as get } from "../../../chunks/index.js";
import { b as authReady, i as isAuthenticated, c as currentUser } from "../../../chunks/darkMode.js";
import "../../../chunks/toast.js";
const ssr = false;
async function load() {
  await authReady;
  const authed = get(isAuthenticated);
  const user = get(currentUser);
  if (!authed) {
    redirect(302, "/login");
  }
  if (user?.role === "tenant") {
    redirect(302, "/portal");
  }
  if (user?.role === "partner") {
    redirect(302, "/partner-portal");
  }
}
export {
  load,
  ssr
};
