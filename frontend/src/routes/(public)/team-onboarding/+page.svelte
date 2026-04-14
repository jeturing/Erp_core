<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

  const nicheMap: Record<string, {
    title: string;
    desc: string;
    icon: string;
    color: string;
    steps: string[];
    calendly?: string;
  }> = {
    mpos: {
      title: 'MPOS & Payments',
      desc: "You're one step away from accepting payments anywhere — Stripe, NFC, QR, all in one place.",
      icon: '💳',
      color: '#00FF9F',
      steps: [
        'Our team will verify your entity and configure your Stripe account',
        'Receive your SAJET MPOS credentials within 24h',
        'Onboarding call to set up your first payment terminal',
        'Go live — start accepting payments in under 48h',
      ],
    },
    build: {
      title: 'Custom Development',
      desc: "Your project is in the right hands. We'll scope, design, and build your custom solution.",
      icon: '🔧',
      color: '#0EA5E9',
      steps: [
        'Technical discovery call to review your requirements',
        'Proposal + timeline delivered within 48h',
        'Kickoff sprint — design, architecture, and first milestone',
        'Weekly updates until launch',
      ],
    },
    partners: {
      title: 'Partner Program',
      desc: "Welcome to the SAJET partner network. Let's set you up for your first referral commission.",
      icon: '🤝',
      color: '#A855F7',
      steps: [
        'Partner agreement signed digitally (5 minutes)',
        'Access to partner dashboard and referral links',
        'Onboarding call — learn the pitch and deal flow',
        'Your first deal closed within 30 days',
      ],
    },
    cpa: {
      title: 'CPA & Accounting Firms',
      desc: "Your multi-client workspace is ready. We'll configure it for your practice.",
      icon: '📊',
      color: '#F59E0B',
      steps: [
        'Firm verification and workspace provisioning',
        'White-label portal configured under your domain',
        'Import or migrate your first 3 client accounts',
        'Live — start managing all clients from one login',
      ],
    },
    smb: {
      title: 'SMB Program',
      desc: "You're on the growth track. Let's get your foundation right before scaling.",
      icon: '🌱',
      color: '#22C55E',
      steps: [
        'Business formation or verification (via Jeturing Atlas if needed)',
        'Starter tools activated — invoicing, expenses, payments',
        'Monthly check-in to track your growth milestones',
        'Upgrade automatically when you hit $5k/month or 5+ employees',
      ],
    },
  };

  $: niche = $page.url.searchParams.get('niche') || 'mpos';
  $: config = nicheMap[niche] || nicheMap['mpos'];
  $: accentColor = config.color;

  let currentStep = $state(0);
  const totalSteps = 4;

  function nextStep() {
    if (currentStep < totalSteps - 1) currentStep++;
  }
</script>

<svelte:head>
  <title>Welcome to SAJET — Team Onboarding</title>
  <meta name="description" content="Your onboarding is confirmed. Our team will reach out within 24 hours." />
</svelte:head>

<div class="ob-root">
  <div class="ob-bg">
    <div class="ob-overlay"></div>
    <div class="ob-glow glow-1" style="background: {accentColor};"></div>
    <div class="ob-glow glow-2"></div>
  </div>

  <nav class="ob-nav">
    <a href="/" class="nav-logo">
      <div class="logo-mark">S</div>
      <span>SAJET</span>
    </a>
  </nav>

  <main class="ob-main">
    <!-- Success header -->
    <div class="success-header">
      <div class="success-icon" style="background: {accentColor}20; border-color: {accentColor}40;">
        <span class="niche-icon">{config.icon}</span>
        <div class="checkmark" style="background: {accentColor};">✓</div>
      </div>
      <h1>You're in. <em style="color: {accentColor};">Welcome.</em></h1>
      <p class="sub">
        {config.desc}
      </p>
      <div class="niche-badge" style="border-color: {accentColor}40; color: {accentColor};">
        {config.title} Track
      </div>
    </div>

    <!-- What happens next -->
    <section class="next-section">
      <div class="section-label">What happens next</div>
      <div class="steps-track">
        {#each config.steps as step, i}
          <div class="step-item" class:active={i <= currentStep} class:current={i === currentStep}>
            <div class="step-dot" style={i <= currentStep ? `background: ${accentColor};` : ''}>
              {#if i < currentStep}
                <span class="step-check">✓</span>
              {:else}
                <span class="step-num">{i + 1}</span>
              {/if}
            </div>
            <div class="step-connector" class:filled={i < currentStep} style={i < currentStep ? `background: ${accentColor};` : ''}></div>
            <div class="step-content">
              <p class:active-text={i === currentStep}>{step}</p>
            </div>
          </div>
        {/each}
      </div>

      {#if currentStep < totalSteps - 1}
        <button class="next-btn" onclick={nextStep} style="background: {accentColor}; color: #020e1f;">
          Got it →
        </button>
      {:else}
        <div class="complete-msg" style="border-color: {accentColor}40; color: {accentColor};">
          ✓ Your onboarding path is clear. Expect a call from our team within 24 hours.
        </div>
      {/if}
    </section>

    <!-- Expect from us -->
    <section class="expect-section">
      <h2>What to expect from us</h2>
      <div class="expect-grid">
        <div class="expect-card">
          <div class="expect-icon">⚡</div>
          <h3>Fast response</h3>
          <p>Our team will reach out within 24 hours — usually faster during business hours EST.</p>
        </div>
        <div class="expect-card">
          <div class="expect-icon">🤝</div>
          <h3>Dedicated contact</h3>
          <p>You'll be assigned a single point of contact for your onboarding — not a support ticket queue.</p>
        </div>
        <div class="expect-card">
          <div class="expect-icon">🔒</div>
          <h3>No spam, ever</h3>
          <p>Your info stays in our CRM. We'll only reach out about your onboarding — nothing else.</p>
        </div>
      </div>
    </section>

    <!-- CTA to explore -->
    <div class="explore-row">
      <p>While you wait, explore what's waiting for you:</p>
      <div class="explore-links">
        <a href="/mpos" class="ex-btn">💳 MPOS</a>
        <a href="/build" class="ex-btn">🔧 Dev</a>
        <a href="/cpa" class="ex-btn">📊 CPA</a>
        <a href="/partners" class="ex-btn">🤝 Partners</a>
      </div>
    </div>
  </main>

  <footer class="ob-footer">
    <div class="footer-inner">
      <span class="footer-copy">© 2025 SAJET by Jeturing</span>
      <div class="footer-links">
        <a href="/terms">Terms</a>
        <a href="/privacy">Privacy</a>
      </div>
    </div>
  </footer>
</div>

<style>
  .ob-root {
    background: #020e1f; color: #f0ede8;
    font-family: 'Inter', sans-serif;
    min-height: 100vh; overflow-x: hidden;
  }
  .ob-bg {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
  }
  .ob-overlay {
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 30% 10%, rgba(0,59,115,.25) 0%, transparent 60%);
  }
  .ob-glow {
    position: absolute; border-radius: 50%; filter: blur(100px); opacity: .12;
  }
  .glow-1 { width: 600px; height: 600px; top: -15%; left: 20%; }
  .glow-2 { width: 400px; height: 400px; background: #0ea5e9; bottom: 5%; right: -5%; }

  .ob-nav {
    position: relative; z-index: 10;
    padding: 1.5rem 2rem; max-width: 1100px; margin: 0 auto;
  }
  .nav-logo { display: flex; align-items: center; gap: .6rem; text-decoration: none; font-weight: 700; color: #fff; }
  .logo-mark {
    width: 36px; height: 36px; border-radius: 8px;
    background: linear-gradient(135deg, #00FF9F, #0ea5e9);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; color: #020e1f;
  }

  .ob-main {
    position: relative; z-index: 1;
    max-width: 760px; margin: 0 auto; padding: 3rem 2rem 5rem;
  }

  .success-header { text-align: center; margin-bottom: 4rem; }
  .success-icon {
    position: relative; display: inline-flex; align-items: center; justify-content: center;
    width: 100px; height: 100px; border-radius: 50%; border: 2px solid;
    margin-bottom: 1.5rem;
  }
  .niche-icon { font-size: 2.8rem; }
  .checkmark {
    position: absolute; bottom: -4px; right: -4px;
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem; font-weight: 800; color: #020e1f;
  }
  .success-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2rem, 5vw, 3rem); font-weight: 800; color: #fff;
    margin-bottom: .8rem;
  }
  .success-header h1 em { font-style: normal; }
  .sub { color: #94a3b8; font-size: 1.05rem; line-height: 1.65; max-width: 520px; margin: 0 auto 1.2rem; }
  .niche-badge {
    display: inline-block; padding: .3rem .9rem;
    border: 1px solid; border-radius: 100px;
    font-size: .75rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
  }

  .next-section { margin-bottom: 4rem; }
  .section-label {
    font-size: .75rem; text-transform: uppercase; letter-spacing: .1em;
    color: #64748b; margin-bottom: 2rem;
  }
  .steps-track { display: flex; flex-direction: column; gap: 0; margin-bottom: 2rem; }
  .step-item { display: grid; grid-template-columns: 32px 2px 1fr; gap: 0 1rem; align-items: start; padding-bottom: 1.5rem; }
  .step-item:last-child { padding-bottom: 0; }
  .step-dot {
    width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
    font-size: .8rem; font-weight: 700; color: #64748b;
    transition: all .3s;
  }
  .step-item.active .step-dot { color: #020e1f; }
  .step-check { font-size: .85rem; }
  .step-connector {
    width: 2px; background: rgba(255,255,255,.08); margin-top: 0;
    align-self: stretch; min-height: 1.5rem;
    transition: background .3s;
  }
  .step-item:last-child .step-connector { display: none; }
  .step-content { padding-top: .35rem; padding-bottom: 1.5rem; }
  .step-content p { color: #64748b; font-size: .92rem; line-height: 1.55; margin: 0; transition: color .3s; }
  .step-content p.active-text { color: #e2e8f0; }

  .next-btn {
    padding: .75rem 2rem; border-radius: 8px; border: none; cursor: pointer;
    font-weight: 700; font-size: 1rem; transition: transform .15s, opacity .2s;
  }
  .next-btn:hover { transform: translateY(-1px); opacity: .9; }

  .complete-msg {
    padding: 1rem 1.5rem; border: 1px solid; border-radius: 10px;
    font-size: .95rem; font-weight: 500;
  }

  .expect-section { margin-bottom: 4rem; }
  .expect-section h2 {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700;
    color: #fff; margin-bottom: 1.5rem;
  }
  .expect-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
  .expect-card {
    padding: 1.5rem; border-radius: 12px;
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07);
  }
  .expect-icon { font-size: 1.5rem; margin-bottom: .6rem; }
  .expect-card h3 { font-family: 'Space Grotesk', sans-serif; font-size: .95rem; color: #fff; margin-bottom: .4rem; }
  .expect-card p { font-size: .83rem; color: #64748b; line-height: 1.5; margin: 0; }

  .explore-row { text-align: center; }
  .explore-row p { color: #64748b; margin-bottom: 1rem; font-size: .9rem; }
  .explore-links { display: flex; flex-wrap: wrap; justify-content: center; gap: .6rem; }
  .ex-btn {
    display: inline-flex; align-items: center; gap: .3rem;
    padding: .55rem 1.1rem; border-radius: 8px;
    border: 1px solid rgba(255,255,255,.1); color: #94a3b8;
    text-decoration: none; font-size: .85rem; transition: all .2s;
  }
  .ex-btn:hover { border-color: rgba(255,255,255,.3); color: #fff; }

  .ob-footer {
    position: relative; z-index: 1;
    border-top: 1px solid rgba(255,255,255,.06); padding: 1.5rem 2rem;
  }
  .footer-inner {
    max-width: 760px; margin: 0 auto;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .8rem;
  }
  .footer-copy { color: #475569; font-size: .8rem; }
  .footer-links { display: flex; gap: 1.2rem; }
  .footer-links a { color: #475569; font-size: .8rem; text-decoration: none; }
  .footer-links a:hover { color: #94a3b8; }

  @media (max-width: 640px) {
    .expect-grid { grid-template-columns: 1fr; }
    .step-item { grid-template-columns: 28px 2px 1fr; }
  }
</style>
