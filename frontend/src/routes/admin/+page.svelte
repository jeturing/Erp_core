<script>
	import { onMount } from 'svelte';
	import AdminHeader from './components/AdminHeader.svelte';
	import SmtpManager from './components/SmtpManager.svelte';
	import TemplateManager from './components/TemplateManager.svelte';
	import StorageAlertsManager from './components/StorageAlertsManager.svelte';

	let activeTab = 'smtp';
	let apiKey = 'prov-key-2026-secure';
	let baseUrl = '/api/admin';

	// Headers comunes para todas las peticiones
	const getHeaders = () => ({
		'Content-Type': 'application/json',
		'x-api-key': apiKey
	});

	const handleTabChange = (tab) => {
		activeTab = tab;
	};

	const handleApiKeyChange = (event) => {
		apiKey = event.detail;
	};
</script>

<div class="admin-container">
	<AdminHeader {apiKey} on:apiKeyChange={handleApiKeyChange} />

	<div class="tabs-container">
		<div class="tabs">
			<button
				class="tab-button {activeTab === 'smtp' ? 'active' : ''}"
				on:click={() => handleTabChange('smtp')}
			>
				📧 SMTP
			</button>
			<button
				class="tab-button {activeTab === 'templates' ? 'active' : ''}"
				on:click={() => handleTabChange('templates')}
			>
				📝 Email Templates
			</button>
			<button
				class="tab-button {activeTab === 'storage' ? 'active' : ''}"
				on:click={() => handleTabChange('storage')}
			>
				💾 Storage Alerts
			</button>
		</div>
	</div>

	<div class="content-area">
		{#if activeTab === 'smtp'}
			<SmtpManager />
		{:else if activeTab === 'templates'}
			<TemplateManager />
		{:else if activeTab === 'storage'}
			<StorageAlertsManager />
		{/if}
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
		background: #020e1f;
		background-image:
			radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0, 59, 115, 0.35) 0%, transparent 60%),
			radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0, 59, 115, 0.2) 0%, transparent 60%);
		min-height: 100vh;
	}

	.admin-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 20px;
		background: #0a1628;
		border: 1px solid rgba(0, 255, 159, 0.08);
		border-radius: 12px;
		box-shadow: rgba(50,50,93,0.25) 0px 30px 60px -12px, rgba(0,0,0,0.3) 0px 18px 36px -18px;
		margin-top: 20px;
		margin-bottom: 20px;
	}

	.tabs-container {
		border-bottom: 1px solid rgba(0, 255, 159, 0.12);
		margin: 30px 0 0 0;
	}

	.tabs {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}

	.tab-button {
		padding: 12px 24px;
		border: none;
		background: transparent;
		cursor: pointer;
		font-size: 13px;
		font-weight: 500;
		color: rgba(200, 211, 232, 0.55);
		border-bottom: 2px solid transparent;
		transition: all 0.2s ease;
		position: relative;
		bottom: -1px;
		letter-spacing: 0.01em;
	}

	.tab-button:hover {
		color: #c8d3e8;
		border-bottom-color: rgba(0, 255, 159, 0.25);
	}

	.tab-button.active {
		color: #00FF9F;
		border-bottom-color: #00FF9F;
	}

	.content-area {
		padding: 30px 0;
		animation: fadeIn 0.3s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
