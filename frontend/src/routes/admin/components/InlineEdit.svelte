<script>
	import { createEventDispatcher } from 'svelte';

	export let value = '';
	export let placeholder = '';
	export let editable = true;

	let isEditing = false;
	let editValue = value;
	let inputElement;

	const dispatch = createEventDispatcher();

	const startEdit = () => {
		if (!editable) return;
		isEditing = true;
		editValue = value;
		setTimeout(() => inputElement?.focus(), 0);
	};

	const saveEdit = () => {
		value = editValue;
		isEditing = false;
		dispatch('change', value);
	};

	const cancelEdit = () => {
		isEditing = false;
		editValue = value;
	};

	const handleKeydown = (e) => {
		if (e.key === 'Enter') {
			saveEdit();
		} else if (e.key === 'Escape') {
			cancelEdit();
		}
	};

	$: if (!isEditing) {
		editValue = value;
	}
</script>

<div class="inline-edit">
	{#if isEditing}
		<input
			bind:this={inputElement}
			type="text"
			bind:value={editValue}
			{placeholder}
			class="inline-input"
			on:blur={saveEdit}
			on:keydown={handleKeydown}
		/>
	{:else}
		<div class="inline-text" on:click={startEdit} role="button" tabindex="0">
			{value || <span class="placeholder">{placeholder}</span>}
		</div>
	{/if}
</div>

<style>
	.inline-edit {
		width: 100%;
	}

	.inline-text {
		padding: 10px 12px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
		min-height: 38px;
		display: flex;
		align-items: center;
		user-select: none;
	}

	.inline-text:hover {
		border-color: #667eea;
		background: #f9fafb;
	}

	.placeholder {
		color: #d1d5db;
		font-style: italic;
	}

	.inline-input {
		padding: 10px 12px;
		border: 2px solid #667eea;
		border-radius: 6px;
		font-size: 14px;
		font-family: inherit;
		width: 100%;
		box-sizing: border-box;
	}

	.inline-input:focus {
		outline: none;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}
</style>
