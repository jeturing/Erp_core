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
			<SmtpManager {baseUrl} {getHeaders} />
		{:else if activeTab === 'templates'}
			<TemplateManager {baseUrl} {getHeaders} />
		{:else if activeTab === 'storage'}
			<StorageAlertsManager {baseUrl} {getHeaders} />
		{/if}
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
			sans-serif;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
	}

	.admin-container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 20px;
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		margin-top: 20px;
		margin-bottom: 20px;
	}

	.tabs-container {
		border-bottom: 2px solid #e5e7eb;
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
		font-size: 14px;
		font-weight: 500;
		color: #6b7280;
		border-bottom: 3px solid transparent;
		transition: all 0.3s ease;
		position: relative;
		bottom: -2px;
	}

	.tab-button:hover {
		color: #111827;
		border-bottom-color: #e5e7eb;
	}

	.tab-button.active {
		color: #667eea;
		border-bottom-color: #667eea;
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
