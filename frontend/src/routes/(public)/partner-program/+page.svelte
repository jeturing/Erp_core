<script lang="ts">
  import FunnelPage from '$lib/components/FunnelPage.svelte';
  import type { ComponentProps } from 'svelte';

  type Config = ComponentProps<typeof FunnelPage>['config'];

  const config: Config = {
    niche: 'partners',
    badge: '🤝 Partner Program · 50% Revenue Share',
    headline: 'Sell SAJET.<br/><em>Keep half of everything.</em>',
    subheadline: 'Join 50+ commercial partners earning recurring income. You bring the client, we handle the tech and support. 50% revenue share on every subscription.',
    videoUrl: 'https://cdn.coverr.co/videos/coverr-business-meeting-in-a-modern-office-4912/1080p.mp4',
    accentColor: '#A855F7',
    stats: [
      { value: '50%', label: 'Revenue share' },
      { value: '$0', label: 'Onboarding cost' },
      { value: '48h', label: 'Client activation' },
      { value: 'MRR', label: 'Recurring income' },
    ],
    painPoints: [
      'One-time commissions that disappear after the sale is closed',
      'Recommending software you can\'t customize for your clients',
      'No white-label option — you send clients straight to the vendor',
      'Chasing invoices and manual reporting for every referral',
      'No dedicated portal to manage your book of business',
      'Building your own tech stack to serve SMB clients costs a fortune',
    ],
    solution: [
      { icon: '💰', title: '50% MRR split — forever', desc: 'Not a one-time fee. Every month your client pays, you earn half. Build a real recurring income stream.' },
      { icon: '🎨', title: 'White-label portal', desc: 'Your clients see your brand. Custom subdomain, your logo. We power it, you own the relationship.' },
      { icon: '⚡', title: 'We handle all support', desc: 'Our team handles onboarding, training, and technical support. You focus on growing your book.' },
      { icon: '📊', title: 'Real-time partner dashboard', desc: 'Track MRR, commissions, client status, and pipeline in your dedicated partner portal.' },
    ],
    features: [
      { icon: '🏷️', title: 'Branded client portal at your-brand.sajet.us', desc: 'Fully white-labeled. Your clients interact with your brand — not ours.' },
      { icon: '📋', title: 'Pre-built proposals and decks', desc: 'Close deals faster with ready-made sales materials, case studies, and pricing sheets.' },
      { icon: '🔔', title: 'Automated commission tracking', desc: 'Every payment is logged in real time. No spreadsheets. Monthly payouts via ACH or wire.' },
      { icon: '🎓', title: 'Partner certification program', desc: 'Free training and certification. Certified partners get priority leads and higher tiers.' },
      { icon: '📞', title: 'Dedicated partner success manager', desc: 'Direct access to a Sajet team member for deal support, escalations, and co-selling.' },
    ],
    cta: 'Apply to the Partner Program',
    quizTitle: 'Let\'s see if you\'re a fit for our partner program.',
    quizSteps: [
      {
        id: 'has_entity',
        question: 'Do you have a registered business or consulting firm?',
        hint: 'We partner with agencies, consultants, accountants, and resellers.',
        type: 'single',
        field: 'has_entity',
        options: [
          { label: '✓ Yes, registered', value: 'true' },
          { label: '🌱 Freelance / not yet', value: 'false', disqualify: true, reason: 'no_entity' },
        ],
      },
      {
        id: 'client_count',
        question: 'How many active business clients do you currently serve?',
        hint: 'We require a minimum of 2 existing business clients.',
        type: 'number',
        field: 'client_count',
        required: true,
      },
      {
        id: 'has_sales_team',
        question: 'Do you have at least one dedicated sales or business development person?',
        hint: 'Our top partners have a dedicated person focused on client acquisition.',
        type: 'single',
        field: 'has_sales_team',
        options: [
          { label: '✓ Yes, we have sales', value: 'true' },
          { label: '✗ It\'s just me', value: 'false', disqualify: true, reason: 'no_sales_team' },
        ],
      },
    ],
  };
</script>

<svelte:head>
  <title>SAJET Partner Program — 50% Revenue Share on Every Client</title>
  <meta name="description" content="Become a SAJET commercial partner. White-label ERP platform, 50% MRR split, dedicated dashboard. Apply now." />
</svelte:head>

<FunnelPage {config} />
