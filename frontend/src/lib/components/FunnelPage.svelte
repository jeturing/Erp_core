<script lang="ts">
  import { goto } from '$app/navigation';
  import { submitFunnelLead } from '$lib/api/funnelLeads';
  import type { FunnelLeadPayload } from '$lib/api/funnelLeads';
  import { onMount } from 'svelte';

  // ── Props ────────────────────────────────────────────────────────────────
  interface FunnelConfig {
    niche:       'mpos' | 'build' | 'partners' | 'cpa' | 'smb' | 'general';
    badge:       string;
    headline:    string;
    subheadline: string;
    painPoints:  string[];
    solution:    { icon: string; title: string; desc: string }[];
    features:    { icon: string; title: string; desc: string }[];
    stats:       { value: string; label: string }[];
    cta:         string;
    quizTitle:   string;
    quizSteps:   QuizStep[];
    videoUrl?:   string;
    accentColor?: string;
  }

  interface QuizStep {
    id:       string;
    question: string;
    type:     'single' | 'input' | 'number';
    options?: { label: string; value: string; disqualify?: boolean; reason?: string }[];
    field:    keyof FunnelLeadPayload;
    required?: boolean;
    hint?:    string;
  }

  let { config }: { config: FunnelConfig } = $props();

  // ── State ─────────────────────────────────────────────────────────────────
  type Stage = 'hero' | 'quiz' | 'form' | 'success';
  let stage         = $state<Stage>('hero');
  let quizStep      = $state(0);
  let quizAnswers   = $state<Record<string, any>>({});
  let disqualified  = $state(false);
  let disqualReason = $state('');
  let submitting    = $state(false);
  let error         = $state('');
  let videoLoaded   = $state(false);
  let heroVisible   = $state(false);

  // Form fields
  let fullName     = $state('');
  let email        = $state('');
  let phone        = $state('');
  let companyName  = $state('');
  let country      = $state('');
  let mainGoal     = $state('');

  const accent = config.accentColor ?? '#00FF9F';

  onMount(() => {
    setTimeout(() => { heroVisible = true; }, 100);
  });

  // ── Quiz logic ────────────────────────────────────────────────────────────
  function answerQuiz(step: QuizStep, value: any) {
    quizAnswers = { ...quizAnswers, [step.id]: value };

    // Check disqualification
    if (step.type === 'single') {
      const opt = step.options?.find(o => o.value === value);
      if (opt?.disqualify) {
        disqualified  = true;
        disqualReason = opt.reason ?? 'not_qualified';
        stage = 'quiz'; // Keep showing quiz with disqualify message
        return;
      }
    }

    if (quizStep < config.quizSteps.length - 1) {
      quizStep += 1;
    } else {
      stage = 'form';
    }
  }

  function nextQuiz(step: QuizStep) {
    const val = quizAnswers[step.id];
    if (step.required && !val) return;
    answerQuiz(step, val ?? '');
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!fullName || !email) { error = 'Name and email are required'; return; }

    submitting = true; error = '';
    try {
      const payload: FunnelLeadPayload = {
        niche:          config.niche,
        full_name:      fullName,
        email,
        phone:          phone || undefined,
        company_name:   companyName || undefined,
        country:        country || undefined,
        main_goal:      mainGoal || undefined,
        has_entity:     quizAnswers['has_entity'],
        monthly_volume: quizAnswers['monthly_volume'],
        budget_range:   quizAnswers['budget_range'],
        timeline:       quizAnswers['timeline'],
        client_count:   quizAnswers['client_count'] ? parseInt(quizAnswers['client_count']) : undefined,
        has_sales_team: quizAnswers['has_sales_team'],
        industry:       quizAnswers['industry'],
      };

      const res = await submitFunnelLead(payload);

      if (res.redirect.startsWith('http')) {
        window.location.href = res.redirect;
      } else {
        await goto(res.redirect);
      }
      stage = 'success';
    } catch (err: any) {
      error = err?.message ?? 'Something went wrong. Please try again.';
    } finally {
      submitting = false;
    }
  }

  const countries = [
    { code: 'US', name: 'United States' },
    { code: 'MX', name: 'Mexico' },
    { code: 'CO', name: 'Colombia' },
    { code: 'DO', name: 'Dominican Republic' },
    { code: 'GT', name: 'Guatemala' },
    { code: 'SV', name: 'El Salvador' },
    { code: 'HN', name: 'Honduras' },
    { code: 'PE', name: 'Peru' },
    { code: 'EC', name: 'Ecuador' },
    { code: 'CL', name: 'Chile' },
    { code: 'AR', name: 'Argentina' },
    { code: 'PR', name: 'Puerto Rico' },
    { code: 'CR', name: 'Costa Rica' },
    { code: 'PA', name: 'Panama' },
    { code: 'VE', name: 'Venezuela' },
    { code: 'BO', name: 'Bolivia' },
    { code: 'PY', name: 'Paraguay' },
    { code: 'UY', name: 'Uruguay' },
    { code: 'NI', name: 'Nicaragua' },
  ];
</script>

<!-- ══ HERO ══════════════════════════════════════════════════════════════════ -->
<div class="funnel-root">

  <!-- Video / animated background -->
  <div class="hero-bg">
    {#if config.videoUrl}
      <video
        class="hero-video"
        class:loaded={videoLoaded}
        autoplay muted loop playsinline
        oncanplay={() => videoLoaded = true}
      >
        <source src={config.videoUrl} type="video/mp4" />
      </video>
    {/if}
    <div class="hero-overlay"></div>
    <div class="hero-particles">
      {#each Array(20) as _, i}
        <div class="particle" style="--i:{i}; --accent:{accent}"></div>
      {/each}
    </div>
  </div>

  <!-- ── SECTION 1: HERO ── -->
  <section class="hero-section" class:visible={heroVisible}>
    <nav class="funnel-nav">
      <a href="/" class="nav-logo">
        <div class="logo-mark">S</div>
        <span class="logo-text">SAJET</span>
      </a>
      <a href="/login" class="nav-login">Sign in →</a>
    </nav>

    <div class="hero-content">
      <div class="badge">{config.badge}</div>
      <h1 class="hero-headline">{@html config.headline}</h1>
      <p class="hero-sub">{config.subheadline}</p>
      <button class="cta-primary" onclick={() => stage = 'quiz'}>
        {config.cta}
        <span class="cta-arrow">→</span>
      </button>
      <p class="hero-trust">No credit card · Takes 2 minutes · Cancel anytime</p>
    </div>

    <!-- Stats bar -->
    {#if config.stats.length}
      <div class="stats-bar">
        {#each config.stats as stat}
          <div class="stat-item">
            <span class="stat-value" style="color:{accent}">{stat.value}</span>
            <span class="stat-label">{stat.label}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- ── SECTION 2: PAIN ── -->
  <section class="pain-section">
    <div class="section-inner">
      <div class="section-badge">Sound familiar?</div>
      <h2 class="section-title">The real cost of doing nothing</h2>
      <div class="pain-grid">
        {#each config.painPoints as pain}
          <div class="pain-card">
            <span class="pain-x">✕</span>
            <p>{pain}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- ── SECTION 3: SOLUTION ── -->
  <section class="solution-section">
    <div class="section-inner">
      <div class="section-badge" style="background:rgba(0,255,159,.12);color:{accent}">The Sajet way</div>
      <h2 class="section-title">Everything you need. Nothing you don't.</h2>
      <div class="solution-grid">
        {#each config.solution as item}
          <div class="solution-card">
            <div class="solution-icon" style="background:rgba(0,255,159,.08);color:{accent}">{item.icon}</div>
            <h3>{item.title}</h3>
            <p>{item.desc}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- ── SECTION 4: FEATURES ── -->
  <section class="features-section">
    <div class="section-inner">
      <h2 class="section-title">Built for your business</h2>
      <div class="features-list">
        {#each config.features as f}
          <div class="feature-row">
            <span class="feature-icon" style="color:{accent}">{f.icon}</span>
            <div>
              <strong>{f.title}</strong>
              <p>{f.desc}</p>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- ── SECTION 5: QUIZ / FORM / SUCCESS ── -->
  <section class="conversion-section" id="start">
    <div class="conversion-inner">

      <!-- QUIZ STAGE -->
      {#if stage === 'hero' || stage === 'quiz'}
        <div class="quiz-wrapper">
          {#if disqualified}
            <!-- Disqualified → SMB path -->
            <div class="disqualify-box">
              <div class="disq-icon">🌱</div>
              <h3>You're in the right place — just a different path.</h3>
              <p>
                We love growth-stage companies. Based on your answers, we want to point you to
                <strong>Jeturing Atlas</strong> — our SMB accelerator program designed to help
                you get structure, funding access, and technology in place before scaling.
              </p>
              <a href="https://jeturing.com/atlas" class="cta-primary" target="_blank" rel="noopener">
                Explore Atlas Program →
              </a>
              <a href="/smb" class="cta-ghost">Learn about SMB plans</a>
            </div>
          {:else if stage === 'hero'}
            <div class="quiz-start">
              <p class="quiz-label">Takes 60 seconds</p>
              <h3 class="quiz-title">{config.quizTitle}</h3>
              <button class="cta-primary" onclick={() => stage = 'quiz'}>
                {config.cta} →
              </button>
            </div>
          {:else}
            <!-- Quiz steps -->
            {@const step = config.quizSteps[quizStep]}
            <div class="quiz-progress">
              {#each config.quizSteps as _, i}
                <div class="progress-dot" class:active={i === quizStep} class:done={i < quizStep} style="--accent:{accent}"></div>
              {/each}
            </div>
            <div class="quiz-card" class:animate-in={true}>
              <p class="step-counter">Question {quizStep + 1} of {config.quizSteps.length}</p>
              <h3 class="step-question">{step.question}</h3>
              {#if step.hint}<p class="step-hint">{step.hint}</p>{/if}

              {#if step.type === 'single'}
                <div class="options-grid">
                  {#each step.options ?? [] as opt}
                    <button
                      class="option-btn"
                      class:selected={quizAnswers[step.id] === opt.value}
                      style="--accent:{accent}"
                      onclick={() => answerQuiz(step, opt.value)}
                    >
                      {opt.label}
                    </button>
                  {/each}
                </div>
              {:else if step.type === 'input'}
                <input
                  class="quiz-input"
                  type="text"
                  placeholder="Your answer..."
                  bind:value={quizAnswers[step.id]}
                  onkeydown={(e) => e.key === 'Enter' && nextQuiz(step)}
                />
                <button class="cta-secondary" onclick={() => nextQuiz(step)}>Continue →</button>
              {:else if step.type === 'number'}
                <input
                  class="quiz-input"
                  type="number"
                  min="0"
                  placeholder="0"
                  bind:value={quizAnswers[step.id]}
                  onkeydown={(e) => e.key === 'Enter' && nextQuiz(step)}
                />
                <button class="cta-secondary" onclick={() => nextQuiz(step)}>Continue →</button>
              {/if}
            </div>
          {/if}
        </div>

      <!-- FORM STAGE -->
      {:else if stage === 'form'}
        <form class="lead-form" onsubmit={handleSubmit}>
          <div class="form-header">
            <div class="form-check" style="color:{accent}">✓ You qualify!</div>
            <h3>Let's get you set up</h3>
            <p>Fill in your details and we'll prepare your workspace.</p>
          </div>

          {#if error}
            <div class="form-error">{error}</div>
          {/if}

          <div class="form-row">
            <div class="form-group">
              <label for="fl-name">Full Name *</label>
              <input id="fl-name" type="text" bind:value={fullName} placeholder="Maria Garcia" required />
            </div>
            <div class="form-group">
              <label for="fl-email">Email *</label>
              <input id="fl-email" type="email" bind:value={email} placeholder="maria@empresa.com" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="fl-phone">Phone</label>
              <input id="fl-phone" type="tel" bind:value={phone} placeholder="+1 809 000 0000" />
            </div>
            <div class="form-group">
              <label for="fl-company">Company Name</label>
              <input id="fl-company" type="text" bind:value={companyName} placeholder="Empresa S.A." />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="fl-country">Country</label>
              <select id="fl-country" bind:value={country}>
                <option value="">Select country...</option>
                {#each countries as c}
                  <option value={c.code}>{c.name}</option>
                {/each}
              </select>
            </div>
            <div class="form-group">
              <label for="fl-goal">What's your main goal?</label>
              <input id="fl-goal" type="text" bind:value={mainGoal} placeholder="Describe in one sentence..." />
            </div>
          </div>

          <button type="submit" class="cta-primary full-width" disabled={submitting}>
            {#if submitting}
              <span class="spinner"></span> Setting up your space...
            {:else}
              Get started now →
            {/if}
          </button>
          <p class="form-trust">
            🔒 Your data is encrypted and never shared. No credit card required.
          </p>
        </form>

      <!-- SUCCESS STAGE -->
      {:else if stage === 'success'}
        <div class="success-box">
          <div class="success-icon" style="color:{accent}">✓</div>
          <h3>You're in!</h3>
          <p>Redirecting you to your personalized onboarding...</p>
          <div class="success-loader" style="--accent:{accent}"></div>
        </div>
      {/if}
    </div>
  </section>

  <!-- ── FOOTER ── -->
  <footer class="funnel-footer">
    <div class="footer-inner">
      <div class="footer-logo">
        <div class="logo-mark small">S</div>
        <span>SAJET</span>
      </div>
      <div class="footer-links">
        <a href="/terms">Terms</a>
        <a href="/privacy">Privacy</a>
        <a href="/security">Security</a>
        <a href="/login">Sign in</a>
      </div>
      <p class="footer-copy">© {new Date().getFullYear()} Jeturing / SAJET. All rights reserved.</p>
    </div>
  </footer>
</div>

<style>
  /* ═══ ROOT ══════════════════════════════════════════════════════ */
  .funnel-root {
    background: #020e1f;
    color: #f0ede8;
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ═══ HERO BACKGROUND ═══════════════════════════════════════════ */
  .hero-bg {
    position: absolute;
    inset: 0;
    height: 100vh;
    overflow: hidden;
    z-index: 0;
  }
  .hero-video {
    width: 100%; height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 1.2s ease;
  }
  .hero-video.loaded { opacity: 0.35; }
  .hero-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(2,14,31,.92) 0%, rgba(0,59,115,.75) 50%, rgba(2,14,31,.95) 100%);
  }

  /* Particles */
  .hero-particles { position: absolute; inset: 0; pointer-events: none; }
  .particle {
    position: absolute;
    width: 2px; height: 2px;
    border-radius: 50%;
    background: var(--accent);
    opacity: 0;
    left: calc(var(--i) * 5.3% + 2%);
    top: calc(var(--i) * 4.7% + 5%);
    animation: float calc(3s + var(--i) * 0.4s) ease-in-out infinite alternate;
    animation-delay: calc(var(--i) * 0.2s);
  }
  @keyframes float {
    from { opacity: 0; transform: translateY(0) scale(1); }
    to   { opacity: 0.6; transform: translateY(-30px) scale(1.5); }
  }

  /* ═══ NAV ════════════════════════════════════════════════════════ */
  .funnel-nav {
    position: relative; z-index: 10;
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.5rem 2rem;
    max-width: 1100px; margin: 0 auto;
  }
  .nav-logo { display: flex; align-items: center; gap: .6rem; text-decoration: none; }
  .logo-mark {
    width: 36px; height: 36px; border-radius: 8px;
    background: linear-gradient(135deg, #00FF9F, #0EA5E9);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; color: #020e1f;
  }
  .logo-mark.small { width: 28px; height: 28px; font-size: .8rem; }
  .logo-text { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.1rem; color: #fff; letter-spacing: .05em; }
  .nav-login { color: #94a3b8; font-size: .9rem; text-decoration: none; transition: color .2s; }
  .nav-login:hover { color: #fff; }

  /* ═══ HERO SECTION ══════════════════════════════════════════════ */
  .hero-section {
    position: relative; z-index: 1;
    min-height: 100vh;
    display: flex; flex-direction: column;
    justify-content: center;
    padding-top: 5rem;
    opacity: 0; transform: translateY(24px);
    transition: opacity .8s ease, transform .8s ease;
  }
  .hero-section.visible { opacity: 1; transform: translateY(0); }

  .hero-content {
    max-width: 780px; margin: 0 auto;
    padding: 2rem 2rem 4rem;
    text-align: center;
  }
  .badge {
    display: inline-flex; align-items: center;
    gap: .4rem; padding: .35rem .9rem;
    border: 1px solid rgba(0,255,159,.35);
    border-radius: 100px;
    font-size: .75rem; font-weight: 600; letter-spacing: .08em;
    color: #00FF9F; text-transform: uppercase; margin-bottom: 1.5rem;
  }
  .hero-headline {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2.2rem, 5vw, 4rem);
    font-weight: 800; line-height: 1.12;
    color: #fff; margin-bottom: 1.2rem;
  }
  .hero-headline :global(em) { color: #00FF9F; font-style: normal; }
  .hero-sub {
    font-size: 1.15rem; color: #94a3b8; line-height: 1.6;
    max-width: 600px; margin: 0 auto 2.5rem;
  }
  .hero-trust { font-size: .8rem; color: #64748b; margin-top: .8rem; }

  /* ═══ CTAs ═══════════════════════════════════════════════════════ */
  .cta-primary {
    display: inline-flex; align-items: center; gap: .5rem;
    background: #00FF9F; color: #020e1f;
    font-weight: 700; font-size: 1rem;
    padding: .85rem 2rem; border-radius: 8px;
    border: none; cursor: pointer;
    transition: transform .15s, box-shadow .15s;
    text-decoration: none;
  }
  .cta-primary:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,255,159,.3); }
  .cta-primary:disabled { opacity: .6; cursor: not-allowed; transform: none; }
  .cta-primary.full-width { width: 100%; justify-content: center; font-size: 1.05rem; padding: 1rem; }
  .cta-secondary {
    display: inline-flex; align-items: center; gap: .4rem;
    background: transparent; color: #fff;
    font-weight: 600; font-size: .95rem;
    padding: .75rem 1.5rem; border-radius: 8px;
    border: 1px solid rgba(255,255,255,.2); cursor: pointer;
    transition: border-color .2s, background .2s;
    margin-top: 1rem;
  }
  .cta-secondary:hover { border-color: rgba(255,255,255,.5); background: rgba(255,255,255,.05); }
  .cta-ghost {
    display: block; margin-top: .8rem;
    color: #64748b; font-size: .85rem; text-decoration: none;
    transition: color .2s;
  }
  .cta-ghost:hover { color: #94a3b8; }
  .cta-arrow { font-size: 1.1rem; }

  /* ═══ STATS BAR ══════════════════════════════════════════════════ */
  .stats-bar {
    display: flex; justify-content: center; flex-wrap: wrap; gap: 2rem;
    padding: 2rem; background: rgba(255,255,255,.03);
    border-top: 1px solid rgba(255,255,255,.06);
    position: relative; z-index: 1;
  }
  .stat-item { text-align: center; }
  .stat-value { display: block; font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 800; }
  .stat-label { font-size: .8rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }

  /* ═══ SECTIONS ═══════════════════════════════════════════════════ */
  .section-inner { max-width: 1100px; margin: 0 auto; padding: 5rem 2rem; text-align: center; }
  .section-badge {
    display: inline-block; padding: .3rem .8rem;
    border-radius: 6px; font-size: .75rem; font-weight: 600;
    letter-spacing: .06em; text-transform: uppercase;
    background: rgba(255,255,255,.06); color: #94a3b8;
    margin-bottom: 1.2rem;
  }
  .section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.8rem, 3vw, 2.6rem);
    font-weight: 700; color: #fff; margin-bottom: 3rem; line-height: 1.2;
  }

  /* ═══ PAIN ════════════════════════════════════════════════════════ */
  .pain-section { background: rgba(255,255,255,.02); }
  .pain-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem;
  }
  .pain-card {
    display: flex; align-items: flex-start; gap: .8rem;
    padding: 1.2rem 1.5rem;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 10px; text-align: left;
  }
  .pain-card p { font-size: .92rem; color: #94a3b8; line-height: 1.5; margin: 0; }
  .pain-x { color: #ef4444; font-weight: 800; font-size: 1rem; flex-shrink: 0; margin-top: .1rem; }

  /* ═══ SOLUTION ════════════════════════════════════════════════════ */
  .solution-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;
  }
  .solution-card {
    padding: 1.8rem; border-radius: 12px;
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    text-align: left; transition: transform .2s, border-color .2s;
  }
  .solution-card:hover { transform: translateY(-3px); border-color: rgba(0,255,159,.25); }
  .solution-icon {
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; margin-bottom: 1rem;
  }
  .solution-card h3 { font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: .5rem; }
  .solution-card p { font-size: .88rem; color: #94a3b8; line-height: 1.5; margin: 0; }

  /* ═══ FEATURES ════════════════════════════════════════════════════ */
  .features-section { background: rgba(0,59,115,.08); }
  .features-list { display: flex; flex-direction: column; gap: 1.2rem; max-width: 700px; margin: 0 auto; text-align: left; }
  .feature-row {
    display: flex; align-items: flex-start; gap: 1rem;
    padding: 1.2rem 1.5rem;
    background: rgba(255,255,255,.03);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,.06);
  }
  .feature-icon { font-size: 1.3rem; flex-shrink: 0; margin-top: .1rem; }
  .feature-row strong { display: block; color: #fff; font-size: .95rem; margin-bottom: .3rem; }
  .feature-row p { color: #64748b; font-size: .85rem; margin: 0; }

  /* ═══ CONVERSION SECTION ══════════════════════════════════════════ */
  .conversion-section {
    padding: 5rem 2rem;
    background: linear-gradient(180deg, rgba(0,59,115,.15) 0%, rgba(2,14,31,1) 100%);
  }
  .conversion-inner {
    max-width: 620px; margin: 0 auto;
  }

  /* Quiz */
  .quiz-wrapper { text-align: center; }
  .quiz-start { }
  .quiz-label { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; color: #64748b; margin-bottom: .5rem; }
  .quiz-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #fff; margin-bottom: 2rem; }
  .quiz-progress { display: flex; justify-content: center; gap: .5rem; margin-bottom: 2rem; }
  .progress-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: rgba(255,255,255,.15); transition: all .3s;
  }
  .progress-dot.done { background: var(--accent); opacity: .5; }
  .progress-dot.active { background: var(--accent); transform: scale(1.3); }
  .quiz-card {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px; padding: 2.5rem;
    text-align: left;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  .quiz-card.animate-in { animation: slideIn .3s ease; }
  .step-counter { font-size: .75rem; text-transform: uppercase; letter-spacing: .08em; color: #64748b; margin-bottom: .8rem; }
  .step-question { font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 700; color: #fff; margin-bottom: .6rem; }
  .step-hint { font-size: .85rem; color: #64748b; margin-bottom: 1.5rem; }
  .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin-top: 1.5rem; }
  .option-btn {
    padding: 1rem; border-radius: 10px;
    border: 1px solid rgba(255,255,255,.12);
    background: rgba(255,255,255,.03); color: #d1d5db;
    font-size: .9rem; cursor: pointer; transition: all .2s; text-align: center;
  }
  .option-btn:hover { border-color: var(--accent); color: #fff; background: rgba(0,255,159,.06); }
  .option-btn.selected { border-color: var(--accent); background: rgba(0,255,159,.1); color: #fff; }
  .quiz-input {
    width: 100%; padding: .9rem 1rem; background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.15); border-radius: 8px;
    color: #fff; font-size: 1rem; margin-top: 1.5rem;
    outline: none; transition: border-color .2s;
  }
  .quiz-input:focus { border-color: rgba(0,255,159,.5); }

  /* Disqualify */
  .disqualify-box {
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px; padding: 3rem 2.5rem; text-align: center;
  }
  .disq-icon { font-size: 3rem; margin-bottom: 1rem; }
  .disqualify-box h3 { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; color: #fff; margin-bottom: 1rem; }
  .disqualify-box p { color: #94a3b8; line-height: 1.6; margin-bottom: 2rem; max-width: 480px; margin-left: auto; margin-right: auto; }

  /* Lead Form */
  .lead-form {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px; padding: 2.5rem;
  }
  .form-header { text-align: center; margin-bottom: 2rem; }
  .form-check { font-size: 1.5rem; font-weight: 800; font-family: 'Space Grotesk', sans-serif; margin-bottom: .4rem; }
  .form-header h3 { font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; color: #fff; margin-bottom: .4rem; }
  .form-header p { color: #94a3b8; font-size: .9rem; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
  .form-group { display: flex; flex-direction: column; gap: .4rem; }
  .form-group label { font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: #64748b; font-weight: 600; }
  .form-group input, .form-group select {
    padding: .75rem 1rem;
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 8px; color: #fff; font-size: .95rem;
    outline: none; transition: border-color .2s; width: 100%;
  }
  .form-group input:focus, .form-group select:focus { border-color: rgba(0,255,159,.4); }
  .form-group select option { background: #0f172a; }
  .form-error {
    background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.3);
    border-radius: 8px; padding: .75rem 1rem; color: #fca5a5;
    font-size: .85rem; margin-bottom: 1.2rem;
  }
  .form-trust { text-align: center; font-size: .78rem; color: #475569; margin-top: .8rem; }
  .spinner {
    width: 16px; height: 16px; border: 2px solid rgba(0,0,0,.2);
    border-top-color: #020e1f; border-radius: 50%;
    animation: spin .6s linear infinite; display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Success */
  .success-box { text-align: center; padding: 4rem 2rem; }
  .success-icon { font-size: 4rem; font-weight: 900; }
  .success-box h3 { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; color: #fff; margin: 1rem 0 .5rem; }
  .success-box p { color: #94a3b8; margin-bottom: 2rem; }
  .success-loader {
    width: 60px; height: 3px; background: rgba(255,255,255,.1);
    border-radius: 2px; margin: 0 auto; overflow: hidden;
  }
  .success-loader::after {
    content: ''; display: block; width: 40%;
    height: 100%; background: var(--accent);
    animation: load 1.5s ease infinite;
  }
  @keyframes load { from { transform: translateX(-100%); } to { transform: translateX(300%); } }

  /* ═══ FOOTER ══════════════════════════════════════════════════════ */
  .funnel-footer {
    border-top: 1px solid rgba(255,255,255,.06);
    background: rgba(255,255,255,.01);
    padding: 2.5rem 2rem;
  }
  .footer-inner {
    max-width: 1100px; margin: 0 auto;
    display: flex; align-items: center; flex-wrap: wrap; gap: 1rem; justify-content: space-between;
  }
  .footer-logo { display: flex; align-items: center; gap: .5rem; font-weight: 700; font-size: .9rem; color: #fff; }
  .footer-links { display: flex; gap: 1.5rem; }
  .footer-links a { color: #64748b; font-size: .85rem; text-decoration: none; transition: color .2s; }
  .footer-links a:hover { color: #fff; }
  .footer-copy { color: #334155; font-size: .78rem; }

  /* ═══ RESPONSIVE ══════════════════════════════════════════════════ */
  @media (max-width: 640px) {
    .form-row { grid-template-columns: 1fr; }
    .options-grid { grid-template-columns: 1fr; }
    .hero-content { padding: 1.5rem; }
    .quiz-card { padding: 1.5rem; }
    .lead-form { padding: 1.5rem; }
    .stats-bar { gap: 1.5rem; padding: 1.5rem 1rem; }
    .section-inner { padding: 3.5rem 1.5rem; }
    .footer-inner { flex-direction: column; text-align: center; }
    .footer-links { justify-content: center; flex-wrap: wrap; gap: 1rem; }
  }
</style>
