export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["favicon.png","favicon.svg","icons/apple-touch-icon.png","icons/icon-192.png","icons/icon-512.png","icons/icon-base.svg","vite.svg"]),
	mimeTypes: {".png":"image/png",".svg":"image/svg+xml"},
	_: {
		client: {start:"_app/immutable/entry/start.mvdX-0k5.js",app:"_app/immutable/entry/app.CEt8q0nb.js",imports:["_app/immutable/entry/start.mvdX-0k5.js","_app/immutable/chunks/Bl6j3YKi.js","_app/immutable/chunks/DuWWigTJ.js","_app/immutable/chunks/B_gHqzB-.js","_app/immutable/chunks/BUApaBEI.js","_app/immutable/chunks/B7uMneuC.js","_app/immutable/entry/app.CEt8q0nb.js","_app/immutable/chunks/PPVm8Dsz.js","_app/immutable/chunks/DQiEKq5i.js","_app/immutable/chunks/DDc_ZsX7.js","_app/immutable/chunks/B_gHqzB-.js","_app/immutable/chunks/DuWWigTJ.js","_app/immutable/chunks/Cpj98o6Y.js","_app/immutable/chunks/GISHIjFi.js","_app/immutable/chunks/DWNdrKHs.js","_app/immutable/chunks/Do5B4ou-.js","_app/immutable/chunks/B7uMneuC.js","_app/immutable/chunks/C44dcGQ9.js","_app/immutable/chunks/Au2gfsmC.js","_app/immutable/chunks/BXwTWXYs.js","_app/immutable/chunks/BvvNcLM0.js","_app/immutable/chunks/Cduyk_Qq.js","_app/immutable/chunks/RpkTUpfy.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js')),
			__memo(() => import('./nodes/4.js')),
			__memo(() => import('./nodes/5.js')),
			__memo(() => import('./nodes/6.js')),
			__memo(() => import('./nodes/7.js')),
			__memo(() => import('./nodes/8.js')),
			__memo(() => import('./nodes/9.js')),
			__memo(() => import('./nodes/10.js')),
			__memo(() => import('./nodes/11.js')),
			__memo(() => import('./nodes/12.js')),
			__memo(() => import('./nodes/13.js')),
			__memo(() => import('./nodes/14.js')),
			__memo(() => import('./nodes/15.js')),
			__memo(() => import('./nodes/16.js')),
			__memo(() => import('./nodes/17.js')),
			__memo(() => import('./nodes/18.js')),
			__memo(() => import('./nodes/19.js')),
			__memo(() => import('./nodes/20.js')),
			__memo(() => import('./nodes/21.js')),
			__memo(() => import('./nodes/22.js')),
			__memo(() => import('./nodes/23.js')),
			__memo(() => import('./nodes/24.js')),
			__memo(() => import('./nodes/25.js')),
			__memo(() => import('./nodes/26.js')),
			__memo(() => import('./nodes/27.js')),
			__memo(() => import('./nodes/28.js')),
			__memo(() => import('./nodes/29.js')),
			__memo(() => import('./nodes/30.js')),
			__memo(() => import('./nodes/31.js')),
			__memo(() => import('./nodes/32.js')),
			__memo(() => import('./nodes/33.js')),
			__memo(() => import('./nodes/34.js')),
			__memo(() => import('./nodes/35.js')),
			__memo(() => import('./nodes/36.js')),
			__memo(() => import('./nodes/37.js')),
			__memo(() => import('./nodes/38.js')),
			__memo(() => import('./nodes/39.js')),
			__memo(() => import('./nodes/40.js')),
			__memo(() => import('./nodes/41.js')),
			__memo(() => import('./nodes/42.js')),
			__memo(() => import('./nodes/43.js')),
			__memo(() => import('./nodes/44.js')),
			__memo(() => import('./nodes/45.js')),
			__memo(() => import('./nodes/46.js')),
			__memo(() => import('./nodes/47.js')),
			__memo(() => import('./nodes/48.js')),
			__memo(() => import('./nodes/49.js')),
			__memo(() => import('./nodes/50.js')),
			__memo(() => import('./nodes/51.js')),
			__memo(() => import('./nodes/52.js')),
			__memo(() => import('./nodes/53.js')),
			__memo(() => import('./nodes/54.js')),
			__memo(() => import('./nodes/55.js')),
			__memo(() => import('./nodes/56.js')),
			__memo(() => import('./nodes/57.js')),
			__memo(() => import('./nodes/58.js')),
			__memo(() => import('./nodes/59.js')),
			__memo(() => import('./nodes/60.js')),
			__memo(() => import('./nodes/61.js')),
			__memo(() => import('./nodes/62.js')),
			__memo(() => import('./nodes/63.js')),
			__memo(() => import('./nodes/64.js')),
			__memo(() => import('./nodes/65.js')),
			__memo(() => import('./nodes/66.js')),
			__memo(() => import('./nodes/67.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/(public)",
				pattern: /^\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 50 },
				endpoint: null
			},
			{
				id: "/(public)/about",
				pattern: /^\/about\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 51 },
				endpoint: null
			},
			{
				id: "/(portal)/accountant-portal",
				pattern: /^\/accountant-portal\/?$/,
				params: [],
				page: { layouts: [0,3,], errors: [1,,], leaf: 46 },
				endpoint: null
			},
			{
				id: "/(public)/accountants",
				pattern: /^\/accountants\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 52 },
				endpoint: null
			},
			{
				id: "/(admin)/admin-users",
				pattern: /^\/admin-users\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/admin",
				pattern: /^\/admin\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 67 },
				endpoint: null
			},
			{
				id: "/(admin)/agreements",
				pattern: /^\/agreements\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/(admin)/api-keys",
				pattern: /^\/api-keys\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/(admin)/audit",
				pattern: /^\/audit\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 8 },
				endpoint: null
			},
			{
				id: "/(admin)/billing",
				pattern: /^\/billing\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 9 },
				endpoint: null
			},
			{
				id: "/(admin)/blueprints",
				pattern: /^\/blueprints\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 10 },
				endpoint: null
			},
			{
				id: "/(admin)/branding",
				pattern: /^\/branding\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 11 },
				endpoint: null
			},
			{
				id: "/(admin)/catalog",
				pattern: /^\/catalog\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 12 },
				endpoint: null
			},
			{
				id: "/(admin)/clients",
				pattern: /^\/clients\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 13 },
				endpoint: null
			},
			{
				id: "/(admin)/commissions",
				pattern: /^\/commissions\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 14 },
				endpoint: null
			},
			{
				id: "/(admin)/communications",
				pattern: /^\/communications\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 15 },
				endpoint: null
			},
			{
				id: "/(portal)/customer-onboarding",
				pattern: /^\/customer-onboarding\/?$/,
				params: [],
				page: { layouts: [0,3,], errors: [1,,], leaf: 47 },
				endpoint: null
			},
			{
				id: "/(admin)/dashboard",
				pattern: /^\/dashboard\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 16 },
				endpoint: null
			},
			{
				id: "/(public)/data-processing",
				pattern: /^\/data-processing\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 53 },
				endpoint: null
			},
			{
				id: "/(admin)/developer-portal",
				pattern: /^\/developer-portal\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 17 },
				endpoint: null
			},
			{
				id: "/(admin)/dispersion",
				pattern: /^\/dispersion\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 18 },
				endpoint: null
			},
			{
				id: "/(admin)/domains",
				pattern: /^\/domains\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 19 },
				endpoint: null
			},
			{
				id: "/(admin)/infrastructure",
				pattern: /^\/infrastructure\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 20 },
				endpoint: null
			},
			{
				id: "/(admin)/invoices",
				pattern: /^\/invoices\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 21 },
				endpoint: null
			},
			{
				id: "/(admin)/landing-sections",
				pattern: /^\/landing-sections\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 22 },
				endpoint: null
			},
			{
				id: "/(admin)/leads",
				pattern: /^\/leads\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 23 },
				endpoint: null
			},
			{
				id: "/(public)/login",
				pattern: /^\/login\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 54 },
				endpoint: null
			},
			{
				id: "/(public)/login/admin",
				pattern: /^\/login\/admin\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 55 },
				endpoint: null
			},
			{
				id: "/(admin)/logs",
				pattern: /^\/logs\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 24 },
				endpoint: null
			},
			{
				id: "/(admin)/migrations",
				pattern: /^\/migrations\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 25 },
				endpoint: null
			},
			{
				id: "/(admin)/neural-users",
				pattern: /^\/neural-users\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 26 },
				endpoint: null
			},
			{
				id: "/(public)/onboarding-access",
				pattern: /^\/onboarding-access\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 56 },
				endpoint: null
			},
			{
				id: "/(admin)/onboarding-config",
				pattern: /^\/onboarding-config\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 27 },
				endpoint: null
			},
			{
				id: "/(portal)/partner-portal",
				pattern: /^\/partner-portal\/?$/,
				params: [],
				page: { layouts: [0,3,], errors: [1,,], leaf: 48 },
				endpoint: null
			},
			{
				id: "/(public)/partner-signup",
				pattern: /^\/partner-signup\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 57 },
				endpoint: null
			},
			{
				id: "/(admin)/partners",
				pattern: /^\/partners\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 28 },
				endpoint: null
			},
			{
				id: "/(admin)/plan-governance",
				pattern: /^\/plan-governance\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 29 },
				endpoint: null
			},
			{
				id: "/(admin)/plans",
				pattern: /^\/plans\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 30 },
				endpoint: null
			},
			{
				id: "/(public)/plt/[slug]",
				pattern: /^\/plt\/([^/]+?)\/?$/,
				params: [{"name":"slug","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,4,], errors: [1,,], leaf: 58 },
				endpoint: null
			},
			{
				id: "/(portal)/portal",
				pattern: /^\/portal\/?$/,
				params: [],
				page: { layouts: [0,3,], errors: [1,,], leaf: 49 },
				endpoint: null
			},
			{
				id: "/(public)/pricing",
				pattern: /^\/pricing\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 59 },
				endpoint: null
			},
			{
				id: "/(public)/privacy",
				pattern: /^\/privacy\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 60 },
				endpoint: null
			},
			{
				id: "/(admin)/quotas",
				pattern: /^\/quotas\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 31 },
				endpoint: null
			},
			{
				id: "/(admin)/quotations",
				pattern: /^\/quotations\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 32 },
				endpoint: null
			},
			{
				id: "/(admin)/reconciliation",
				pattern: /^\/reconciliation\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 33 },
				endpoint: null
			},
			{
				id: "/(public)/recover-account",
				pattern: /^\/recover-account\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 61 },
				endpoint: null
			},
			{
				id: "/(admin)/reports",
				pattern: /^\/reports\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 34 },
				endpoint: null
			},
			{
				id: "/(admin)/roles",
				pattern: /^\/roles\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 35 },
				endpoint: null
			},
			{
				id: "/(admin)/seats",
				pattern: /^\/seats\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 36 },
				endpoint: null
			},
			{
				id: "/(public)/security",
				pattern: /^\/security\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 62 },
				endpoint: null
			},
			{
				id: "/(public)/servicios",
				pattern: /^\/servicios\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 63 },
				endpoint: null
			},
			{
				id: "/(admin)/session-monitoring",
				pattern: /^\/session-monitoring\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 37 },
				endpoint: null
			},
			{
				id: "/(admin)/settings",
				pattern: /^\/settings\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 38 },
				endpoint: null
			},
			{
				id: "/(admin)/settlements",
				pattern: /^\/settlements\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 39 },
				endpoint: null
			},
			{
				id: "/(public)/signup",
				pattern: /^\/signup\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 64 },
				endpoint: null
			},
			{
				id: "/(public)/sla",
				pattern: /^\/sla\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 65 },
				endpoint: null
			},
			{
				id: "/(admin)/stripe-connect",
				pattern: /^\/stripe-connect\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 40 },
				endpoint: null
			},
			{
				id: "/(admin)/tenants",
				pattern: /^\/tenants\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 41 },
				endpoint: null
			},
			{
				id: "/(public)/terms",
				pattern: /^\/terms\/?$/,
				params: [],
				page: { layouts: [0,4,], errors: [1,,], leaf: 66 },
				endpoint: null
			},
			{
				id: "/(admin)/testimonials",
				pattern: /^\/testimonials\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 42 },
				endpoint: null
			},
			{
				id: "/(admin)/translations",
				pattern: /^\/translations\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 43 },
				endpoint: null
			},
			{
				id: "/(admin)/tunnels",
				pattern: /^\/tunnels\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 44 },
				endpoint: null
			},
			{
				id: "/(admin)/workorders",
				pattern: /^\/workorders\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 45 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
