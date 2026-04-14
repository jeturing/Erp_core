<script lang="ts">
  import FunnelPage from '$lib/components/FunnelPage.svelte';
  import type { ComponentProps } from 'svelte';

  type Config = ComponentProps<typeof FunnelPage>['config'];

  const config: Config = {
    niche: 'cpa',
    badge: '📊 For CPAs & Accounting Firms',
    headline: 'One workspace.<br/><em>Every client. Every book.</em>',
    subheadline: 'SAJET gives your accounting firm a multi-client workspace with shared invoicing, payroll sync, and white-label portals — under your brand.',
    videoUrl: 'https://cdn.coverr.co/videos/coverr-accountant-working-on-laptop-3791/1080p.mp4',
    accentColor: '#F59E0B',
    stats: [
      { value: '1 login', label: 'All clients' },
      { value: '∞', label: 'Client seats' },
      { value: 'Auto', label: 'Reconciliation' },
      { value: '100%', label: 'Branded portal' },
    ],
    painPoints: [
      'Switching between 5 different tools to manage different clients',
      'Sharing login credentials or creating duplicate accounts per client',
      'Month-end reconciliation that takes days of manual work',
      'Clients emailing you PDFs instead of giving you live data access',
      'No professional portal — clients see generic SaaS branding',
      'Chasing clients for bank statements and expense receipts every month',
    ],
    solution: [
      { icon: '🗂️', title: 'Multi-client workspace', desc: 'Manage every client from one login. Separate books, one dashboard. Switch contexts in one click.' },
      { icon: '🏷️', title: 'Your-firm.sajet.us portal', desc: 'Clients log into your branded portal. They upload documents, view reports, and approve expenses — all in your workspace.' },
      { icon: '⚙️', title: 'Automated reconciliation', desc: 'Bank feeds, Stripe payouts, and expense categorization happen automatically. You review, not re-enter.' },
      { icon: '📤', title: 'Export to any format', desc: 'One-click export to your preferred reporting format — PDF, Excel, or directly to your filing software.' },
    ],
    features: [
      { icon: '👥', title: 'Unlimited client sub-accounts', desc: 'Each client gets their own isolated space. You have admin visibility over all of them.' },
      { icon: '📊', title: 'Consolidated P&L and balance sheet', desc: 'See all clients\' financial health at a glance. Flag anomalies before your clients even notice.' },
      { icon: '📬', title: 'Automated document requests', desc: 'SAJET automatically reminds clients to upload receipts, invoices, and statements on schedule.' },
      { icon: '🔐', title: 'Role-based access per client', desc: 'Assign view-only, edit, or approval roles. Clients can\'t see each other\'s data.' },
      { icon: '📱', title: 'Mobile app for clients', desc: 'Clients photograph receipts, approve payments, and check their balances from anywhere.' },
    ],
    cta: 'Set up my firm workspace',
    quizTitle: 'Tell us about your practice.',
    quizSteps: [
      {
        id: 'has_entity',
        question: 'Is your accounting firm legally registered?',
        hint: 'We require a registered CPA firm or accounting practice.',
        type: 'single',
        field: 'has_entity',
        options: [
          { label: '✓ Yes, registered firm', value: 'true' },
          { label: '🌱 I\'m an independent freelancer', value: 'false', disqualify: true, reason: 'no_entity' },
        ],
      },
      {
        id: 'client_count',
        question: 'How many business clients does your firm currently serve?',
        hint: 'Our multi-client workspace is designed for firms with 2+ active clients.',
        type: 'number',
        field: 'client_count',
        required: true,
      },
      {
        id: 'industry',
        question: 'What\'s your firm\'s primary specialization?',
        type: 'single',
        field: 'industry',
        options: [
          { label: '🏪 Small business / SMB', value: 'smb_accounting' },
          { label: '🍽️ Restaurants & food service', value: 'restaurant_accounting' },
          { label: '🏗️ Construction & real estate', value: 'construction_accounting' },
          { label: '🛒 Retail & e-commerce', value: 'retail_accounting' },
          { label: '📋 General accounting', value: 'general_accounting' },
        ],
      },
    ],
  };
</script>

<svelte:head>
  <title>SAJET for CPAs — Multi-Client Accounting Workspace</title>
  <meta name="description" content="One login, every client. White-label accounting portal for CPA firms. Automated reconciliation, document management, and client portals under your brand." />
</svelte:head>

<FunnelPage {config} />
