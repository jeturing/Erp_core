<script>
	import { onMount } from 'svelte';

	export let html = '';
	export let variables = {};

	let previewHtml = '';
	let variableCount = 0;

	onMount(() => {
		updatePreview();
	});

	const updatePreview = () => {
		previewHtml = html;
		variableCount = (html.match(/\{\{[^}]+\}\}/g) || []).length;
	};

	$: if (html) updatePreview();

	const insertTestData = () => {
		let testData = {};
		for (const [key, type] of Object.entries(variables)) {
			switch (type) {
				case 'number':
					testData[key] = Math.floor(Math.random() * 100);
					break;
				case 'float':
					testData[key] = (Math.random() * 100).toFixed(2);
					break;
				case 'date':
					testData[key] = new Date().toLocaleDateString('es-ES');
					break;
				case 'boolean':
					testData[key] = Math.random() > 0.5 ? 'Sí' : 'No';
					break;
				default:
					testData[key] = `Valor de ${key}`;
			}
		}

		let preview = html;
		for (const [key, value] of Object.entries(testData)) {
			preview = preview.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
		}

		// Reemplazar variables no encontradas
		preview = preview.replace(/\{\{[^}]+\}\}/g, '[variable]');

		previewHtml = preview;
	};
</script>

<div class="preview-container">
	<div class="preview-controls">
		<h4>📧 Vista Previa del Email</h4>
		<button class="btn btn-small btn-primary" on:click={insertTestData}>
			📊 Llenar con Datos de Prueba
		</button>
		{#if variableCount > 0}
			<span class="variable-count">Variables pendientes: {variableCount}</span>
		{/if}
	</div>

	<div class="preview-frame">
		<iframe
			title="Email Preview"
			sandbox="allow-same-origin"
			srcdoc="<!DOCTYPE html><html><head><meta charset='UTF-8'><style>
				body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f3f4f6; }
				.email { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }
				.email-body { padding: 20px; }
				img { max-width: 100%; height: auto; }
				a { color: #667eea; text-decoration: none; }
				a:hover { text-decoration: underline; }
				table { width: 100%; border-collapse: collapse; }
				.footer { background: #f9fafb; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }
			</style></head><body><div class='email'><div class='email-body'>{previewHtml}</div></div></body></html>"
		/>
	</div>

	<div class="preview-info">
		<p>💡 Vista previa en iframe. Las imágenes externas pueden no cargarse.</p>
		{#if variableCount > 0}
			<p class="warning">
				⚠️ Variables sin reemplazar detectadas. Usa "Llenar con Datos de Prueba" para verlas con contenido.
			</p>
		{/if}
	</div>
</div>

<style>
	.preview-container {
		margin-top: 20px;
	}

	.preview-controls {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 15px;
		padding-bottom: 12px;
		border-bottom: 1px solid #e5e7eb;
	}

	.preview-controls h4 {
		margin: 0;
		font-size: 14px;
		color: #1f2937;
		flex: 1;
	}

	.variable-count {
		font-size: 12px;
		color: #f59e0b;
		background: #fef3c7;
		padding: 4px 8px;
		border-radius: 4px;
	}

	.preview-frame {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		overflow: hidden;
		height: 400px;
		margin-bottom: 12px;
	}

	.preview-frame iframe {
		width: 100%;
		height: 100%;
		border: none;
	}

	.preview-info {
		font-size: 12px;
		color: #6b7280;
		padding: 12px;
		background: #f9fafb;
		border-radius: 6px;
	}

	.preview-info p {
		margin: 4px 0;
	}

	.warning {
		color: #f59e0b;
		background: #fef3c7;
		padding: 8px;
		border-radius: 4px;
		margin: 8px 0 0 0;
	}

	.btn {
		padding: 6px 12px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
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
</style>
