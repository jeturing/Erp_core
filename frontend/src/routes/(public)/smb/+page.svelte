<script lang="ts">
  import { goto } from '$app/navigation';
</script>

<svelte:head>
  <title>SAJET for Growing Businesses — SMB Program</title>
  <meta name="description" content="You're on the right track. SAJET's SMB program meets you where you are — tools, structure, and a clear path to scale." />
</svelte:head>

<div class="smb-root">
  <!-- Background -->
  <div class="smb-bg">
    <div class="smb-overlay"></div>
    <div class="smb-glow glow-1"></div>
    <div class="smb-glow glow-2"></div>
  </div>

  <!-- Nav -->
  <nav class="smb-nav">
    <a href="/" class="nav-logo">
      <div class="logo-mark">S</div>
      <span>SAJET</span>
    </a>
    <a href="/login" class="nav-login">Sign in →</a>
  </nav>

  <!-- Hero -->
  <section class="smb-hero">
    <div class="hero-inner">
      <div class="hero-badge">🌱 Growing Business Track</div>
      <h1>You're building something real.<br/><em>Let's get you ready to scale.</em></h1>
      <p>
        Not every business is ready for enterprise ERP — and that's okay.
        The SAJET SMB track gives you the tools, structure, and mentorship
        to build the foundation that enterprise-level systems require.
      </p>
    </div>
  </section>

  <!-- What you get -->
  <section class="smb-section">
    <div class="section-inner">
      <div class="section-label">What's included</div>
      <h2>The path from startup to SMB</h2>
      <div class="track-grid">
        <div class="track-card">
          <div class="track-num">01</div>
          <h3>Business formation</h3>
          <p>Get your LLC or corporation set up correctly. We partner with <strong>Jeturing Atlas</strong> to fast-track legal structure, EIN, and banking in the US.</p>
          <a href="https://jeturing.com/atlas" class="track-link" target="_blank" rel="noopener">Explore Atlas →</a>
        </div>
        <div class="track-card">
          <div class="track-num">02</div>
          <h3>SMB starter tools</h3>
          <p>Basic invoicing, expense tracking, and payment acceptance at a price that fits a growing business — $0 to get started, scales with your revenue.</p>
          <a href="/signup" class="track-link">Start for free →</a>
        </div>
        <div class="track-card">
          <div class="track-num">03</div>
          <h3>Upgrade when ready</h3>
          <p>Once you cross $5,000/month in revenue or reach 5+ employees, you automatically qualify for the full SAJET platform — your data migrates seamlessly.</p>
          <button class="track-link" onclick={() => goto('/mpos')}>See full platform →</button>
        </div>
      </div>
    </div>
  </section>

  <!-- Jeturing Atlas callout -->
  <section class="atlas-section">
    <div class="atlas-inner">
      <div class="atlas-badge">Powered by Jeturing</div>
      <h2>Not incorporated yet? Start with Atlas.</h2>
      <p>
        Jeturing Atlas is our business formation accelerator. Get your LLC registered,
        open a business bank account, and get your first payment link — all in one week.
        It's the bridge between idea and business.
      </p>
      <div class="atlas-features">
        <div class="af">✓ LLC / Corp formation</div>
        <div class="af">✓ EIN registration</div>
        <div class="af">✓ Business bank account</div>
        <div class="af">✓ First payment link</div>
        <div class="af">✓ Mentorship calls</div>
        <div class="af">✓ Path to SAJET</div>
      </div>
      <a href="https://jeturing.com/atlas" class="cta-atlas" target="_blank" rel="noopener">
        Start with Atlas →
      </a>
    </div>
  </section>

  <!-- CTA back to funnels -->
  <section class="already-section">
    <div class="already-inner">
      <p>Already have your LLC? Jump directly to the plan that fits your business:</p>
      <div class="niche-links">
        <a href="/mpos" class="niche-btn">💳 Accept Payments</a>
        <a href="/build" class="niche-btn">🔧 Custom Dev</a>
        <a href="/cpa" class="niche-btn">📊 Accounting Firms</a>
        <a href="/partners" class="niche-btn">🤝 Become a Partner</a>
      </div>
    </div>
  </section>

  <footer class="smb-footer">
    <div class="footer-inner">
      <a href="/" class="footer-logo">
        <div class="logo-mark small">S</div>
        <span>SAJET</span>
      </a>
      <div class="footer-links">
        <a href="/terms">Terms</a>
        <a href="/privacy">Privacy</a>
        <a href="/login">Sign in</a>
      </div>
    </div>
  </footer>
</div>

<style>
  .smb-root {
    background: #020e1f; color: #f0ede8;
    font-family: 'Inter', sans-serif;
    min-height: 100vh; overflow-x: hidden;
  }
  .smb-bg {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
  }
  .smb-overlay {
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 20% 20%, rgba(0,59,115,.3) 0%, transparent 60%);
  }
  .smb-glow {
    position: absolute; border-radius: 50%; filter: blur(80px); opacity: .15;
  }
  .glow-1 { width: 500px; height: 500px; background: #22c55e; top: -10%; left: -10%; }
  .glow-2 { width: 400px; height: 400px; background: #0ea5e9; bottom: 10%; right: -5%; }

  .smb-nav {
    position: relative; z-index: 10;
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.5rem 2rem; max-width: 1100px; margin: 0 auto;
  }
  .nav-logo { display: flex; align-items: center; gap: .6rem; text-decoration: none; font-weight: 700; color: #fff; }
  .logo-mark {
    width: 36px; height: 36px; border-radius: 8px;
    background: linear-gradient(135deg, #22c55e, #0ea5e9);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; color: #020e1f;
  }
  .logo-mark.small { width: 28px; height: 28px; font-size: .8rem; }
  .nav-login { color: #94a3b8; font-size: .9rem; text-decoration: none; }

  .smb-hero {
    position: relative; z-index: 1;
    min-height: 65vh; display: flex; align-items: center;
  }
  .hero-inner {
    max-width: 780px; margin: 0 auto; padding: 5rem 2rem 3rem;
    text-align: center;
  }
  .hero-badge {
    display: inline-block; padding: .35rem .9rem;
    border: 1px solid rgba(34,197,94,.35); border-radius: 100px;
    font-size: .75rem; font-weight: 600; letter-spacing: .08em;
    color: #22c55e; text-transform: uppercase; margin-bottom: 1.5rem;
  }
  .smb-hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2rem, 4.5vw, 3.5rem);
    font-weight: 800; line-height: 1.15; color: #fff; margin-bottom: 1.2rem;
  }
  .smb-hero h1 em { color: #22c55e; font-style: normal; }
  .smb-hero p { font-size: 1.1rem; color: #94a3b8; line-height: 1.65; max-width: 580px; margin: 0 auto; }

  .smb-section { position: relative; z-index: 1; padding: 4rem 2rem; }
  .section-inner { max-width: 1000px; margin: 0 auto; text-align: center; }
  .section-label {
    font-size: .75rem; text-transform: uppercase; letter-spacing: .1em;
    color: #64748b; margin-bottom: .8rem;
  }
  .smb-section h2 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.7rem, 3vw, 2.4rem); font-weight: 700;
    color: #fff; margin-bottom: 3rem;
  }
  .track-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
  .track-card {
    padding: 2rem; border-radius: 14px;
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    text-align: left; position: relative;
  }
  .track-num {
    font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 800;
    color: rgba(255,255,255,.08); position: absolute; top: 1rem; right: 1.2rem;
  }
  .track-card h3 { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; color: #fff; margin-bottom: .6rem; }
  .track-card p { font-size: .88rem; color: #94a3b8; line-height: 1.55; margin-bottom: 1.2rem; }
  .track-link {
    color: #22c55e; font-size: .88rem; font-weight: 600;
    text-decoration: none; background: none; border: none; cursor: pointer; padding: 0;
    transition: opacity .2s;
  }
  .track-link:hover { opacity: .7; }

  .atlas-section {
    position: relative; z-index: 1;
    background: rgba(34,197,94,.06); border-top: 1px solid rgba(34,197,94,.15); border-bottom: 1px solid rgba(34,197,94,.15);
    padding: 5rem 2rem;
  }
  .atlas-inner { max-width: 700px; margin: 0 auto; text-align: center; }
  .atlas-badge {
    display: inline-block; padding: .3rem .8rem;
    background: rgba(34,197,94,.12); border-radius: 6px;
    font-size: .75rem; font-weight: 600; color: #22c55e; text-transform: uppercase;
    letter-spacing: .06em; margin-bottom: 1.2rem;
  }
  .atlas-inner h2 { font-family: 'Space Grotesk', sans-serif; font-size: clamp(1.6rem,3vw,2.2rem); font-weight: 700; color: #fff; margin-bottom: 1rem; }
  .atlas-inner p { color: #94a3b8; line-height: 1.65; margin-bottom: 2rem; }
  .atlas-features {
    display: flex; flex-wrap: wrap; justify-content: center; gap: .6rem 1.5rem;
    margin-bottom: 2.5rem;
  }
  .af { font-size: .88rem; color: #d1fae5; }
  .cta-atlas {
    display: inline-flex; align-items: center; gap: .5rem;
    background: #22c55e; color: #020e1f;
    font-weight: 700; font-size: 1rem;
    padding: .9rem 2.2rem; border-radius: 8px;
    text-decoration: none; transition: transform .15s, box-shadow .15s;
  }
  .cta-atlas:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(34,197,94,.3); }

  .already-section { position: relative; z-index: 1; padding: 4rem 2rem; text-align: center; }
  .already-inner { max-width: 800px; margin: 0 auto; }
  .already-inner p { color: #64748b; margin-bottom: 1.5rem; font-size: .95rem; }
  .niche-links { display: flex; flex-wrap: wrap; justify-content: center; gap: .75rem; }
  .niche-btn {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .65rem 1.3rem; border-radius: 8px;
    border: 1px solid rgba(255,255,255,.12);
    color: #d1d5db; font-size: .9rem;
    text-decoration: none; transition: all .2s;
  }
  .niche-btn:hover { border-color: rgba(255,255,255,.35); color: #fff; background: rgba(255,255,255,.04); }

  .smb-footer { position: relative; z-index: 1; border-top: 1px solid rgba(255,255,255,.06); padding: 2rem; }
  .footer-inner { max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
  .footer-logo { display: flex; align-items: center; gap: .5rem; text-decoration: none; color: #fff; font-weight: 700; font-size: .9rem; }
  .footer-links { display: flex; gap: 1.5rem; }
  .footer-links a { color: #64748b; font-size: .85rem; text-decoration: none; }
  .footer-links a:hover { color: #fff; }

  @media (max-width: 640px) {
    .niche-links { gap: .5rem; }
    .track-grid { grid-template-columns: 1fr; }
  }
</style>
