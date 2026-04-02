<script>
	import { onMount } from 'svelte';

	const baseUrl = '/api/admin';
	const apiKey = 'prov-key-2026-secure';

	let config = {
		warning_threshold: 75,
		critical_threshold: 90,
		exceeded_threshold: 100,
		check_interval_hours: 24,
		slack_enabled: false,
		slack_webhook: ''
	};

	let formData = { ...config };
	let alerts = [];
	let stats = {};
	let trends = {};
	let loading = true;
	let editMode = false;
	let alert = null;
	let selectedAlertId = null;
	let showSlackConfig = false;

	onMount(() => {
		Promise.all([loadConfig(), loadActiveAlerts(), loadStats(), loadTrends()]);
	});

	const getHeaders = () => ({
		'Content-Type': 'application/json',
		'X-API-Key': apiKey
	});

	const loadConfig = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/config`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			const data = await res.json();
			config = data;
			formData = { ...config };
			showAlert('✅ Configuración cargada', 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const loadActiveAlerts = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/active`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			alerts = await res.json();
		} catch (error) {
			showAlert(`❌ Error cargando alertas: ${error.message}`, 'error');
		}
	};

	const loadStats = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/stats`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			stats = await res.json();
		} catch (error) {
			console.error('Error loading stats:', error);
		}
	};

	const loadTrends = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/trends`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			trends = await res.json();
		} catch (error) {
			console.error('Error loading trends:', error);
		} finally {
			loading = false;
		}
	};

	const updateConfig = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/config`, {
				method: 'PUT',
				headers: getHeaders(),
				body: JSON.stringify(formData)
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			config = { ...formData };
			editMode = false;
			showAlert('✅ Configuración actualizada exitosamente', 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const resolveAlert = async (alertId) => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/resolve`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({ alert_id: alertId })
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			showAlert('✅ Alerta resuelta', 'success');
			await loadActiveAlerts();
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const setupSlackWebhook = async () => {
		try {
			const res = await fetch(`${baseUrl}/storage-alerts/slack`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({
					slack_enabled: formData.slack_enabled,
					slack_webhook: formData.slack_webhook
				})
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			config.slack_enabled = formData.slack_enabled;
			config.slack_webhook = formData.slack_webhook;
			showAlert('✅ Configuración de Slack actualizada', 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const cancelEdit = () => {
		formData = { ...config };
		editMode = false;
	};

	const showAlert = (message, type) => {
		alert = { message, type };
		setTimeout(() => {
			alert = null;
		}, 4000);
	};

	const getAlertLevel = (usage) => {
		if (usage >= config.exceeded_threshold) return 'exceeded';
		if (usage >= config.critical_threshold) return 'critical';
		if (usage >= config.warning_threshold) return 'warning';
		return 'normal';
	};

	const getAlertLevelBadge = (usage) => {
		const level = getAlertLevel(usage);
		switch (level) {
			case 'exceeded':
				return '🔴';
			case 'critical':
				return '🟠';
			case 'warning':
				return '🟡';
			default:
				return '🟢';
		}
	};

	const formatDate = (dateString) => {
		return new Date(dateString).toLocaleDateString('es-ES', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	};

	const formatBytes = (bytes) => {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
	};
</script>

<div class="storage-container">
	{#if alert}
		<div class="alert alert-{alert.type}">
			{alert.message}
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner" />
			<p>Cargando alertas de almacenamiento...</p>
		</div>
	{:else}
		<!-- Thresholds Section -->
		<div class="section">
			<div class="section-header">
				<h4>📊 Umbrales de Alerta</h4>
				<button class="btn btn-small btn-primary" on:click={() => (editMode = !editMode)}>
					{editMode ? '❌ Cancelar' : '✏️ Editar'}
				</button>
			</div>

			{#if editMode}
				<div class="edit-form">
					<div class="form-group">
						<label for="warning">Umbral de Advertencia (%)</label>
						<div class="slider-group">
							<input
								id="warning"
								type="range"
								min="0"
								max="100"
								bind:value={formData.warning_threshold}
								class="slider"
							/>
							<span class="slider-value">{formData.warning_threshold}%</span>
						</div>
					</div>

					<div class="form-group">
						<label for="critical">Umbral Crítico (%)</label>
						<div class="slider-group">
							<input
								id="critical"
								type="range"
								min="0"
								max="100"
								bind:value={formData.critical_threshold}
								class="slider"
							/>
							<span class="slider-value">{formData.critical_threshold}%</span>
						</div>
					</div>

					<div class="form-group">
						<label for="exceeded">Umbral Excedido (%)</label>
						<div class="slider-group">
							<input
								id="exceeded"
								type="range"
								min="0"
								max="100"
								bind:value={formData.exceeded_threshold}
								class="slider"
							/>
							<span class="slider-value">{formData.exceeded_threshold}%</span>
						</div>
					</div>

					<div class="form-group">
						<label for="interval">Intervalo de Verificación (horas)</label>
						<input
							id="interval"
							type="number"
							bind:value={formData.check_interval_hours}
							min="1"
							max="168"
						/>
					</div>

					<div class="form-actions">
						<button class="btn btn-primary" on:click={updateConfig}>💾 Guardar</button>
						<button class="btn btn-secondary" on:click={cancelEdit}>❌ Cancelar</button>
					</div>
				</div>
			{:else}
				<div class="threshold-grid">
					<div class="threshold-card warning">
						<span class="label">Advertencia</span>
						<span class="value">{config.warning_threshold}%</span>
					</div>
					<div class="threshold-card critical">
						<span class="label">Crítico</span>
						<span class="value">{config.critical_threshold}%</span>
					</div>
					<div class="threshold-card exceeded">
						<span class="label">Excedido</span>
						<span class="value">{config.exceeded_threshold}%</span>
					</div>
					<div class="threshold-card info">
						<span class="label">Verificar Cada</span>
						<span class="value">{config.check_interval_hours} horas</span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Active Alerts Section -->
		<div class="section">
			<div class="section-header">
				<h4>🚨 Alertas Activas</h4>
				<span class="badge">{alerts.length} alertas</span>
			</div>

			{#if alerts.length === 0}
				<div class="empty-state">
					<span class="icon">✅</span>
					<p>No hay alertas activas. Tu almacenamiento está bajo control.</p>
				</div>
			{:else}
				<div class="alerts-grid">
					{#each alerts as alert (alert.id)}
						<div class="alert-card alert-level-{getAlertLevel(alert.storage_usage_percent)}">
							<div class="alert-header">
								<span class="level-badge">{getAlertLevelBadge(alert.storage_usage_percent)}</span>
								<span class="customer-name">{alert.customer_id || 'Sistema'}</span>
							</div>

							<div class="alert-body">
								<div class="usage-bar">
									<div
										class="usage-fill"
										style="width: {alert.storage_usage_percent}%"
									/>
								</div>
								<span class="usage-text">{alert.storage_usage_percent.toFixed(1)}% utilizado</span>
							</div>

							<div class="alert-footer">
								<span class="date">{formatDate(alert.created_at)}</span>
								<button
									class="btn btn-small btn-danger"
									on:click={() => resolveAlert(alert.id)}
								>
									✓ Resolver
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Statistics Section -->
		{#if stats && Object.keys(stats).length > 0}
			<div class="section">
				<div class="section-header">
					<h4>📈 Estadísticas</h4>
				</div>

				<div class="stats-grid">
					{#each Object.entries(stats) as [key, value]}
						<div class="stat-card">
							<span class="stat-label">{key}</span>
							<span class="stat-value">{typeof value === 'number' ? value.toFixed(2) : value}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Slack Configuration Section -->
		<div class="section">
			<div class="section-header">
				<h4>💬 Configuración de Slack</h4>
				<button
					class="btn btn-small"
					class:btn-primary={!showSlackConfig}
					class:btn-secondary={showSlackConfig}
					on:click={() => (showSlackConfig = !showSlackConfig)}
				>
					{showSlackConfig ? '❌ Cerrar' : '⚙️ Configurar'}
				</button>
			</div>

			{#if showSlackConfig}
				<div class="slack-form">
					<div class="form-group">
						<label>
							<input type="checkbox" bind:checked={formData.slack_enabled} />
							Habilitar notificaciones de Slack
						</label>
					</div>

					{#if formData.slack_enabled}
						<div class="form-group">
							<label for="webhook">URL del Webhook de Slack</label>
							<input
								id="webhook"
								type="text"
								bind:value={formData.slack_webhook}
								placeholder="https://hooks.slack.com/services/..."
							/>
							<small>Obtén tu webhook en: https://api.slack.com/messaging/webhooks</small>
						</div>

						<button class="btn btn-primary" on:click={setupSlackWebhook}>
							💾 Guardar Webhook
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Help Section -->
		<div class="help-section">
			<h4>📚 Ayuda: Alertas de Almacenamiento</h4>
			<ul>
				<li><strong>Advertencia:</strong> Se envía cuando el almacenamiento alcanza el {config.warning_threshold}%</li>
				<li><strong>Crítico:</strong> Se envía cuando el almacenamiento alcanza el {config.critical_threshold}%</li>
				<li><strong>Excedido:</strong> Se envía cuando el almacenamiento alcanza o supera el {config.exceeded_threshold}%</li>
				<li><strong>Verificación:</strong> Se realiza cada {config.check_interval_hours} horas automáticamente</li>
				<li><strong>Slack:</strong> Las alertas pueden enviarse automáticamente a un canal de Slack</li>
			</ul>
		</div>
	{/if}
</div>

<style>
	.storage-container {
		padding: 20px;
		background: white;
		border-radius: 8px;
	}

	.loading {
		text-align: center;
		padding: 40px 20px;
	}

	.spinner {
		border: 4px solid #e5e7eb;
		border-top-color: #667eea;
		border-radius: 50%;
		width: 40px;
		height: 40px;
		margin: 0 auto 15px;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.alert {
		padding: 12px 15px;
		border-radius: 6px;
		margin-bottom: 15px;
		font-size: 14px;
		font-weight: 500;
	}

	.alert-success {
		background: #dcfce7;
		color: #166534;
		border-left: 4px solid #22c55e;
	}

	.alert-error {
		background: #fee2e2;
		color: #991b1b;
		border-left: 4px solid #ef4444;
	}

	.section {
		margin-bottom: 25px;
		border-bottom: 1px solid #e5e7eb;
		padding-bottom: 20px;
	}

	.section:last-of-type {
		border-bottom: none;
	}

	.section-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 15px;
	}

	.section-header h4 {
		margin: 0;
		font-size: 16px;
		color: #1f2937;
	}

	.badge {
		background: #dbeafe;
		color: #1e40af;
		padding: 4px 8px;
		border-radius: 12px;
		font-size: 12px;
		font-weight: 600;
	}

	.threshold-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 15px;
	}

	.threshold-card {
		padding: 15px;
		border-radius: 8px;
		text-align: center;
		color: white;
		font-weight: 600;
	}

	.threshold-card.warning {
		background: linear-gradient(135deg, #f59e0b, #f97316);
	}

	.threshold-card.critical {
		background: linear-gradient(135deg, #ef4444, #dc2626);
	}

	.threshold-card.exceeded {
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
	}

	.threshold-card.info {
		background: linear-gradient(135deg, #3b82f6, #1d4ed8);
	}

	.threshold-card .label {
		display: block;
		font-size: 12px;
		opacity: 0.9;
		margin-bottom: 5px;
	}

	.threshold-card .value {
		display: block;
		font-size: 20px;
	}

	.edit-form {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 20px;
	}

	.form-group {
		margin-bottom: 15px;
	}

	.form-group label {
		display: block;
		margin-bottom: 8px;
		font-size: 14px;
		font-weight: 600;
		color: #374151;
	}

	.form-group input[type='text'],
	.form-group input[type='number'] {
		width: 100%;
		padding: 10px 12px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 14px;
		box-sizing: border-box;
	}

	.form-group input:focus {
		outline: none;
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.slider-group {
		display: flex;
		gap: 15px;
		align-items: center;
	}

	.slider {
		flex: 1;
		height: 6px;
		border-radius: 3px;
		background: #e5e7eb;
		outline: none;
		-webkit-appearance: none;
		appearance: none;
	}

	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: #667eea;
		cursor: pointer;
	}

	.slider::-moz-range-thumb {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: #667eea;
		cursor: pointer;
		border: none;
	}

	.slider-value {
		min-width: 50px;
		text-align: center;
		font-weight: 600;
		color: #667eea;
	}

	.form-actions {
		display: flex;
		gap: 10px;
		margin-top: 20px;
	}

	.empty-state {
		text-align: center;
		padding: 40px 20px;
		background: #f0fdf4;
		border-radius: 8px;
		border: 1px dashed #86efac;
	}

	.empty-state .icon {
		display: block;
		font-size: 48px;
		margin-bottom: 15px;
	}

	.empty-state p {
		margin: 0;
		color: #166534;
		font-size: 14px;
	}

	.alerts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 15px;
	}

	.alert-card {
		border-radius: 8px;
		padding: 15px;
		background: white;
		border: 2px solid;
	}

	.alert-level-normal {
		border-color: #22c55e;
	}

	.alert-level-warning {
		border-color: #f59e0b;
		background: #fffbeb;
	}

	.alert-level-critical {
		border-color: #ef4444;
		background: #fef2f2;
	}

	.alert-level-exceeded {
		border-color: #8b5cf6;
		background: #faf5ff;
	}

	.alert-header {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 12px;
	}

	.level-badge {
		font-size: 20px;
	}

	.customer-name {
		font-weight: 600;
		color: #1f2937;
		flex: 1;
	}

	.alert-body {
		margin-bottom: 12px;
	}

	.usage-bar {
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 8px;
	}

	.usage-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea, #764ba2);
		transition: width 0.3s;
	}

	.usage-text {
		font-size: 12px;
		color: #6b7280;
		font-weight: 500;
	}

	.alert-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 12px;
	}

	.date {
		color: #9ca3af;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}

	.stat-card {
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		padding: 20px;
		border-radius: 8px;
		text-align: center;
	}

	.stat-label {
		display: block;
		font-size: 12px;
		font-weight: 600;
		opacity: 0.9;
		margin-bottom: 8px;
		text-transform: uppercase;
	}

	.stat-value {
		display: block;
		font-size: 24px;
		font-weight: 700;
	}

	.slack-form {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 20px;
	}

	.slack-form input[type='checkbox'] {
		margin-right: 8px;
		cursor: pointer;
	}

	.slack-form label {
		display: flex;
		align-items: center;
		font-weight: 500;
		color: #374151;
		cursor: pointer;
	}

	.slack-form small {
		display: block;
		margin-top: 5px;
		color: #6b7280;
		font-size: 12px;
	}

	.help-section {
		background: #fef3c7;
		border: 1px solid #fcd34d;
		border-radius: 8px;
		padding: 15px;
		margin-top: 20px;
	}

	.help-section h4 {
		margin: 0 0 10px 0;
		color: #92400e;
		font-size: 14px;
	}

	.help-section ul {
		margin: 0;
		padding-left: 20px;
		font-size: 13px;
		color: #78350f;
	}

	.help-section li {
		margin-bottom: 6px;
	}

	.btn {
		padding: 10px 16px;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 600;
		transition: all 0.2s;
	}

	.btn-small {
		padding: 6px 12px;
		font-size: 12px;
	}

	.btn-primary {
		background: #667eea;
		color: white;
	}

	.btn-primary:hover {
		background: #5568d3;
	}

	.btn-secondary {
		background: #e5e7eb;
		color: #374151;
	}

	.btn-secondary:hover {
		background: #d1d5db;
	}

	.btn-danger {
		background: #ef4444;
		color: white;
	}

	.btn-danger:hover {
		background: #dc2626;
	}
</style>
