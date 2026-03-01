<script>
	import { createEventDispatcher } from 'svelte';

	export let apiKey = 'prov-key-2026-secure';

	const dispatch = createEventDispatcher();
	let showKeyInput = false;
	let tempKey = apiKey;

	const handleSaveKey = () => {
		apiKey = tempKey;
		dispatch('apiKeyChange', apiKey);
		showKeyInput = false;
	};

	const handleCancel = () => {
		tempKey = apiKey;
		showKeyInput = false;
	};
</script>

<div class="header">
	<div class="header-content">
		<div class="logo-section">
			<h1>⚙️ Admin Panel</h1>
			<p>Gestión centralizada de SMTP, Templates y Alertas de Almacenamiento</p>
		</div>

		<div class="api-key-section">
			{#if showKeyInput}
				<div class="key-input-group">
					<input
						type="password"
						bind:value={tempKey}
						placeholder="API Key"
						class="key-input"
					/>
					<button class="btn btn-small btn-success" on:click={handleSaveKey}>✓ Guardar</button>
					<button class="btn btn-small btn-secondary" on:click={handleCancel}>✕ Cancelar</button>
				</div>
			{:else}
				<button class="btn btn-small btn-secondary" on:click={() => (showKeyInput = true)}>
					🔑 Cambiar API Key
				</button>
				<span class="api-key-display">API Key: {apiKey.substring(0, 8)}...{apiKey.substring(apiKey.length - 4)}</span>
			{/if}
		</div>
	</div>

	<div class="status-bar">
		<div class="status-item">
			<span class="status-badge status-ok">✓ Sistema Operacional</span>
		</div>
		<div class="status-item">
			<span class="status-time">{new Date().toLocaleString('es-ES')}</span>
		</div>
	</div>
</div>

<style>
	.header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 30px;
		border-radius: 12px 12px 0 0;
		margin: -20px -20px 0 -20px;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 30px;
		margin-bottom: 20px;
	}

	.logo-section h1 {
		margin: 0;
		font-size: 28px;
		font-weight: 700;
		letter-spacing: -0.5px;
	}

	.logo-section p {
		margin: 5px 0 0 0;
		opacity: 0.9;
		font-size: 14px;
		font-weight: 400;
	}

	.api-key-section {
		display: flex;
		gap: 12px;
		align-items: center;
	}

	.key-input-group {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.key-input {
		padding: 8px 12px;
		border: none;
		border-radius: 6px;
		font-size: 13px;
		width: 200px;
		background: rgba(255, 255, 255, 0.9);
		color: #1f2937;
	}

	.key-input:focus {
		outline: none;
		background: white;
		box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
	}

	.api-key-display {
		font-size: 12px;
		opacity: 0.85;
		font-weight: 500;
	}

	.status-bar {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		padding-top: 15px;
		border-top: 1px solid rgba(255, 255, 255, 0.2);
		font-size: 13px;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.status-badge {
		padding: 4px 10px;
		border-radius: 4px;
		font-weight: 600;
		font-size: 12px;
	}

	.status-ok {
		background: rgba(34, 197, 94, 0.2);
		color: #86efac;
	}

	.status-time {
		opacity: 0.8;
	}

	.btn {
		padding: 8px 16px;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 13px;
		font-weight: 600;
		transition: all 0.2s ease;
	}

	.btn-small {
		padding: 6px 12px;
		font-size: 12px;
	}

	.btn-success {
		background: rgba(34, 197, 94, 0.2);
		color: #86efac;
		border: 1px solid rgba(34, 197, 94, 0.3);
	}

	.btn-success:hover {
		background: rgba(34, 197, 94, 0.3);
	}

	.btn-secondary {
		background: rgba(255, 255, 255, 0.15);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.btn-secondary:hover {
		background: rgba(255, 255, 255, 0.25);
	}

	@media (max-width: 768px) {
		.header {
			padding: 20px;
		}

		.header-content {
			flex-direction: column;
			align-items: flex-start;
		}

		.api-key-section {
			width: 100%;
		}

		.status-bar {
			flex-direction: column;
		}
	}
</style>
