<script>
	import { onMount } from 'svelte';

	export let value = '';
	export let variables = {};

	let editorContainer;
	let quill;
	let showVariables = false;
	let variableList = Object.keys(variables);

	onMount(async () => {
		// Importar Quill dinámicamente
		const QuillModule = await import('quill');
		const Quill = QuillModule.default;

		quill = new Quill(editorContainer, {
			theme: 'snow',
			modules: {
				toolbar: [
					['bold', 'italic', 'underline', 'strike'],
					['blockquote', 'code-block'],
					[{ header: 1 }, { header: 2 }],
					[{ list: 'ordered' }, { list: 'bullet' }],
					[{ color: [] }, { background: [] }],
					[{ align: [] }],
					['link', 'image'],
					['clean']
				]
			},
			placeholder: 'Escribe tu contenido HTML aquí...'
		});

		// Establecer contenido inicial
		if (value) {
			quill.root.innerHTML = value;
		}

		// Actualizar valor cuando cambia el editor
		quill.on('text-change', () => {
			value = quill.root.innerHTML;
		});
	});

	const insertVariable = (varName) => {
		if (quill) {
			const range = quill.getSelection();
			quill.insertText(range.index, `{{${varName}}}`);
			quill.setSelection(range.index + varName.length + 4);
		}
	};

	const insertTemplate = (templateName) => {
		if (quill) {
			const templates = {
				header: `<table style="width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px;">
					<tr><td><h1>{{company_name}}</h1></td></tr>
				</table>`,
				footer: `<table style="width: 100%; background: #f3f4f6; color: #6b7280; padding: 20px; text-align: center; font-size: 12px;">
					<tr><td>© {{year}} {{company_name}}. Todos los derechos reservados.</td></tr>
				</table>`,
				alert_box: `<div style="background: #fef08a; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
					<strong>⚠️ Alerta:</strong> {{message}}
				</div>`,
				button: `<a href="{{link}}" style="display: inline-block; background: #667eea; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">{{button_text}}</a>`,
				table_header: `<table style="width: 100%; border-collapse: collapse;">
					<thead style="background: #f3f4f6;">
						<tr>
							<th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Columna 1</th>
							<th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Columna 2</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{{content1}}</td>
							<td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{{content2}}</td>
						</tr>
					</tbody>
				</table>`
			};

			if (templates[templateName]) {
				const range = quill.getSelection();
				quill.root.innerHTML += templates[templateName];
				quill.setSelection(quill.getLength());
			}
		}
	};
</script>

<div class="editor-wrapper">
	<div class="editor-toolbar">
		<div class="toolbar-section">
			<span class="toolbar-label">Insertar Variable:</span>
			<div class="variable-buttons">
				{#each variableList as varName}
					<button
						class="btn-variable"
						on:click={() => insertVariable(varName)}
						title={`Insertar {{${varName}}}`}
					>
						{{{varName}}}
					</button>
				{/each}
				{#if variableList.length === 0}
					<span class="no-variables">No hay variables definidas</span>
				{/if}
			</div>
		</div>

		<div class="toolbar-section">
			<span class="toolbar-label">Insertar Template:</span>
			<select class="template-select" on:change={(e) => insertTemplate(e.target.value)}>
				<option value="">Selecciona un template...</option>
				<option value="header">Encabezado</option>
				<option value="footer">Pie de página</option>
				<option value="alert_box">Caja de Alerta</option>
				<option value="button">Botón</option>
				<option value="table_header">Tabla</option>
			</select>
		</div>

		<button
			class="btn-toggle-variables"
			on:click={() => (showVariables = !showVariables)}
		>
			📋 {showVariables ? 'Ocultar' : 'Ver'} Variables
		</button>
	</div>

	{#if showVariables && variableList.length > 0}
		<div class="variables-info">
			<h4>Variables disponibles:</h4>
			<ul>
				{#each Object.entries(variables) as [key, type]}
					<li>
						<code>{{{{key}}}}</code>
						<span class="var-type">({type})</span>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<div class="quill-container" bind:this={editorContainer} />

	<div class="editor-info">
		<small>✓ Soporta HTML enriquecido con variables {{variable_name}}</small>
	</div>
</div>

<style>
	:global(.ql-container) {
		font-size: 14px;
		font-family: inherit;
	}

	:global(.ql-editor) {
		min-height: 300px;
		max-height: 500px;
		overflow-y: auto;
		padding: 12px;
	}

	:global(.ql-toolbar) {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px 6px 0 0;
	}

	:global(.ql-editor.ql-blank::before) {
		color: #d1d5db;
		font-style: italic;
	}

	.editor-wrapper {
		border-radius: 8px;
		overflow: hidden;
		border: 1px solid #e5e7eb;
	}

	.editor-toolbar {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		padding: 15px;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.toolbar-section {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}

	.toolbar-label {
		font-weight: 600;
		font-size: 12px;
		color: #4b5563;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.variable-buttons {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
	}

	.btn-variable {
		padding: 6px 10px;
		background: #dbeafe;
		color: #1e40af;
		border: 1px solid #93c5fd;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
		font-weight: 600;
		font-family: monospace;
		transition: all 0.2s;
	}

	.btn-variable:hover {
		background: #93c5fd;
		border-color: #3b82f6;
	}

	.no-variables {
		font-size: 12px;
		color: #9ca3af;
		font-style: italic;
	}

	.template-select {
		padding: 6px 10px;
		border: 1px solid #d1d5db;
		border-radius: 4px;
		font-size: 12px;
		background: white;
		cursor: pointer;
		transition: all 0.2s;
	}

	.template-select:hover {
		border-color: #667eea;
		background: #f9fafb;
	}

	.template-select:focus {
		outline: none;
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.btn-toggle-variables {
		padding: 6px 12px;
		background: #667eea;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
		font-weight: 600;
		transition: all 0.2s;
		width: fit-content;
	}

	.btn-toggle-variables:hover {
		background: #5568d3;
	}

	.variables-info {
		background: #eff6ff;
		border-left: 4px solid #3b82f6;
		padding: 12px 15px;
		margin: 0;
	}

	.variables-info h4 {
		margin: 0 0 8px 0;
		font-size: 13px;
		color: #1e40af;
	}

	.variables-info ul {
		margin: 0;
		padding-left: 20px;
		list-style: none;
	}

	.variables-info li {
		font-size: 12px;
		color: #1e40af;
		margin: 4px 0;
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.variables-info code {
		background: #dbeafe;
		padding: 2px 6px;
		border-radius: 3px;
		font-family: monospace;
	}

	.var-type {
		color: #6b7280;
		font-size: 11px;
	}

	.quill-container {
		background: white;
	}

	.editor-info {
		padding: 8px 12px;
		background: #f9fafb;
		border-top: 1px solid #e5e7eb;
		color: #6b7280;
		font-size: 12px;
	}

	@media (max-width: 768px) {
		.editor-toolbar {
			flex-direction: column;
		}

		.toolbar-section {
			width: 100%;
		}

		.variable-buttons {
			width: 100%;
		}

		:global(.ql-editor) {
			min-height: 250px;
		}
	}
</style>
