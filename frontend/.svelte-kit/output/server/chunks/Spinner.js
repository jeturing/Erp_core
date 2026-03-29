import { k as attr_class, l as clsx, p as bind_props, b as stringify } from "./index2.js";
import { a8 as fallback } from "./utils2.js";
function Spinner($$renderer, $$props) {
  let size = fallback($$props["size"], "md");
  let center = fallback($$props["center"], true);
  const sizeClasses = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" };
  $$renderer.push(`<div${attr_class(clsx(center ? "flex items-center justify-center" : ""))}><svg${attr_class(`animate-spin ${stringify(sizeClasses[size])} text-primary-500`)} viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>`);
  bind_props($$props, { size, center });
}
export {
  Spinner as S
};
