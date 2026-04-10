<script>
	import { onMount } from 'svelte';

	const baseUrl = '/api/admin';

	let smtpConfig = {
		host: '',
		port: 587,
		username: '',
		password: '',
		from_email: '',
		from_name: ''
	};

	let formData = { ...smtpConfig };
	let loading = true;
	let testing = false;
	let editMode = false;
	let alert = null;
	let showPassword = false;

	onMount(() => {
		loadSmtpConfig();
	});

	const getHeaders = () => {
		const headers = {
			'Content-Type': 'application/json'
		};
		if (typeof window !== 'undefined') {
			const token = localStorage.getItem('access_token');
			if (token) {
				headers.Authorization = `Bearer ${token}`;
			}
		}
		return headers;
	};

	const loadSmtpConfig = async () => {
		try {
			loading = true;
			const res = await fetch(`${baseUrl}/smtp/config`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			const data = await res.json();
			smtpConfig = data;
			formData = { ...smtpConfig };
			showAlert('✅ Configuración SMTP cargada', 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		} finally {
			loading = false;
		}
	};

	const testSmtp = async () => {
		try {
			testing = true;
			const res = await fetch(`${baseUrl}/smtp/test`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({
					test_email: formData.from_email
				})
			});

			const data = await res.json();

			if (res.ok) {
				showAlert('✅ Conexión SMTP exitosa. Email de prueba enviado.', 'success');
			} else {
				showAlert(`❌ Error SMTP: ${data.detail || 'Error desconocido'}`, 'error');
			}
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		} finally {
			testing = false;
		}
	};

	const updateSmtpConfig = async () => {
		try {
			const res = await fetch(`${baseUrl}/smtp/config`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify(formData)
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			const data = await res.json();
			smtpConfig = { ...formData };
			editMode = false;
			showAlert('✅ Configuración SMTP actualizada exitosamente', 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const updateCredential = async (field) => {
		try {
			const res = await fetch(`${baseUrl}/smtp/credential`, {
				method: 'PUT',
				headers: getHeaders(),
				body: JSON.stringify({
					field: field,
					value: formData[field]
				})
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			smtpConfig[field] = formData[field];
			showAlert(`✅ ${field} actualizado correctamente`, 'success');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const getSmtpStatus = async () => {
		try {
			const res = await fetch(`${baseUrl}/smtp/status`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!res.ok) throw new Error(`Error ${res.status}`);

			const data = await res.json();
			showAlert(`ℹ️ Estado: ${data.status}`, 'info');
		} catch (error) {
			showAlert(`❌ Error: ${error.message}`, 'error');
		}
	};

	const cancelEdit = () => {
		formData = { ...smtpConfig };
		editMode = false;
	};

	const showAlert = (message, type) => {
		alert = { message, type };
		setTimeout(() => {
			alert = null;
		}, 4000);
	};

	const maskPassword = (pwd) => {
		if (!pwd) return '(no configurada)';
		return '*'.repeat(Math.min(pwd.length, 12));
	};
</script>

<div class="smtp-container">
	{#if alert}
		<div class="alert alert-{alert.type}">
			{alert.message}
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Cargando configuración SMTP...</p>
		</div>
	{:else}
		<div class="smtp-status">
			<div class="status-card">
				<h4>📊 Estado SMTP</h4>
				<div class="status-grid">
					<div class="status-item">
						<span class="label">Host:</span>
						<span class="value">{smtpConfig.host || 'No configurado'}</span>
					</div>
					<div class="status-item">
						<span class="label">Puerto:</span>
						<span class="value">{smtpConfig.port || '-'}</span>
					</div>
					<div class="status-item">
						<span class="label">Usuario:</span>
						<span class="value">{smtpConfig.username || 'No configurado'}</span>
					</div>
					<div class="status-item">
						<span class="label">Password:</span>
						<span class="value">
							{#if showPassword}
								{smtpConfig.password || '(vacío)'}
							{:else}
								{maskPassword(smtpConfig.password)}
							{/if}
							<button
								class="btn-icon"
								on:click={() => (showPassword = !showPassword)}
								title="Toggle visibility"
							>
								{showPassword ? '👁️' : '👁️‍🗨️'}
							</button>
						</span>
					</div>
					<div class="status-item">
						<span class="label">De (Email):</span>
						<span class="value">{smtpConfig.from_email || 'No configurado'}</span>
					</div>
					<div class="status-item">
						<span class="label">De (Nombre):</span>
						<span class="value">{smtpConfig.from_name || 'No configurado'}</span>
					</div>
				</div>
			</div>

			<div class="action-buttons">
				<button class="btn btn-primary" on:click={() => (editMode = !editMode)}>
					{editMode ? '❌ Cancelar' : '✏️ Editar Configuración'}
				</button>
				<button class="btn btn-secondary" on:click={getSmtpStatus} disabled={loading}>
					ℹ️ Verificar Estado
				</button>
				<button class="btn btn-success" on:click={testSmtp} disabled={testing || loading}>
					{testing ? '⏳ Probando...' : '🧪 Probar Conexión'}
				</button>
			</div>
		</div>

		{#if editMode}
			<div class="edit-form">
				<h4>✏️ Editar Configuración SMTP</h4>

				<div class="form-group">
					<label for="host">Host SMTP</label>
					<input
						id="host"
						type="text"
						bind:value={formData.host}
						placeholder="smtp.gmail.com"
					/>
				</div>

				<div class="form-group">
					<label for="port">Puerto</label>
					<input id="port" type="number" bind:value={formData.port} min="1" max="65535" />
				</div>

				<div class="form-group">
					<label for="username">Usuario</label>
					<input
						id="username"
						type="text"
						bind:value={formData.username}
						placeholder="tu-email@gmail.com"
					/>
				</div>

				<div class="form-group">
					<label for="password">Contraseña</label>
					<div class="password-input">
						<input
							id="password"
							type={showPassword ? 'text' : 'password'}
							bind:value={formData.password}
							placeholder="Contraseña SMTP"
						/>
						<button class="btn-icon" on:click={() => (showPassword = !showPassword)}>
							{showPassword ? '👁️' : '👁️‍🗨️'}
						</button>
					</div>
				</div>

				<div class="form-group">
					<label for="from_email">Email De</label>
					<input
						id="from_email"
						type="email"
						bind:value={formData.from_email}
						placeholder="noreply@empresa.com"
					/>
				</div>

				<div class="form-group">
					<label for="from_name">Nombre De</label>
					<input
						id="from_name"
						type="text"
						bind:value={formData.from_name}
						placeholder="Nombre de la Empresa"
					/>
				</div>

				<div class="form-actions">
					<button class="btn btn-primary" on:click={updateSmtpConfig}> 💾 Guardar Cambios </button>
					<button class="btn btn-secondary" on:click={cancelEdit}> ❌ Cancelar </button>
				</div>
			</div>
		{/if}

		<div class="help-section">
			<h4>📚 Ayuda: Configuración SMTP</h4>
			<ul>
				<li>
					<strong>Gmail:</strong> host=smtp.gmail.com, port=587, requiere contraseña de aplicación
				</li>
				<li>
					<strong>Outlook:</strong> host=smtp-mail.outlook.com, port=587
				</li>
				<li>
					<strong>SendGrid:</strong> host=smtp.sendgrid.net, port=587, usuario=apikey
				</li>
				<li>
					<strong>Nota:</strong> Siempre prueba la conexión después de cambios
				</li>
			</ul>
		</div>
	{/if}
</div>

<style>
	.smtp-container {
		padding: 20px;
		background: #0d1e35;
		border-radius: 8px;
	}

	.loading {
		text-align: center;
		padding: 40px 20px;
	}

	.spinner {
		border: 4px solid #e5e7eb;
		border-top-color: #00FF9F;
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
		color: #00FF9F;
		border-left: 4px solid #22c55e;
	}

	.alert-error {
		background: #fee2e2;
		color: #f87171;
		border-left: 4px solid #ef4444;
	}

	.alert-info {
		background: #dbeafe;
		color: #93c5fd;
		border-left: 4px solid #3b82f6;
	}

	.smtp-status {
		margin-bottom: 20px;
	}

	.status-card {
		background: linear-gradient(135deg, #0a1e38 0%, #003B73 100%);
		color: white;
		padding: 20px;
		border-radius: 8px;
		margin-bottom: 15px;
		border: 1px solid rgba(0, 255, 159, 0.12);
	}

	.status-card h4 {
		margin: 0 0 15px 0;
		font-size: 16px;
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 15px;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}

	.label {
		font-size: 12px;
		font-weight: 600;
		opacity: 0.85;
		text-transform: uppercase;
	}

	.value {
		font-size: 14px;
		display: flex;
		align-items: center;
		gap: 8px;
		word-break: break-all;
	}

	.btn-icon {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		font-size: 14px;
	}

	.action-buttons {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
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

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-primary {
		background: #003B73;
		color: #00FF9F;
		border: 1px solid rgba(0, 255, 159, 0.25);
	}

	.btn-primary:hover:not(:disabled) {
		background: #004d99;
		box-shadow: 0 4px 16px rgba(0, 255, 159, 0.2);
	}

	.btn-secondary {
		background: rgba(255,255,255,0.06);
		color: #a0b0c8;
		border: 1px solid rgba(255,255,255,0.1);
	}

	.btn-secondary:hover:not(:disabled) {
		background: rgba(255,255,255,0.1);
	}

	.btn-success {
		background: rgba(0, 255, 159, 0.1);
		color: #00FF9F;
		border: 1px solid rgba(0, 255, 159, 0.2);
	}

	.btn-success:hover:not(:disabled) {
		background: rgba(0, 255, 159, 0.2);
		box-shadow: 0 4px 12px rgba(0, 255, 159, 0.2);
	}

	.edit-form {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 20px;
		margin-bottom: 20px;
	}

	.edit-form h4 {
		margin: 0 0 15px 0;
		color: #c8d3e8;
	}

	.form-group {
		margin-bottom: 15px;
	}

	.form-group label {
		display: block;
		margin-bottom: 6px;
		font-size: 14px;
		font-weight: 600;
		color: #a0b0c8;
	}

	.form-group input {
		width: 100%;
		padding: 10px 12px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 14px;
		box-sizing: border-box;
	}

	.form-group input:focus {
		outline: none;
		border-color: #00FF9F;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.password-input {
		display: flex;
		gap: 10px;
		align-items: center;
	}

	.password-input input {
		flex: 1;
		margin: 0;
	}

	.form-actions {
		display: flex;
		gap: 10px;
		margin-top: 20px;
	}

	.help-section {
		background: rgba(251, 191, 36, 0.06);
		border: 1px solid rgba(251, 191, 36, 0.2);
		padding: 15px;
		margin-top: 20px;
	}

	.help-section h4 {
		margin: 0 0 10px 0;
		color: #fbbf24;
		font-size: 14px;
	}

	.help-section ul {
		margin: 0;
		padding-left: 20px;
		font-size: 13px;
		color: #f59e0b;
	}

	.help-section li {
		margin-bottom: 6px;
	}
</style>
