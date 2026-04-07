<script>
	import { onMount } from 'svelte';
	import RichTextEditor from './RichTextEditor.svelte';
	import InlineEdit from './InlineEdit.svelte';
	import TemplatePreview from './TemplatePreview.svelte';

	export let baseUrl = '';
	export let getHeaders = () => ({});

	let templates = [];
	let selectedTemplate = null;
	let showCreateForm = false;
	let loading = false;
	let error = null;
	let success = null;

	const templateTypes = [
		'storage_warning',
		'storage_critical',
		'storage_exceeded',
		'welcome',
		'plan_upgrade',
		'invoice',
		'password_reset',
		'account_suspended',
		'billing_alert',
		'custom'
	];

	// Form para crear/editar
	let formData = {
		template_type: '',
		name: '',
		subject: '',
		html_body: '',
		text_body: '',
		preview_text: '',
		tags: [],
		variables: {}
	};

	let tagInput = '';
	let variableKey = '';
	let variableType = 'string';

	onMount(async () => {
		await loadTemplates();
	});

	const loadTemplates = async () => {
		try {
			loading = true;
			error = null;
			const response = await fetch(`${baseUrl}/email-templates`, {
				headers: getHeaders()
			});
			const data = await response.json();
			templates = data.data || [];
		} catch (e) {
			error = 'Error cargando templates: ' + e.message;
			console.error(e);
		} finally {
			loading = false;
		}
	};

	const handleSelectTemplate = (template) => {
		selectedTemplate = template;
		formData = { ...template };
	};

	const handleCreateNew = () => {
		showCreateForm = true;
		selectedTemplate = null;
		formData = {
			template_type: '',
			name: '',
			subject: '',
			html_body: '',
			text_body: '',
			preview_text: '',
			tags: [],
			variables: {}
		};
	};

	const handleAddTag = () => {
		if (tagInput.trim() && !formData.tags.includes(tagInput)) {
			formData.tags = [...formData.tags, tagInput];
			tagInput = '';
		}
	};

	const handleRemoveTag = (tag) => {
		formData.tags = formData.tags.filter((t) => t !== tag);
	};

	const handleAddVariable = () => {
		if (variableKey.trim()) {
			formData.variables = {
				...formData.variables,
				[variableKey]: variableType
			};
			variableKey = '';
			variableType = 'string';
		}
	};

	const handleRemoveVariable = (key) => {
		const { [key]: _, ...rest } = formData.variables;
		formData.variables = rest;
	};

	const handleSaveTemplate = async () => {
		try {
			loading = true;
			error = null;
			success = null;

			if (!formData.template_type || !formData.name || !formData.subject || !formData.html_body) {
				error = 'Por favor completa todos los campos requeridos';
				return;
			}

			const method = selectedTemplate ? 'PUT' : 'POST';
			const url = selectedTemplate
				? `${baseUrl}/email-templates/${formData.template_type}`
				: `${baseUrl}/email-templates`;

			const response = await fetch(url, {
				method,
				headers: getHeaders(),
				body: JSON.stringify(formData)
			});

			const data = await response.json();

			if (data.success) {
				success = data.message || 'Template guardado correctamente';
				await loadTemplates();
				showCreateForm = false;
				selectedTemplate = null;
				setTimeout(() => (success = null), 3000);
			} else {
				error = data.message || 'Error al guardar template';
			}
		} catch (e) {
			error = 'Error: ' + e.message;
		} finally {
			loading = false;
		}
	};

	const handleCancel = () => {
		showCreateForm = false;
		selectedTemplate = null;
	};

	const handleToggleTemplate = async (template) => {
		try {
			loading = true;
			const response = await fetch(`${baseUrl}/email-templates/${template.template_type}/toggle`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({ is_active: !template.is_active })
			});

			const data = await response.json();
			if (data.success) {
				await loadTemplates();
			}
		} catch (e) {
			error = 'Error: ' + e.message;
		} finally {
			loading = false;
		}
	};

	const handleDeleteTemplate = async (template) => {
		if (!confirm(`¿Eliminar template ${template.template_type}?`)) return;

		try {
			loading = true;
			// Desactivar en lugar de eliminar
			const response = await fetch(`${baseUrl}/email-templates/${template.template_type}/toggle`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({ is_active: false })
			});

			const data = await response.json();
			if (data.success) {
				await loadTemplates();
			}
		} catch (e) {
			error = 'Error: ' + e.message;
		} finally {
			loading = false;
		}
	};
</script>

<div class="template-manager">
	<div class="manager-header">
		<h2>📝 Gestión de Email Templates</h2>
		<button class="btn btn-primary" on:click={handleCreateNew} disabled={loading}>
			➕ Crear Template
		</button>
	</div>

	{#if error}
		<div class="alert alert-error">{error}</div>
	{/if}

	{#if success}
		<div class="alert alert-success">{success}</div>
	{/if}

	<div class="templates-grid">
		{#if loading && templates.length === 0}
			<div class="loading">Cargando templates...</div>
		{:else if templates.length === 0}
			<div class="empty-state">
				<p>No hay templates. ¡Crea uno para comenzar!</p>
				<button class="btn btn-primary" on:click={handleCreateNew}>Crear Template</button>
			</div>
		{:else}
			<div class="templates-list">
				{#each templates as template (template.template_type)}
					<div class="template-card {selectedTemplate?.template_type === template.template_type ? 'active' : ''}">
						<div class="card-header">
							<h3>{template.name}</h3>
							<span class="badge {template.is_active ? 'active' : 'inactive'}">
								{template.is_active ? '✓ Activo' : '✗ Inactivo'}
							</span>
						</div>
						<div class="card-body">
							<p class="type-label">Tipo: <code>{template.template_type}</code></p>
							<p class="version-label">v{template.version}</p>
						</div>
						<div class="card-footer">
							<button
								class="btn btn-small btn-primary"
								on:click={() => handleSelectTemplate(template)}
								disabled={loading}
							>
								✎ Editar
							</button>
							<button
								class="btn btn-small {template.is_active ? 'btn-warning' : 'btn-success'}"
								on:click={() => handleToggleTemplate(template)}
								disabled={loading}
							>
								{template.is_active ? '🔒 Desactivar' : '🔓 Activar'}
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	{#if showCreateForm || selectedTemplate}
		<div class="form-container">
			<div class="form-header">
				<h3>{selectedTemplate ? `Editar: ${selectedTemplate.name}` : 'Crear Nuevo Template'}</h3>
				<button class="btn-close" on:click={handleCancel}>✕</button>
			</div>

			<div class="form-content">
				<div class="form-row">
					<div class="form-group">
						<label>Tipo de Template *</label>
						{#if selectedTemplate}
							<input type="text" value={formData.template_type} disabled class="input-disabled" />
						{:else}
							<select bind:value={formData.template_type} class="input-field">
								<option value="">Selecciona un tipo...</option>
								{#each templateTypes as type}
									<option value={type}>{type}</option>
								{/each}
							</select>
						{/if}
					</div>

					<div class="form-group">
						<label>Nombre del Template *</label>
						<InlineEdit bind:value={formData.name} />
					</div>
				</div>

				<div class="form-group">
					<label>Asunto del Email *</label>
					<InlineEdit bind:value={formData.subject} placeholder="Ej: 🟡 Alerta - {'{{'}company_name{'}}'}" />
					<small>Puedes usar {'{{'}variables{'}}'} en el asunto</small>
				</div>

				<div class="form-group">
					<label>Contenido HTML *</label>
					<RichTextEditor bind:value={formData.html_body} variables={formData.variables} />
					<small>Editor enriquecido con soporte para {'{{'}variables{'}}'}</small>
				</div>

				<div class="form-row">
					<div class="form-group">
						<label>Texto Plano (alternativa)</label>
						<textarea
							bind:value={formData.text_body}
							class="textarea-field"
							placeholder="Versión en texto plano del email"
						/>
					</div>

					<div class="form-group">
						<label>Preview Text</label>
						<InlineEdit bind:value={formData.preview_text} placeholder="Resumen para clientes de email" />
					</div>
				</div>

				<div class="form-row">
					<div class="form-group">
						<label>Tags</label>
						<div class="tags-input">
							<input
								type="text"
								bind:value={tagInput}
								class="input-field"
								placeholder="Escribe un tag y presiona +"
							/>
							<button class="btn btn-small btn-secondary" on:click={handleAddTag}>+</button>
						</div>
						<div class="tags-display">
							{#each formData.tags as tag (tag)}
								<span class="tag">
									{tag}
									<button
										class="tag-remove"
										on:click={() => handleRemoveTag(tag)}
										type="button"
									>
										✕
									</button>
								</span>
							{/each}
						</div>
					</div>

					<div class="form-group">
						<label>Variables del Template</label>
						<div class="variables-input">
							<input
								type="text"
								bind:value={variableKey}
								class="input-field"
								placeholder="Nombre de variable"
							/>
							<select bind:value={variableType} class="input-field">
								<option value="string">string</option>
								<option value="number">number</option>
								<option value="float">float</option>
								<option value="date">date</option>
								<option value="boolean">boolean</option>
							</select>
							<button class="btn btn-small btn-secondary" on:click={handleAddVariable}>+</button>
						</div>
						<div class="variables-display">
							{#each Object.entries(formData.variables) as [key, type] (key)}
								<span class="variable">
									<code>{key}</code>
									<small>({type})</small>
									<button
										class="var-remove"
										on:click={() => handleRemoveVariable(key)}
										type="button"
									>
										✕
									</button>
								</span>
							{/each}
						</div>
					</div>
				</div>

				<div class="form-actions">
					<button class="btn btn-primary" on:click={handleSaveTemplate} disabled={loading}>
						{loading ? '⏳ Guardando...' : '💾 Guardar Template'}
					</button>
					<button class="btn btn-secondary" on:click={handleCancel} disabled={loading}>
						Cancelar
					</button>
				</div>
			</div>

			{#if formData.html_body}
				<div class="preview-section">
					<h4>📋 Preview del Template</h4>
					<TemplatePreview html={formData.html_body} variables={formData.variables} />
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.template-manager {
		padding: 20px;
	}

	.manager-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 30px;
	}

	.manager-header h2 {
		margin: 0;
		font-size: 22px;
		color: #c8d3e8;
	}

	.templates-grid {
		margin-bottom: 30px;
	}

	.templates-list {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 20px;
	}

	.template-card {
		background: #0d1e35;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 16px;
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
	}

	.template-card:hover {
		border-color: #00FF9F;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
	}

	.template-card.active {
		border-color: #00FF9F;
		background: #f3f4f6;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 12px;
	}

	.card-header h3 {
		margin: 0;
		font-size: 16px;
		color: #f0f4ff;
		flex: 1;
	}

	.badge {
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
	}

	.badge.active {
		background: #d1fae5;
		color: #00FF9F;
	}

	.badge.inactive {
		background: #fee2e2;
		color: #f87171;
	}

	.card-body {
		margin-bottom: 12px;
	}

	.type-label,
	.version-label {
		margin: 4px 0;
		font-size: 12px;
		color: #7a8fa6;
	}

	.card-footer {
		display: flex;
		gap: 8px;
	}

	.form-container {
		background: #091525;
		border-radius: 12px;
		padding: 30px;
		margin-top: 30px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
	}

	.form-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 25px;
		padding-bottom: 15px;
		border-bottom: 2px solid rgba(0, 0, 0, 0.1);
	}

	.form-header h3 {
		margin: 0;
		font-size: 20px;
		color: #c8d3e8;
	}

	.btn-close {
		background: none;
		border: none;
		font-size: 24px;
		cursor: pointer;
		color: #7a8fa6;
		padding: 0;
		width: 30px;
		height: 30px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: all 0.2s;
	}

	.btn-close:hover {
		background: rgba(0, 0, 0, 0.1);
		color: #f0f4ff;
	}

	.form-content {
		background: #0d1e35;
		padding: 25px;
		border-radius: 8px;
		margin-bottom: 20px;
	}

	.form-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 20px;
		margin-bottom: 20px;
	}

	.form-group {
		display: flex;
		flex-direction: column;
	}

	.form-group label {
		font-weight: 600;
		color: #c8d3e8;
		margin-bottom: 8px;
		font-size: 14px;
	}

	.form-group small {
		font-size: 12px;
		color: #7a8fa6;
		margin-top: 4px;
	}

	.input-field,
	.textarea-field,
	.input-disabled {
		padding: 10px 12px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 14px;
		font-family: inherit;
		transition: all 0.2s;
	}

	.input-field:focus,
	.textarea-field:focus {
		outline: none;
		border-color: #00FF9F;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.input-disabled {
		background: #f3f4f6;
		cursor: not-allowed;
	}

	.textarea-field {
		min-height: 100px;
		resize: vertical;
	}

	.tags-input {
		display: flex;
		gap: 8px;
		margin-bottom: 8px;
	}

	.tags-input input {
		flex: 1;
	}

	.tags-display {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.tag {
		background: #dbeafe;
		color: #93c5fd;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 12px;
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	.tag-remove {
		background: none;
		border: none;
		cursor: pointer;
		color: inherit;
		padding: 0;
		font-size: 12px;
		opacity: 0.7;
		transition: opacity 0.2s;
	}

	.tag-remove:hover {
		opacity: 1;
	}

	.variables-input {
		display: flex;
		gap: 8px;
		margin-bottom: 8px;
	}

	.variables-input input {
		flex: 1;
	}

	.variables-input select {
		flex: 0 0 100px;
	}

	.variables-display {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.variable {
		background: #fef08a;
		color: #f59e0b;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 12px;
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	.var-remove {
		background: none;
		border: none;
		cursor: pointer;
		color: inherit;
		padding: 0;
		font-size: 12px;
		opacity: 0.7;
		transition: opacity 0.2s;
	}

	.var-remove:hover {
		opacity: 1;
	}

	.form-actions {
		display: flex;
		gap: 12px;
		justify-content: center;
		margin-top: 20px;
	}

	.preview-section {
		background: #0d1e35;
		padding: 20px;
		border-radius: 8px;
		margin-top: 20px;
	}

	.preview-section h4 {
		margin-top: 0;
		font-size: 16px;
		color: #c8d3e8;
	}

	.alert {
		padding: 12px 16px;
		border-radius: 6px;
		margin-bottom: 20px;
		font-size: 14px;
	}

	.alert-error {
		background: #fee2e2;
		color: #f87171;
		border: 1px solid #fecaca;
	}

	.alert-success {
		background: #d1fae5;
		color: #00FF9F;
		border: 1px solid #a7f3d0;
	}

	.empty-state {
		text-align: center;
		padding: 40px;
		color: #7a8fa6;
	}

	.loading {
		text-align: center;
		padding: 40px;
		color: #7a8fa6;
	}

	.btn {
		padding: 10px 16px;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 600;
		transition: all 0.2s ease;
	}

	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-primary {
		background: #00FF9F;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: #5568d3;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.btn-secondary {
		background: #e5e7eb;
		color: #c8d3e8;
	}

	.btn-secondary:hover:not(:disabled) {
		background: #d1d5db;
	}

	.btn-warning {
		background: #fbbf24;
		color: #f59e0b;
	}

	.btn-warning:hover:not(:disabled) {
		background: #f59e0b;
	}

	.btn-success {
		background: #10b981;
		color: white;
	}

	.btn-success:hover:not(:disabled) {
		background: #059669;
	}

	.btn-small {
		padding: 6px 12px;
		font-size: 12px;
	}

	@media (max-width: 768px) {
		.templates-list {
			grid-template-columns: 1fr;
		}

		.form-container {
			padding: 20px;
		}

		.form-content {
			padding: 15px;
		}

		.form-row {
			grid-template-columns: 1fr;
		}

		.form-actions {
			flex-direction: column;
		}
	}
</style>
