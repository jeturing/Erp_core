<script lang="ts">
  import FunnelPage from '$lib/components/FunnelPage.svelte';
  import type { ComponentProps } from 'svelte';

  type Config = ComponentProps<typeof FunnelPage>['config'];

  const config: Config = {
    niche: 'mpos',
    badge: '⚡ MPOS · Stripe · NFC · QR',
    headline: 'Accept payments anywhere.<br/><em>Keep 100% of your revenue.</em>',
    subheadline: 'SAJET MPOS turns your phone or tablet into a full POS terminal — card, NFC, QR, and split payments. No hardware fees. Powered by Stripe.',
    videoUrl: 'https://cdn.coverr.co/videos/coverr-person-using-a-pos-machine-6628/1080p.mp4',
    accentColor: '#00FF9F',
    stats: [
      { value: '$0', label: 'Monthly fee' },
      { value: '2.9%', label: 'Per transaction' },
      { value: '<48h', label: 'Payout to bank' },
      { value: '99.9%', label: 'Uptime' },
    ],
    painPoints: [
      'Paying $50–$200/month for a POS system that barely works offline',
      'Losing sales because your terminal doesn\'t accept NFC or QR',
      'Waiting 5–7 days to receive your own money',
      'Manual reconciliation between your POS and accounting',
      'Separate apps for invoicing, inventory, and payments — nothing talks to each other',
      'No visibility into which products or staff are performing',
    ],
    solution: [
      { icon: '📱', title: 'Mobile-first POS', desc: 'Works on any iOS or Android device. No proprietary hardware required — just your phone or tablet.' },
      { icon: '⚡', title: 'Instant Stripe payouts', desc: 'Funds deposited in under 48 hours. Real-time balance tracking and payout scheduling built in.' },
      { icon: '🔗', title: 'Synced with your ERP', desc: 'Every sale auto-posts to your books. Inventory, commissions, and reports update in real time.' },
      { icon: '📶', title: 'Works offline', desc: 'Queue transactions without internet. Sync automatically when you reconnect — never lose a sale.' },
    ],
    features: [
      { icon: '💳', title: 'Card, NFC, QR & cash in one screen', desc: 'Accept all payment methods with a single app. No dongles, no extra readers.' },
      { icon: '🧾', title: 'Digital receipts via WhatsApp or email', desc: 'Send branded receipts instantly. Customers keep records, you reduce paper costs.' },
      { icon: '📊', title: 'Sales analytics & staff performance', desc: 'See top-selling items, busiest hours, and team productivity from any device.' },
      { icon: '🏷️', title: 'Inventory & modifiers', desc: 'Variants, combos, and forced modifiers. Kitchen display integration available.' },
      { icon: '💰', title: 'Split bills & tips', desc: 'Table-side splitting and tip prompts built in. Perfect for restaurants, bars, and salons.' },
    ],
    cta: 'Activate my MPOS',
    quizTitle: 'Let\'s make sure SAJET MPOS is the right fit for you.',
    quizSteps: [
      {
        id: 'has_entity',
        question: 'Do you have a registered business or LLC?',
        hint: 'Stripe requires a legal entity to process payments.',
        type: 'single',
        field: 'has_entity',
        options: [
          { label: '✓ Yes, I have one', value: 'true' },
          { label: '🌱 Not yet — working on it', value: 'false', disqualify: true, reason: 'no_entity' },
        ],
      },
      {
        id: 'monthly_volume',
        question: 'What\'s your estimated monthly sales volume?',
        hint: 'This helps us recommend the right plan for your transaction volume.',
        type: 'single',
        field: 'monthly_volume',
        options: [
          { label: 'Under $2,000', value: 'under_2k' },
          { label: '$2,000 – $10,000', value: '2k_10k' },
          { label: '$10,000 – $50,000', value: '10k_50k' },
          { label: 'Over $50,000', value: 'over_50k' },
        ],
      },
      {
        id: 'industry',
        question: 'What type of business are you?',
        type: 'single',
        field: 'industry',
        options: [
          { label: '🍽️ Restaurant / Food', value: 'restaurant' },
          { label: '🛍️ Retail / Store', value: 'retail' },
          { label: '💆 Services / Salon', value: 'services' },
          { label: '🚚 Delivery / Mobile', value: 'delivery' },
          { label: '🏪 Other', value: 'other' },
        ],
      },
    ],
  };
</script>

<svelte:head>
  <title>SAJET MPOS — Accept Payments Anywhere with Stripe</title>
  <meta name="description" content="Turn any phone into a full POS terminal. Card, NFC, QR payments powered by Stripe. No monthly fees. Built for Latin businesses in the US." />
</svelte:head>

<FunnelPage {config} />
