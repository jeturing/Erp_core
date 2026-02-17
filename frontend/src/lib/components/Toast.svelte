<script lang="ts">
  import { toasts, type ToastVariant } from '../stores/toast';

  /** SVG icon paths per state */
  const ICONS: Record<ToastVariant, string[]> = {
    success: ['M20 6 9 17l-5-5'],
    error:   ['M18 6 6 18', 'M6 6 12 12'],
    warning: ['M12 9v4', 'M12 17h.01'],
    info:    ['M12 16v-4', 'M12 8h.01'],
  };

  /** Circle behind warning/info icons */
  const ICON_CIRCLE: Record<ToastVariant, boolean> = {
    success: false,
    error:   false,
    warning: true,
    info:    true,
  };

  /** oklch state colours (Sileo palette) */
  const STATE_COLORS: Record<ToastVariant, string> = {
    success: 'oklch(0.723 0.219 142.136)',
    error:   'oklch(0.637 0.237 25.331)',
    warning: 'oklch(0.795 0.184 86.047)',
    info:    'oklch(0.685 0.169 237.323)',
  };

  /** Dark pill fill per state */
  const FILLS: Record<ToastVariant, string> = {
    success: '#152b1e',
    error:   '#2b1519',
    warning: '#2b2615',
    info:    '#151d2b',
  };

  /** Labels in Spanish */
  const LABELS: Record<ToastVariant, string> = {
    success: 'Éxito',
    error:   'Error',
    warning: 'Aviso',
    info:    'Info',
  };

  const W = 350;
  const H = 40;
  const R = 18;

  /* ---- Swipe-to-dismiss ---- */
  let swipeY: Record<string, number> = {};
  let ptrStart: Record<string, number> = {};

  function onDown(e: PointerEvent, id: string) {
    ptrStart[id] = e.clientY;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onMove(e: PointerEvent, id: string) {
    if (ptrStart[id] == null) return;
    const dy = e.clientY - ptrStart[id];
    swipeY = { ...swipeY, [id]: Math.min(Math.abs(dy), 20) * (dy > 0 ? 1 : -1) };
  }
  function onUp(e: PointerEvent, id: string) {
    if (ptrStart[id] == null) return;
    const dy = e.clientY - ptrStart[id];
    delete ptrStart[id];
    swipeY = { ...swipeY, [id]: 0 };
    if (Math.abs(dy) > 30) toasts.remove(id);
  }
</script>

<div class="sileo-viewport">
  {#each $toasts as toast (toast.id)}
    {@const c = STATE_COLORS[toast.variant]}
    {@const fill = FILLS[toast.variant]}
    {@const paths = ICONS[toast.variant]}
    {@const circle = ICON_CIRCLE[toast.variant]}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="sileo-toast"
      role="alert"
      style="--_tone:{c}; --_tone-bg:color-mix(in oklch,{c} 20%,transparent); transform:translateY({swipeY[toast.id]??0}px)"
      on:pointerdown={e => onDown(e, toast.id)}
      on:pointermove={e => onMove(e, toast.id)}
      on:pointerup={e => onUp(e, toast.id)}
    >
      <!-- Gooey SVG pill -->
      <svg class="sileo-svg" width={W} height={H} viewBox="0 0 {W} {H}">
        <defs>
          <filter id="goo-{toast.id}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
            <feGaussianBlur in="SourceGraphic" stdDeviation="9" result="b"/>
            <feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -10" result="g"/>
            <feComposite in="SourceGraphic" in2="g" operator="atop"/>
          </filter>
        </defs>
        <g filter="url(#goo-{toast.id})">
          <rect x="0" y="0" width={W} height={H} rx={R} ry={R} fill={fill}/>
        </g>
      </svg>

      <!-- Header content -->
      <div class="sileo-header">
        <div class="sileo-badge">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            {#if circle}<circle cx="12" cy="12" r="10"/>{/if}
            {#each paths as d}<path {d}/>{/each}
          </svg>
        </div>
        <span class="sileo-label">{LABELS[toast.variant]}</span>
        <span class="sileo-msg">{toast.message}</span>
        <button type="button" class="sileo-x" on:click|stopPropagation={() => toasts.remove(toast.id)} aria-label="Cerrar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 6 6 18"/><path d="M6 6 12 12"/>
          </svg>
        </button>
      </div>
    </div>
  {/each}
</div>

<style>
  /* ── Variables ── */
  :root {
    --sileo-spring: linear(0,0.007 1.2%,0.026 2.4%,0.06 3.8%,0.157 6.6%,
      0.467 13.7%,0.631 17.7%,0.771 21.8%,0.874 25.8%,0.952 30.1%,
      0.988 33.1%,1.025 38.5%,1.038 45%,1.012 64.2%,0.999 83.7%,1);
    --sileo-dur: 600ms;
  }

  /* ── Viewport ── */
  .sileo-viewport {
    position: fixed;
    z-index: 100;
    top: 0;
    right: 0;
    display: flex;
    flex-direction: column-reverse;
    gap: 0.75rem;
    padding: 0.75rem;
    pointer-events: none;
    max-width: calc(100vw - 1.5rem);
  }

  /* ── Toast pill ── */
  .sileo-toast {
    position: relative;
    pointer-events: auto;
    touch-action: none;
    cursor: pointer;
    border: 0;
    background: transparent;
    padding: 0;
    width: 350px;
    height: 40px;
    overflow: visible;
    contain: layout style;
    animation: sileo-in var(--sileo-dur) var(--sileo-spring) both;
    transition:
      transform calc(var(--sileo-dur) * .66) var(--sileo-spring),
      opacity calc(var(--sileo-dur) * .66) var(--sileo-spring);
  }
  .sileo-toast:hover { transform: scale(1.015) !important; }

  /* ── SVG layer ── */
  .sileo-svg {
    position: absolute;
    inset: 0;
    overflow: visible;
    pointer-events: none;
    transform: translateZ(0);
  }

  /* ── Header ── */
  .sileo-header {
    position: absolute;
    inset: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0 0.625rem;
    height: 40px;
    overflow: hidden;
  }

  /* ── Badge ── */
  .sileo-badge {
    display: flex;
    height: 24px;
    width: 24px;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    border-radius: 9999px;
    color: var(--_tone);
    background: var(--_tone-bg);
  }

  /* ── Title / Message ── */
  .sileo-label {
    font-size: 0.825rem;
    font-weight: 600;
    line-height: 1;
    white-space: nowrap;
    color: var(--_tone);
    text-transform: capitalize;
  }
  .sileo-msg {
    flex: 1;
    font-size: 0.8rem;
    font-weight: 400;
    line-height: 1;
    color: #d4d4d4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
  }

  /* ── Close ── */
  .sileo-x {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    border: 0;
    background: transparent;
    color: #666;
    cursor: pointer;
    border-radius: 4px;
    padding: 0;
    opacity: 0;
    transition: opacity 150ms, color 150ms, background 150ms;
  }
  .sileo-toast:hover .sileo-x { opacity: 1; }
  .sileo-x:hover { color: #fff; background: rgba(255,255,255,0.1); }

  /* ── Animations ── */
  @keyframes sileo-in {
    from { opacity: 0; transform: translateY(-6px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* ── Responsive ── */
  @media (max-width: 420px) {
    .sileo-viewport { left: 0; right: 0; align-items: center; }
    .sileo-toast { width: calc(100vw - 1.5rem); }
  }

  /* ── Reduced motion ── */
  @media (prefers-reduced-motion: reduce) {
    .sileo-toast { animation-duration: 0.01ms; transition-duration: 0.01ms; }
  }
</style>
