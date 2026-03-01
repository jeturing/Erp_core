<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let variables = {};
	export let onSelect = null;

	let searchTerm = '';
	let filteredVariables = [];
	let showList = false;

	$: {
		if (searchTerm) {
			filteredVariables = Object.entries(variables)
				.filter(
					([name]) =>
						name.toLowerCase().includes(searchTerm.toLowerCase()) ||
						variables[name]?.toLowerCase?.().includes(searchTerm.toLowerCase())
				)
				.map(([name, type]) => ({ name, type }));
		} else {
			filteredVariables = Object.entries(variables).map(([name, type]) => ({ name, type }));
		}
	}

	const selectVariable = (variableName) => {
		const variable = `{{${variableName}}}`;
		dispatch('select', variable);

		if (onSelect) {
			onSelect(variable);
		}

		searchTerm = '';
		showList = false;
	};

	const getTypeColor = (type) => {
		const colors = {
			string: '#3b82f6',
			number: '#ef4444',
			float: '#f59e0b',
			date: '#10b981',
			boolean: '#8b5cf6'
		};
		return colors[type] || '#6b7280';
	};

	const getTypeIcon = (type) => {
		const icons = {
			string: '📝',
			number: '#️⃣',
			float: '🔢',
			date: '📅',
			boolean: '✓'
		};
		return icons[type] || '❓';
	};
</script>

<div class="variable-picker">
	<div class="search-container">
		<input
			type="text"
			placeholder="🔍 Buscar variables..."
			bind:value={searchTerm}
			on:focus={() => (showList = true)}
			class="search-input"
		/>
	</div>

	{#if showList && filteredVariables.length > 0}
		<div class="variables-dropdown">
			{#each filteredVariables as variable (variable.name)}
				<button
					class="variable-option"
					on:click={() => selectVariable(variable.name)}
					title={`Type: ${variable.type}`}
				>
					<span class="var-icon">{getTypeIcon(variable.type)}</span>
					<span class="var-name">{variable.name}</span>
					<span
						class="var-type"
						style="border-color: {getTypeColor(variable.type)}; color: {getTypeColor(variable.type)}"
					>
						{variable.type}
					</span>
				</button>
			{/each}
		</div>
	{:else if showList && filteredVariables.length === 0 && searchTerm}
		<div class="no-results">
			<span>❌ No se encontraron variables</span>
		</div>
	{/if}

	{#if !showList && filteredVariables.length > 0}
		<div class="variable-list-compact">
			<div class="list-title">Variables disponibles:</div>
			<div class="tags">
				{#each Object.entries(variables) as [name, type]}
					<button
						class="tag"
						on:click={() => selectVariable(name)}
						title={`Inserta {{${name}}} - Tipo: ${type}`}
					>
						{getTypeIcon(type)} {name}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.variable-picker {
		margin-top: 10px;
	}

	.search-container {
		display: flex;
		gap: 10px;
		margin-bottom: 10px;
	}

	.search-input {
		flex: 1;
		padding: 8px 12px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 14px;
		transition: all 0.2s;
	}

	.search-input:focus {
		outline: none;
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.variables-dropdown {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		max-height: 300px;
		overflow-y: auto;
		position: absolute;
		z-index: 10;
		min-width: 300px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.variable-option {
		display: flex;
		align-items: center;
		gap: 12px;
		width: 100%;
		padding: 12px;
		border: none;
		background: transparent;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s;
		border-bottom: 1px solid #f3f4f6;
	}

	.variable-option:last-child {
		border-bottom: none;
	}

	.variable-option:hover {
		background: #f9fafb;
	}

	.var-icon {
		font-size: 16px;
	}

	.var-name {
		flex: 1;
		font-weight: 600;
		color: #1f2937;
		font-size: 14px;
	}

	.var-type {
		font-size: 11px;
		padding: 2px 8px;
		border: 1px solid;
		border-radius: 3px;
		font-weight: 600;
		white-space: nowrap;
	}

	.no-results {
		padding: 20px;
		text-align: center;
		color: #6b7280;
		font-size: 14px;
	}

	.variable-list-compact {
		padding: 12px;
		background: #f0f9ff;
		border: 1px solid #bfdbfe;
		border-radius: 6px;
	}

	.list-title {
		font-size: 12px;
		font-weight: 600;
		color: #1e40af;
		margin-bottom: 8px;
		text-transform: uppercase;
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.tag {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 4px 8px;
		background: white;
		border: 1px solid #bfdbfe;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
		font-weight: 500;
		color: #1e40af;
		transition: all 0.2s;
	}

	.tag:hover {
		background: #dbeafe;
		border-color: #667eea;
	}
</style>
