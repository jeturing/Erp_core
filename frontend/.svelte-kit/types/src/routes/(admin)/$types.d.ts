import type * as Kit from '@sveltejs/kit';

type Expand<T> = T extends infer O ? { [K in keyof O]: O[K] } : never;
type MatcherParam<M> = M extends (param : string) => param is (infer U extends string) ? U : string;
type RouteParams = {  };
type RouteId = '/(admin)';
type MaybeWithVoid<T> = {} extends T ? T | void : T;
export type RequiredKeys<T> = { [K in keyof T]-?: {} extends { [P in K]: T[K] } ? never : K; }[keyof T];
type OutputDataShape<T> = MaybeWithVoid<Omit<App.PageData, RequiredKeys<T>> & Partial<Pick<App.PageData, keyof T & keyof App.PageData>> & Record<string, any>>
type EnsureDefined<T> = T extends null | undefined ? {} : T;
type OptionalUnion<U extends Record<string, any>, A extends keyof U = U extends U ? keyof U : never> = U extends unknown ? { [P in Exclude<A, keyof U>]?: never } & U : never;
export type Snapshot<T = any> = Kit.Snapshot<T>;
type LayoutRouteId = RouteId | "/(admin)/admin-users" | "/(admin)/agreements" | "/(admin)/api-keys" | "/(admin)/audit" | "/(admin)/billing" | "/(admin)/blueprints" | "/(admin)/branding" | "/(admin)/catalog" | "/(admin)/clients" | "/(admin)/commissions" | "/(admin)/communications" | "/(admin)/dashboard" | "/(admin)/developer-portal" | "/(admin)/dispersion" | "/(admin)/domains" | "/(admin)/infrastructure" | "/(admin)/invoices" | "/(admin)/landing-sections" | "/(admin)/leads" | "/(admin)/logs" | "/(admin)/migrations" | "/(admin)/neural-users" | "/(admin)/onboarding-config" | "/(admin)/partners" | "/(admin)/plan-governance" | "/(admin)/plans" | "/(admin)/quotas" | "/(admin)/quotations" | "/(admin)/reconciliation" | "/(admin)/reports" | "/(admin)/roles" | "/(admin)/seats" | "/(admin)/session-monitoring" | "/(admin)/settings" | "/(admin)/settlements" | "/(admin)/stripe-connect" | "/(admin)/tenants" | "/(admin)/testimonials" | "/(admin)/translations" | "/(admin)/tunnels" | "/(admin)/workorders"
type LayoutParams = RouteParams & {  }
type LayoutParentData = EnsureDefined<import('../$types.js').LayoutData>;

export type LayoutServerData = null;
export type LayoutLoad<OutputData extends OutputDataShape<LayoutParentData> = OutputDataShape<LayoutParentData>> = Kit.Load<LayoutParams, LayoutServerData, LayoutParentData, OutputData, LayoutRouteId>;
export type LayoutLoadEvent = Parameters<LayoutLoad>[0];
export type LayoutData = Expand<Omit<LayoutParentData, keyof Kit.LoadProperties<Awaited<ReturnType<typeof import('../../../../../src/routes/(admin)/+layout.js').load>>>> & OptionalUnion<EnsureDefined<Kit.LoadProperties<Awaited<ReturnType<typeof import('../../../../../src/routes/(admin)/+layout.js').load>>>>>>;
export type LayoutProps = { params: LayoutParams; data: LayoutData; children: import("svelte").Snippet }