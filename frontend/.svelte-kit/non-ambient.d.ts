
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	type MatcherParam<M> = M extends (param : string) => param is (infer U extends string) ? U : string;

	export interface AppTypes {
		RouteId(): "/(public)" | "/(portal)" | "/(admin)" | "/" | "/(public)/about" | "/(portal)/accountant-portal" | "/(public)/accountants" | "/(admin)/admin-users" | "/admin" | "/admin/components" | "/(admin)/agreements" | "/(admin)/audit" | "/(admin)/billing" | "/(admin)/blueprints" | "/(admin)/branding" | "/(admin)/catalog" | "/(admin)/clients" | "/(admin)/commissions" | "/(admin)/communications" | "/(portal)/customer-onboarding" | "/(admin)/dashboard" | "/(public)/data-processing" | "/(admin)/dispersion" | "/(admin)/domains" | "/(admin)/infrastructure" | "/(admin)/invoices" | "/(admin)/landing-sections" | "/(admin)/leads" | "/(public)/login" | "/(admin)/logs" | "/(admin)/migrations" | "/(admin)/neural-users" | "/(public)/onboarding-access" | "/(admin)/onboarding-config" | "/(portal)/partner-portal" | "/(public)/partner-signup" | "/(admin)/partners" | "/(admin)/plan-governance" | "/(admin)/plans" | "/(public)/plt" | "/(public)/plt/[slug]" | "/(portal)/portal" | "/(public)/pricing" | "/(public)/privacy" | "/(admin)/quotations" | "/(admin)/reconciliation" | "/(public)/recover-account" | "/(admin)/reports" | "/(admin)/roles" | "/(admin)/seats" | "/(public)/security" | "/(public)/servicios" | "/(admin)/session-monitoring" | "/(admin)/settings" | "/(admin)/settlements" | "/(public)/signup" | "/(public)/sla" | "/(admin)/tenants" | "/(public)/terms" | "/(admin)/testimonials" | "/(admin)/translations" | "/(admin)/tunnels" | "/(admin)/workorders";
		RouteParams(): {
			"/(public)/plt/[slug]": { slug: string }
		};
		LayoutParams(): {
			"/(public)": { slug?: string };
			"/(portal)": Record<string, never>;
			"/(admin)": Record<string, never>;
			"/": { slug?: string };
			"/(public)/about": Record<string, never>;
			"/(portal)/accountant-portal": Record<string, never>;
			"/(public)/accountants": Record<string, never>;
			"/(admin)/admin-users": Record<string, never>;
			"/admin": Record<string, never>;
			"/admin/components": Record<string, never>;
			"/(admin)/agreements": Record<string, never>;
			"/(admin)/audit": Record<string, never>;
			"/(admin)/billing": Record<string, never>;
			"/(admin)/blueprints": Record<string, never>;
			"/(admin)/branding": Record<string, never>;
			"/(admin)/catalog": Record<string, never>;
			"/(admin)/clients": Record<string, never>;
			"/(admin)/commissions": Record<string, never>;
			"/(admin)/communications": Record<string, never>;
			"/(portal)/customer-onboarding": Record<string, never>;
			"/(admin)/dashboard": Record<string, never>;
			"/(public)/data-processing": Record<string, never>;
			"/(admin)/dispersion": Record<string, never>;
			"/(admin)/domains": Record<string, never>;
			"/(admin)/infrastructure": Record<string, never>;
			"/(admin)/invoices": Record<string, never>;
			"/(admin)/landing-sections": Record<string, never>;
			"/(admin)/leads": Record<string, never>;
			"/(public)/login": Record<string, never>;
			"/(admin)/logs": Record<string, never>;
			"/(admin)/migrations": Record<string, never>;
			"/(admin)/neural-users": Record<string, never>;
			"/(public)/onboarding-access": Record<string, never>;
			"/(admin)/onboarding-config": Record<string, never>;
			"/(portal)/partner-portal": Record<string, never>;
			"/(public)/partner-signup": Record<string, never>;
			"/(admin)/partners": Record<string, never>;
			"/(admin)/plan-governance": Record<string, never>;
			"/(admin)/plans": Record<string, never>;
			"/(public)/plt": { slug?: string };
			"/(public)/plt/[slug]": { slug: string };
			"/(portal)/portal": Record<string, never>;
			"/(public)/pricing": Record<string, never>;
			"/(public)/privacy": Record<string, never>;
			"/(admin)/quotations": Record<string, never>;
			"/(admin)/reconciliation": Record<string, never>;
			"/(public)/recover-account": Record<string, never>;
			"/(admin)/reports": Record<string, never>;
			"/(admin)/roles": Record<string, never>;
			"/(admin)/seats": Record<string, never>;
			"/(public)/security": Record<string, never>;
			"/(public)/servicios": Record<string, never>;
			"/(admin)/session-monitoring": Record<string, never>;
			"/(admin)/settings": Record<string, never>;
			"/(admin)/settlements": Record<string, never>;
			"/(public)/signup": Record<string, never>;
			"/(public)/sla": Record<string, never>;
			"/(admin)/tenants": Record<string, never>;
			"/(public)/terms": Record<string, never>;
			"/(admin)/testimonials": Record<string, never>;
			"/(admin)/translations": Record<string, never>;
			"/(admin)/tunnels": Record<string, never>;
			"/(admin)/workorders": Record<string, never>
		};
		Pathname(): "/" | "/about" | "/accountant-portal" | "/accountants" | "/admin-users" | "/admin" | "/agreements" | "/audit" | "/billing" | "/blueprints" | "/branding" | "/catalog" | "/clients" | "/commissions" | "/communications" | "/customer-onboarding" | "/dashboard" | "/data-processing" | "/dispersion" | "/domains" | "/infrastructure" | "/invoices" | "/landing-sections" | "/leads" | "/login" | "/logs" | "/migrations" | "/neural-users" | "/onboarding-access" | "/onboarding-config" | "/partner-portal" | "/partner-signup" | "/partners" | "/plan-governance" | "/plans" | `/plt/${string}` & {} | "/portal" | "/pricing" | "/privacy" | "/quotations" | "/reconciliation" | "/recover-account" | "/reports" | "/roles" | "/seats" | "/security" | "/servicios" | "/session-monitoring" | "/settings" | "/settlements" | "/signup" | "/sla" | "/tenants" | "/terms" | "/testimonials" | "/translations" | "/tunnels" | "/workorders";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/favicon.png" | "/favicon.svg" | "/icons/apple-touch-icon.png" | "/icons/icon-192.png" | "/icons/icon-512.png" | "/icons/icon-base.svg" | "/vite.svg" | string & {};
	}
}