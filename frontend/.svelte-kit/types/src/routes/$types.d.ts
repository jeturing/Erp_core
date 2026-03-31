import type * as Kit from '@sveltejs/kit';

type Expand<T> = T extends infer O ? { [K in keyof O]: O[K] } : never;
type MatcherParam<M> = M extends (param : string) => param is (infer U extends string) ? U : string;
type RouteParams = {  };
type RouteId = '/';
type MaybeWithVoid<T> = {} extends T ? T | void : T;
export type RequiredKeys<T> = { [K in keyof T]-?: {} extends { [P in K]: T[K] } ? never : K; }[keyof T];
type OutputDataShape<T> = MaybeWithVoid<Omit<App.PageData, RequiredKeys<T>> & Partial<Pick<App.PageData, keyof T & keyof App.PageData>> & Record<string, any>>
type EnsureDefined<T> = T extends null | undefined ? {} : T;
type OptionalUnion<U extends Record<string, any>, A extends keyof U = U extends U ? keyof U : never> = U extends unknown ? { [P in Exclude<A, keyof U>]?: never } & U : never;
export type Snapshot<T = any> = Kit.Snapshot<T>;
type LayoutRouteId = RouteId | "/(admin)/admin-users" | "/(admin)/agreements" | "/(admin)/audit" | "/(admin)/billing" | "/(admin)/blueprints" | "/(admin)/branding" | "/(admin)/catalog" | "/(admin)/clients" | "/(admin)/commissions" | "/(admin)/communications" | "/(admin)/dashboard" | "/(admin)/dispersion" | "/(admin)/domains" | "/(admin)/infrastructure" | "/(admin)/invoices" | "/(admin)/landing-sections" | "/(admin)/leads" | "/(admin)/logs" | "/(admin)/migrations" | "/(admin)/neural-users" | "/(admin)/onboarding-config" | "/(admin)/partners" | "/(admin)/plans" | "/(admin)/quotations" | "/(admin)/reconciliation" | "/(admin)/reports" | "/(admin)/roles" | "/(admin)/seats" | "/(admin)/session-monitoring" | "/(admin)/settings" | "/(admin)/settlements" | "/(admin)/tenants" | "/(admin)/testimonials" | "/(admin)/translations" | "/(admin)/tunnels" | "/(admin)/workorders" | "/(portal)/accountant-portal" | "/(portal)/customer-onboarding" | "/(portal)/partner-portal" | "/(portal)/portal" | "/(public)" | "/(public)/about" | "/(public)/accountants" | "/(public)/data-processing" | "/(public)/login" | "/(public)/onboarding-access" | "/(public)/partner-signup" | "/(public)/plt/[slug]" | "/(public)/pricing" | "/(public)/privacy" | "/(public)/recover-account" | "/(public)/security" | "/(public)/servicios" | "/(public)/signup" | "/(public)/sla" | "/(public)/terms" | "/admin" | null
type LayoutParams = RouteParams & { slug?: string }
type LayoutParentData = EnsureDefined<{}>;

export type LayoutServerData = null;
export type LayoutLoad<OutputData extends OutputDataShape<LayoutParentData> = OutputDataShape<LayoutParentData>> = Kit.Load<LayoutParams, LayoutServerData, LayoutParentData, OutputData, LayoutRouteId>;
export type LayoutLoadEvent = Parameters<LayoutLoad>[0];
export type LayoutData = Expand<Omit<LayoutParentData, keyof LayoutParentData & EnsureDefined<LayoutServerData>> & OptionalUnion<EnsureDefined<LayoutParentData & EnsureDefined<LayoutServerData>>>>;
export type LayoutProps = { params: LayoutParams; data: LayoutData; children: import("svelte").Snippet }