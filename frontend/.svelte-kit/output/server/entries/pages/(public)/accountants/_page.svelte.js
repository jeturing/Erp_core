import "clsx";
import { e as ensure_array_like, d as escape_html, k as attr_class, b as stringify } from "../../../../chunks/index2.js";
import { N as NavBar, F as Footer } from "../../../../chunks/Footer.js";
import { A as Arrow_right } from "../../../../chunks/arrow-right.js";
import { P as Play } from "../../../../chunks/play.js";
import { C as Check } from "../../../../chunks/check.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { C as Chevron_up } from "../../../../chunks/chevron-up.js";
import { C as Chevron_down } from "../../../../chunks/chevron-down.js";
import { E as Eye, C as Chart_column } from "../../../../chunks/eye.js";
import { C as Calculator } from "../../../../chunks/calculator.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { S as Shield_check } from "../../../../chunks/shield-check.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
function AccountantsLanding($$renderer) {
  let openFaq = null;
  const painPoints = [
    {
      before: "Logging into 6 different client portals every morning",
      after: "One dashboard for every client — real-time financials, single sign-on"
    },
    {
      before: "Month-end scramble: exporting CSVs, copy-pasting, reconciling",
      after: "Automated consolidation, bank-feed sync, one-click trial balance"
    },
    {
      before: "Clients call you for invoice status — you don't know either",
      after: "Live AR/AP visibility + client self-service portal"
    }
  ];
  const capabilities = [
    {
      icon: Eye,
      title: "Multi-Client Dashboard",
      desc: "See all your client companies in one view. Switch between tenants instantly."
    },
    {
      icon: Calculator,
      title: "Automated Reconciliation",
      desc: "Bank feeds, invoice matching, and journal entries — connected and automated."
    },
    {
      icon: Chart_column,
      title: "Consolidated Reporting",
      desc: "Cross-client P&L, balance sheets, and cash flow — export-ready for tax season."
    },
    {
      icon: File_text,
      title: "Document Management",
      desc: "Receipts, invoices, contracts — uploaded by clients, organized by you."
    },
    {
      icon: Shield_check,
      title: "Role-Based Access",
      desc: "Read-only, read-write, or full access — per client, per team member."
    },
    {
      icon: Refresh_cw,
      title: "Real-Time Sync",
      desc: "Every transaction updates instantly across modules. No batch processing delays."
    }
  ];
  const partnerTiers = [
    {
      name: "Referral Partner",
      price: "Free",
      desc: "Send clients our way and earn commissions — no platform management required.",
      features: [
        "Referral tracking link",
        "Commission on subscriptions",
        "Partner badge for your site"
      ]
    },
    {
      name: "Managed Partner",
      price: "From $0/mo",
      desc: "Full access to manage your clients' Sajet environments. White-label available.",
      features: [
        "Multi-client dashboard",
        "White-label branding",
        "Priority support channel",
        "Co-branded onboarding",
        "Revenue share model"
      ],
      highlighted: true
    },
    {
      name: "Enterprise Partner",
      price: "Custom",
      desc: "For large accounting firms needing dedicated infrastructure and SLAs.",
      features: [
        "Everything in Managed",
        "Dedicated CSM",
        "Custom SLA",
        "API integrations",
        "Bulk pricing"
      ]
    }
  ];
  const faqs = [
    {
      q: "Is there a cost for accountants to use Sajet?",
      a: "Referral partners pay nothing. Managed and Enterprise partners may have optional add-ons, but the core dashboard is included when your clients subscribe to Sajet."
    },
    {
      q: "Can I migrate my clients from QuickBooks / Xero?",
      a: "Yes. We provide assisted migration tools and data import wizards. Our onboarding team can help with complex migrations at no extra cost for Managed partners."
    },
    {
      q: "What if a client cancels?",
      a: "You retain dashboard access to their historical data for 90 days. Commissions adjust automatically. No penalties for you."
    },
    {
      q: "Do I need technical skills?",
      a: "Not at all. The accountant dashboard is designed for finance professionals, not developers. Everything is point-and-click."
    },
    {
      q: "Can my team members access the dashboard too?",
      a: "Absolutely. You can invite team members with role-based permissions (read-only, read-write, full) per client."
    }
  ];
  $$renderer.push(`<div class="min-h-screen bg-white font-inter">`);
  NavBar($$renderer, {});
  $$renderer.push(`<!----> <section class="bg-gradient-hero pt-32 pb-24"><div class="max-w-4xl mx-auto px-6 text-center"><span class="inline-flex items-center gap-2 rounded-full bg-white/15 text-white text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-6">For Accountants &amp; CPAs</span> <h1 class="text-5xl md:text-6xl font-jakarta font-extrabold text-white leading-tight mb-6">Manage every client.<br/> From one place.</h1> <p class="text-lg font-inter text-white/80 max-w-2xl mx-auto mb-10">Sajet gives accounting professionals a single dashboard to oversee all client companies — financials, documents, and reporting — without juggling multiple logins.</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-4"><a href="/signup?mode=accountant" class="inline-flex items-center gap-2 bg-white text-primary font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn shadow-medium hover:shadow-elevated hover:bg-cloud transition-all">Start Your Free Trial `);
  Arrow_right($$renderer, { class: "w-4 h-4" });
  $$renderer.push(`<!----></a> <a href="mailto:ventas@sajet.us?subject=Solicitar%20demo%20Sajet%20para%20contadores" class="inline-flex items-center gap-2 border border-white/40 text-white font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn hover:bg-white/10 transition-all">`);
  Play($$renderer, { class: "w-4 h-4" });
  $$renderer.push(`<!----> Watch the demo</a></div></div></section> <section class="bg-white py-24"><div class="max-w-5xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-red-50 text-red-600 text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">Sound Familiar?</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark">The old way vs. the Sajet way</h2></div> <div class="space-y-4"><!--[-->`);
  const each_array = ensure_array_like(painPoints);
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let point = each_array[$$index];
    $$renderer.push(`<div class="grid grid-cols-1 md:grid-cols-2 gap-4"><div class="rounded-card-sm border border-red-100 bg-red-50/50 p-5"><p class="text-sm font-inter text-red-700 flex items-start gap-2"><span class="text-red-400 mt-0.5">✗</span> ${escape_html(point.before)}</p></div> <div class="rounded-card-sm border border-emerald-100 bg-emerald-50/50 p-5"><p class="text-sm font-inter text-emerald-700 flex items-start gap-2">`);
    Check($$renderer, {
      class: "w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0",
      strokeWidth: 2.5
    });
    $$renderer.push(`<!----> ${escape_html(point.after)}</p></div></div>`);
  }
  $$renderer.push(`<!--]--></div></div></section> <section class="bg-gradient-subtle py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">Built for Finance Professionals</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">Everything you need to serve<br/> clients efficiently.</h2></div> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"><!--[-->`);
  const each_array_1 = ensure_array_like(capabilities);
  for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
    let cap = each_array_1[$$index_1];
    $$renderer.push(`<div class="rounded-card-sm border border-border bg-white p-6 hover:shadow-medium hover:border-primary/20 transition-all group"><div class="w-10 h-10 rounded-lg bg-primary-light flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">`);
    if (cap.icon) {
      $$renderer.push("<!--[-->");
      cap.icon($$renderer, { class: "w-5 h-5 text-primary", strokeWidth: 1.5 });
      $$renderer.push("<!--]-->");
    } else {
      $$renderer.push("<!--[!-->");
      $$renderer.push("<!--]-->");
    }
    $$renderer.push(`</div> <h3 class="text-base font-jakarta font-semibold text-slate-dark mb-2">${escape_html(cap.title)}</h3> <p class="text-sm font-inter text-slate leading-relaxed">${escape_html(cap.desc)}</p></div>`);
  }
  $$renderer.push(`<!--]--></div></div></section> <section class="bg-white py-24"><div class="max-w-6xl mx-auto px-6"><div class="text-center mb-14"><span class="inline-flex items-center gap-2 rounded-full bg-primary-light text-primary text-[13px] font-inter font-medium tracking-[0.08em] uppercase px-4 py-1.5 mb-4">Partnership Model</span> <h2 class="text-4xl font-jakarta font-bold text-slate-dark mb-4">Choose how you want to work with us.</h2></div> <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start"><!--[-->`);
  const each_array_2 = ensure_array_like(partnerTiers);
  for (let $$index_3 = 0, $$length = each_array_2.length; $$index_3 < $$length; $$index_3++) {
    let tier = each_array_2[$$index_3];
    $$renderer.push(`<div${attr_class(`relative rounded-card-lg border bg-white p-6 flex flex-col ${stringify(tier.highlighted ? "border-primary shadow-elevated ring-2 ring-primary/20" : "border-border shadow-soft")}`)}>`);
    if (tier.highlighted) {
      $$renderer.push("<!--[-->");
      $$renderer.push(`<div class="absolute -top-3 left-1/2 -translate-x-1/2"><span class="inline-flex items-center gap-1 bg-primary text-white text-xs font-inter font-semibold px-3 py-1 rounded-full shadow-md">`);
      Zap($$renderer, { class: "w-3 h-3" });
      $$renderer.push(`<!----> Most Popular</span></div>`);
    } else {
      $$renderer.push("<!--[!-->");
    }
    $$renderer.push(`<!--]--> <h3 class="text-lg font-jakarta font-bold text-slate-dark mb-1">${escape_html(tier.name)}</h3> <p class="text-2xl font-jakarta font-extrabold text-slate-dark mb-2">${escape_html(tier.price)}</p> <p class="text-sm font-inter text-slate mb-4">${escape_html(tier.desc)}</p> <ul class="space-y-2 mb-6 flex-1"><!--[-->`);
    const each_array_3 = ensure_array_like(tier.features);
    for (let $$index_2 = 0, $$length2 = each_array_3.length; $$index_2 < $$length2; $$index_2++) {
      let feat = each_array_3[$$index_2];
      $$renderer.push(`<li class="flex items-start gap-2 text-sm font-inter text-slate-dark">`);
      Check($$renderer, {
        class: "w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5",
        strokeWidth: 2.5
      });
      $$renderer.push(`<!----> <span>${escape_html(feat)}</span></li>`);
    }
    $$renderer.push(`<!--]--></ul> <a href="/signup?mode=accountant"${attr_class(`w-full text-center text-sm font-jakarta font-semibold py-2.5 rounded-btn transition-all block ${stringify(tier.highlighted ? "bg-primary hover:bg-navy text-white shadow-soft hover:shadow-medium" : "border border-primary text-primary hover:bg-primary hover:text-white")}`)}>Get Started</a></div>`);
  }
  $$renderer.push(`<!--]--></div></div></section> <section class="bg-gradient-subtle py-24"><div class="max-w-3xl mx-auto px-6"><div class="text-center mb-14"><h2 class="text-4xl font-jakarta font-bold text-slate-dark">Frequently Asked Questions</h2></div> <div class="space-y-3"><!--[-->`);
  const each_array_4 = ensure_array_like(faqs);
  for (let i = 0, $$length = each_array_4.length; i < $$length; i++) {
    let faq = each_array_4[i];
    $$renderer.push(`<div class="rounded-card-sm border border-border bg-white overflow-hidden"><button class="w-full flex items-center justify-between p-5 text-left"><span class="text-sm font-jakarta font-semibold text-slate-dark pr-4">${escape_html(faq.q)}</span> `);
    if (openFaq === i) {
      $$renderer.push("<!--[-->");
      Chevron_up($$renderer, { class: "w-4 h-4 text-slate flex-shrink-0" });
    } else {
      $$renderer.push("<!--[!-->");
      Chevron_down($$renderer, { class: "w-4 h-4 text-slate flex-shrink-0" });
    }
    $$renderer.push(`<!--]--></button> `);
    if (openFaq === i) {
      $$renderer.push("<!--[-->");
      $$renderer.push(`<div class="px-5 pb-5 -mt-1"><p class="text-sm font-inter text-slate leading-relaxed">${escape_html(faq.a)}</p></div>`);
    } else {
      $$renderer.push("<!--[!-->");
    }
    $$renderer.push(`<!--]--></div>`);
  }
  $$renderer.push(`<!--]--></div></div></section> <section class="bg-gradient-hero py-24"><div class="max-w-3xl mx-auto px-6 text-center"><h2 class="text-4xl md:text-5xl font-jakarta font-extrabold text-white mb-6 leading-tight">Ready to simplify how you<br/> serve your clients?</h2> <p class="text-lg font-inter text-white/80 mb-10 max-w-xl mx-auto">Join accounting firms that manage all their clients from one platform. 14-day free trial, no credit card required.</p> <div class="flex flex-col sm:flex-row items-center justify-center gap-4"><a href="/signup?mode=accountant" class="inline-flex items-center gap-2 bg-white text-primary font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn shadow-medium hover:shadow-elevated hover:bg-cloud transition-all">Start Free Trial `);
  Arrow_right($$renderer, { class: "w-4 h-4" });
  $$renderer.push(`<!----></a> <a href="mailto:ventas@sajet.us?subject=Solicitar%20walkthrough%20Sajet%20para%20contadores" class="inline-flex items-center gap-2 border border-white/40 text-white font-jakarta font-semibold text-sm px-8 py-3.5 rounded-btn hover:bg-white/10 transition-all">Book a walkthrough</a></div></div></section> `);
  Footer($$renderer);
  $$renderer.push(`<!----></div>`);
}
function _page($$renderer) {
  AccountantsLanding($$renderer);
}
export {
  _page as default
};
