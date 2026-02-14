<script lang="ts">
  import Badge from './Badge.svelte';
  import Spinner from './Spinner.svelte';

  type BadgeVariant =
    | 'success'
    | 'warning'
    | 'error'
    | 'info'
    | 'primary'
    | 'accent'
    | 'secondary'
    | 'basic'
    | 'pro'
    | 'enterprise';

  interface Column {
    key: string;
    label: string;
    type?: 'text' | 'badge' | 'date' | 'actions' | 'boolean';
    badgeColors?: Record<string, BadgeVariant>;
    sortable?: boolean;
  }

  export let columns: Column[] = [];
  export let data: Record<string, unknown>[] = [];
  export let loading: boolean = false;
  export let emptyMessage: string = 'No hay datos disponibles';
  export let onRowClick: ((row: Record<string, unknown>) => void) | null = null;
  export let actions: { label: string; onClick: (row: Record<string, unknown>) => void; variant?: string }[] = [];

  let sortBy: string | null = null;
  let sortDir: 'asc' | 'desc' = 'asc';

  function toggleSort(column: Column) {
    if (!column.sortable) return;

    if (sortBy === column.key) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      return;
    }

    sortBy = column.key;
    sortDir = 'asc';
  }

  function formatDate(value: unknown): string {
    if (!value || typeof value !== 'string') return '-';
    try {
      const date = new Date(value);
      return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return value;
    }
  }

  function getValue(row: Record<string, unknown>, key: string): unknown {
    return key.split('.').reduce<unknown>((obj, part) => {
      if (obj && typeof obj === 'object' && part in obj) {
        return (obj as Record<string, unknown>)[part];
      }
      return undefined;
    }, row);
  }

  function normalizeBadgeVariant(value: unknown, map?: Record<string, BadgeVariant>): BadgeVariant {
    if (typeof value === 'string' && map && map[value]) {
      return map[value];
    }
    return 'secondary';
  }

  $: sortedData =
    sortBy === null
      ? data
      : [...data].sort((a, b) => {
          const sortKey = sortBy as string;
          const aVal = getValue(a, sortKey) ?? '';
          const bVal = getValue(b, sortKey) ?? '';
          const cmp = String(aVal).localeCompare(String(bVal));
          return sortDir === 'asc' ? cmp : -cmp;
        });
</script>

<div class="overflow-x-auto">
  <table class="min-w-full divide-y divide-surface-border">
    <thead class="bg-surface-highlight/30">
      <tr>
        {#each columns as column}
          <th
            class="px-6 py-3 text-left text-xs font-medium text-secondary-400 uppercase tracking-wider"
            class:cursor-pointer={column.sortable}
            class:hover:bg-surface-highlight={column.sortable}
            on:click={() => toggleSort(column)}
          >
            <div class="flex items-center gap-1">
              {column.label}
              {#if column.sortable}
                <span class="text-secondary-500">
                  {#if sortBy === column.key}
                    {sortDir === 'asc' ? '↑' : '↓'}
                  {:else}
                    ↕
                  {/if}
                </span>
              {/if}
            </div>
          </th>
        {/each}

        {#if actions.length > 0}
          <th class="px-6 py-3 text-right text-xs font-medium text-secondary-400 uppercase tracking-wider">
            Acciones
          </th>
        {/if}
      </tr>
    </thead>

    <tbody class="bg-surface-card divide-y divide-surface-border">
      {#if loading}
        <tr>
          <td colspan={columns.length + (actions.length > 0 ? 1 : 0)} class="px-6 py-12 text-center">
            <Spinner size="lg" />
            <p class="mt-2 text-secondary-400">Cargando...</p>
          </td>
        </tr>
      {:else if sortedData.length === 0}
        <tr>
          <td colspan={columns.length + (actions.length > 0 ? 1 : 0)} class="px-6 py-12 text-center text-secondary-500">
            {emptyMessage}
          </td>
        </tr>
      {:else}
        {#each sortedData as row}
          <tr
            class={`${
              onRowClick ? 'hover:bg-surface-highlight/50 cursor-pointer' : ''
            }`}
            on:click={() => onRowClick?.(row)}
          >
            {#each columns as column}
              <td class="px-6 py-4 whitespace-nowrap">
                {#if column.type === 'badge'}
                  {@const value = getValue(row, column.key)}
                  <Badge variant={normalizeBadgeVariant(value, column.badgeColors)}>{String(value ?? '-')}</Badge>
                {:else if column.type === 'date'}
                  <span class="text-sm text-secondary-300">{formatDate(getValue(row, column.key))}</span>
                {:else if column.type === 'boolean'}
                  {@const value = Boolean(getValue(row, column.key))}
                  <span class="inline-flex items-center">
                    {#if value}
                      <svg class="w-5 h-5 text-accent-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                    {:else}
                      <svg class="w-5 h-5 text-secondary-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                      </svg>
                    {/if}
                  </span>
                {:else}
                  <span class="text-sm text-secondary-100">{String(getValue(row, column.key) ?? '-')}</span>
                {/if}
              </td>
            {/each}

            {#if actions.length > 0}
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex justify-end gap-2">
                  {#each actions as action}
                    <button
                      type="button"
                      class="text-primary-400 hover:text-primary-300 transition-colors"
                      class:text-error={action.variant === 'danger'}
                      on:click|stopPropagation={() => action.onClick(row)}
                    >
                      {action.label}
                    </button>
                  {/each}
                </div>
              </td>
            {/if}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
