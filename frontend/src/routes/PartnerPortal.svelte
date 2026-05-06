<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    LogOut, LayoutDashboard, Users, Briefcase, DollarSign, CreditCard,
    UserCircle, Plus, TrendingUp, Building2, ExternalLink, RefreshCw,
    Package, FileText, Download, Palette, Pencil, Trash2,
    ChevronRight, ArrowUpRight, Loader2,
    Globe, ChevronDown, ChevronUp, Link2, Rocket, Target, CheckCircle2, AlertTriangle
  } from 'lucide-svelte';
  import { auth, currentUser } from '../lib/stores';
  import { Spinner } from '../lib/components';
  import { goto } from '$app/navigation';
  import PartnerOnboarding from '../lib/components/PartnerOnboarding.svelte';
  import partnerPortalApi from '../lib/api/partnerPortal';
  import type {
    AddonSubscriptionItem,
    PartnerOnboardingStatus, PartnerDashboard, PartnerLeadsResponse,
    PartnerLeadItem, PartnerProfile, PartnerClientItem, PartnerCommissionItem, PartnerPortalInvoiceItem, ServiceCatalogItemType,
    PartnerDeploymentsResponse, PartnerDeploymentItem, BlueprintPackageItem,
  } from '../lib/types';
  import { formatDate } from '../lib/utils/formatters';

  // State
  let loading = true;
  let error = '';
  let activeTab: 'dashboard' | 'deployments' | 'leads' | 'clients' | 'services' | 'invoices' | 'commissions' | 'stripe' | 'branding' | 'profile' = 'dashboard';

  // Data
  let onboardingStatus: PartnerOnboardingStatus | null = null;
  let dashboard: PartnerDashboard | null = null;
  let leads: PartnerLeadsResponse | null = null;
  let deployments: PartnerDeploymentsResponse | null = null;
  let blueprintPackages: BlueprintPackageItem[] = [];
  let clients: { items: PartnerClientItem[]; total: number } | null = null;
  let invoices: { items: PartnerPortalInvoiceItem[]; total: number; summary: { total_billed: number; total_paid: number; total_pending: number } } | null = null;
  let commissions: { items: PartnerCommissionItem[]; total: number; summary: { total_earned: number; pending: number; paid: number } } | null = null;
  let profile: PartnerProfile | null = null;
  let editingProfile = false;
  let savingProfile = false;
  let profileForm = { company_name: '', legal_name: '', tax_id: '', contact_name: '', phone: '', country: '', address: '' };
  let showOnboarding = false;

  // Client services
  let selectedServiceClientId: number | null = null;
  let selectedServiceClientValue = '';
  let clientServiceCatalog: ServiceCatalogItemType[] = [];
  let clientServiceSubscriptions: AddonSubscriptionItem[] = [];
  let servicesLoading = false;
  let servicesError = '';
  let servicesMessage = '';
  let servicesMessageType: 'success' | 'error' = 'success';
  let purchasingServiceId: number | null = null;
  let savingClientSettings = false;
  let clientEditForm = {
    company_name: '',
    contact_email: '',
    contact_name: '',
    phone: '',
    country: '',
    plan_name: 'basic',
    user_count: 1,
    notes: '',
  };

  // New Lead form
  let showNewLead = false;
  let editingLeadId: number | null = null;
  let newLead = { company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
  let savingLead = false;

  // New Client form
  let showNewClient = false;
  let newClient = { company_name: '', contact_email: '', subdomain: '', plan_name: 'basic', user_count: 1, contact_name: '', notes: '' };
  let savingClient = false;
  let clientCredentials: { admin_login: string; admin_password: string; subdomain: string; url: string } | null = null;
  let showClientCredentials = false;

  // Automated deployment wizard
  let showDeploymentWizard = false;
  let savingDeployment = false;
  let selectedDeployment: PartnerDeploymentItem | null = null;
  let deploymentPollHandle: ReturnType<typeof setTimeout> | null = null;
  let deploymentWizardStep = 1;
  let deploymentForm = {
    lead_id: '',
    company_name: '',
    contact_name: '',
    contact_email: '',
    phone: '',
    country_code: 'US',
    industry: 'retail',
    blueprint_package_name: '',
    subdomain: '',
    plan_name: 'basic',
    user_count: 1,
    billing_mode: 'partner_direct',
    notes: '',
  };

  // Client domains (expandable)
  let expandedClientId: number | null = null;
  let clientDomains: Map<number, Array<{
    domain: string; sources: string[]; is_active: boolean;
    verification_status: string | null; custom_domain_id: number | null;
  }>> = new Map();
  let domainsLoading: number | null = null;

  // Branding state
  let brandingData: {
    is_configured: boolean; white_label_enabled: boolean; profile_id?: number;
    brand_name: string; logo_url: string | null; favicon_url: string | null;
    primary_color: string; secondary_color: string;
    support_email: string | null; support_url: string | null;
    portal_url: string | null; terms_url: string | null; privacy_url: string | null;
    custom_css: string | null; is_active: boolean; updated_at?: string | null;
  } | null = null;
  let brandingForm = {
    brand_name: '', logo_url: '', favicon_url: '',
    primary_color: '#4F46E5', secondary_color: '#7C3AED',
    support_email: '', support_url: '', portal_url: '',
    terms_url: '', privacy_url: '', custom_css: '',
  };
  let savingBranding = false;
  let brandingMessage = '';
  let brandingMessageType: 'success' | 'error' = 'success';

  $: showOnboarding = Boolean(onboardingStatus && onboardingStatus.current_step < 4);

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount || 0);
  }

  function statusColor(status: string | null): string {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-700';
      case 'contacted': return 'bg-indigo-100 text-indigo-700';
      case 'qualified': case 'in_qualification': return 'bg-amber-100 text-amber-700';
      case 'proposal': return 'bg-purple-100 text-purple-700';
      case 'won': return 'bg-green-100 text-green-700';
      case 'tenant_requested': return 'bg-orange-100 text-orange-700';
      case 'provisioning_running': return 'bg-sky-100 text-sky-700';
      case 'provisioning_failed': return 'bg-red-100 text-red-700';
      case 'tenant_ready': case 'invoiced': return 'bg-teal-100 text-teal-700';
      case 'lost': return 'bg-red-100 text-red-700';
      case 'active': return 'bg-green-100 text-green-700';
      case 'pending': return 'bg-amber-100 text-amber-700';
      case 'paid': return 'bg-green-100 text-green-700';
      case 'void': return 'bg-red-100 text-red-700';
      case 'issued': case 'open': case 'overdue': case 'past_due': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  function phaseLabel(phase: string): string {
    const phaseMap: Record<string, string> = {
      strategy: 'Alineacion',
      blueprint: 'Blueprint',
      provisioning: 'Tenant',
      validation: 'Validacion',
      training: 'Capacitacion',
      handoff: 'Activo',
    };
    return phaseMap[phase] || phase;
  }

  function deploymentStatusLabel(status: string): string {
    const statusMap: Record<string, string> = {
      tenant_requested: 'Solicitado',
      provisioning_running: 'Provisioning',
      provisioning_failed: 'Bloqueado',
      invoiced: 'Facturado',
      active: 'Activo',
    };
    return statusMap[status] || status;
  }

  function applyLeadToDeploymentForm() {
    const leadId = Number(deploymentForm.lead_id || 0);
    const lead = leads?.items?.find((item) => Number(item.id) === leadId);
    if (!lead) return;
    deploymentForm = {
      ...deploymentForm,
      company_name: lead.company_name || deploymentForm.company_name,
      contact_name: lead.contact_name || deploymentForm.contact_name,
      contact_email: lead.contact_email || deploymentForm.contact_email,
      phone: lead.phone || deploymentForm.phone,
      country_code: lead.country || deploymentForm.country_code,
      notes: lead.notes || deploymentForm.notes,
    };
  }

  function suggestBlueprintForIndustry() {
    const industry = deploymentForm.industry.toLowerCase();
    const match = blueprintPackages.find((pkg) => {
      const haystack = `${pkg.name} ${pkg.display_name} ${pkg.description || ''}`.toLowerCase();
      return haystack.includes(industry);
    }) || blueprintPackages.find((pkg) => pkg.is_default) || blueprintPackages[0];
    if (match && !deploymentForm.blueprint_package_name) {
      deploymentForm = { ...deploymentForm, blueprint_package_name: match.name };
    }
  }

  function partnerInvoicePrimaryAction(invoice: PartnerPortalInvoiceItem) {
    if (invoice.payment_url) {
      return { label: 'Pagar', href: invoice.payment_url };
    }
    if (invoice.download_url) {
      return { label: 'Descargar PDF', href: invoice.download_url };
    }
    if (invoice.view_url) {
      return { label: 'Ver factura', href: invoice.view_url };
    }
    return null;
  }

  function partnerInvoiceSecondaryDownload(invoice: PartnerPortalInvoiceItem): string | null {
    if (!invoice.download_url || invoice.download_url === invoice.payment_url) {
      return null;
    }
    return invoice.download_url;
  }

  function isEmailPackage(item: Pick<ServiceCatalogItemType, 'service_code' | 'metadata_json'>): boolean {
    return item.service_code === 'postal_email_package' || item.metadata_json?.kind === 'postal_email_package';
  }

  function formatInteger(value: number | null | undefined): string {
    return new Intl.NumberFormat('es-DO').format(Number(value || 0));
  }

  function getSelectedServiceClient(): PartnerClientItem | null {
    const id = Number(selectedServiceClientId);
    return clients?.items?.find((client) => Number(client.customer_id) === id) || null;
  }

  $: availableClientServices = clientServiceCatalog;
  $: activeClientServices = clientServiceSubscriptions;

  function clearDeploymentPolling() {
    if (deploymentPollHandle) {
      clearTimeout(deploymentPollHandle);
      deploymentPollHandle = null;
    }
  }

  function isDeploymentProcessing(dep: PartnerDeploymentItem | null | undefined): boolean {
    if (!dep) return false;
    return dep.is_running || dep.provisioning_status === 'pending' || dep.provisioning_status === 'running';
  }

  function syncSelectedDeployment() {
    if (!deployments?.items?.length) {
      selectedDeployment = null;
      return;
    }
    if (!selectedDeployment) {
      selectedDeployment = deployments.items[0];
      return;
    }
    const updated = deployments.items.find((item) => item.id === selectedDeployment?.id);
    if (updated) {
      selectedDeployment = updated;
    }
  }

  function upsertDeployment(dep: PartnerDeploymentItem) {
    if (!deployments) return;
    const items = [...deployments.items];
    const index = items.findIndex((item) => item.id === dep.id);
    if (index >= 0) {
      items[index] = dep;
    } else {
      items.unshift(dep);
    }
    deployments = {
      ...deployments,
      items,
      total: items.length,
      summary: {
        ...deployments.summary,
        total: items.length,
      },
    };
    selectedDeployment = dep;
  }

  function getDeploymentHeadline(dep: PartnerDeploymentItem | null | undefined): string {
    if (!dep) return 'Preparando despliegue';
    if (dep.provisioning_status === 'failed') return 'El provisioning encontró un bloqueo';
    if (isDeploymentProcessing(dep)) return 'Estamos creando la cuenta y validando disponibilidad';
    if (dep.handoff_status === 'completed') return 'Tenant entregado y activo';
    return 'Tenant listo para handoff comercial';
  }

  function getDeploymentSupportText(dep: PartnerDeploymentItem | null | undefined): string {
    if (!dep) return 'El flujo se reflejará aquí en tiempo real.';
    if (dep.provisioning_status === 'failed') return dep.last_error || 'Revisa el detalle y reintenta el provisioning.';
    if (isDeploymentProcessing(dep)) return 'Puedes seguir trabajando mientras SAJET crea el tenant, publica la ruta y prueba el acceso.';
    if (dep.availability_test?.ok === false) return 'La cuenta fue creada, pero la validación pública quedó pendiente. Revisa el detalle antes del handoff.';
    if (dep.handoff_status === 'completed') return 'El cliente ya puede operar con el tenant entregado.';
    return 'La cuenta fue creada correctamente y ya puedes coordinar el handoff con el cliente.';
  }

  function getPhaseVisualState(dep: PartnerDeploymentItem, phase: { key: string; target: number }): 'done' | 'current' | 'upcoming' {
    const progress = Number(dep.progress_percent || 0);
    if (progress >= phase.target) return 'done';
    const currentPhase = dep.phases.find((item) => progress < item.target);
    return currentPhase?.key === phase.key ? 'current' : 'upcoming';
  }

  function getAvailabilityBadge(dep: PartnerDeploymentItem | null | undefined) {
    const test = dep?.availability_test;
    if (!test) {
      return { label: 'Pendiente', tone: 'bg-gray-100 text-gray-600 border-gray-200' };
    }
    if (test.ok) {
      return { label: 'Validado', tone: 'bg-green-100 text-green-700 border-green-200' };
    }
    return { label: 'Revisión manual', tone: 'bg-amber-100 text-amber-700 border-amber-200' };
  }

  async function pollDeployment(deploymentId: number, immediate = false) {
    clearDeploymentPolling();
    const execute = async () => {
      try {
        const deployment = await partnerPortalApi.getDeployment(deploymentId);
        upsertDeployment(deployment);
        if (deployment.provisioning_status === 'ready' && deployment.tenant_url) {
          clients = await partnerPortalApi.getClients();
        }
        if (!isDeploymentProcessing(deployment)) {
          await loadDeploymentCockpit();
          return;
        }
      } catch (err) {
        error = err instanceof Error ? err.message : 'No se pudo refrescar el despliegue';
      }
      deploymentPollHandle = window.setTimeout(() => {
        void pollDeployment(deploymentId, true);
      }, 2500);
    };

    if (immediate) {
      await execute();
      return;
    }

    deploymentPollHandle = window.setTimeout(() => {
      void execute();
    }, 800);
  }

  function hydrateClientEditForm() {
    const client = getSelectedServiceClient();
    if (!client) return;
    clientEditForm = {
      company_name: client.company_name || '',
      contact_email: client.email || '',
      contact_name: client.contact_name || '',
      phone: client.phone || '',
      country: client.country || '',
      plan_name: client.plan || 'basic',
      user_count: Number(client.user_count || 1),
      notes: client.notes || '',
    };
  }

  function selectServiceClient(customerId: number | null) {
    selectedServiceClientId = customerId;
    selectedServiceClientValue = customerId ? String(customerId) : '';
    hydrateClientEditForm();
  }

  async function loadData() {
    loading = true;
    error = '';
    try {
      onboardingStatus = await partnerPortalApi.getOnboardingStatus();
      if (onboardingStatus.current_step >= 4) {
        await loadTabData();
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al cargar el portal';
    } finally {
      loading = false;
    }
  }

  async function loadTabData() {
    try {
      switch (activeTab) {
        case 'dashboard':
          [dashboard, deployments] = await Promise.all([
            partnerPortalApi.getDashboard(),
            partnerPortalApi.getDeployments(),
          ]);
          break;
        case 'deployments':
          await loadDeploymentCockpit();
          break;
        case 'leads':
          leads = await partnerPortalApi.getLeads();
          break;
        case 'clients':
          clients = await partnerPortalApi.getClients();
          break;
        case 'services':
          await ensureClientsLoaded();
          await loadClientServices(selectedServiceClientId);
          break;
        case 'invoices':
          invoices = await partnerPortalApi.getInvoices();
          break;
        case 'commissions':
          commissions = await partnerPortalApi.getCommissions();
          break;
        case 'profile':
          profile = await partnerPortalApi.getProfile();
          break;
        case 'branding':
          brandingData = await partnerPortalApi.getBranding();
          if (brandingData) {
            brandingForm = {
              brand_name: brandingData.brand_name || '',
              logo_url: brandingData.logo_url || '',
              favicon_url: brandingData.favicon_url || '',
              primary_color: brandingData.primary_color || '#4F46E5',
              secondary_color: brandingData.secondary_color || '#7C3AED',
              support_email: brandingData.support_email || '',
              support_url: brandingData.support_url || '',
              portal_url: brandingData.portal_url || '',
              terms_url: brandingData.terms_url || '',
              privacy_url: brandingData.privacy_url || '',
              custom_css: brandingData.custom_css || '',
            };
          }
          break;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error';
    }
  }

  async function ensureClientsLoaded() {
    if (!clients) {
      clients = await partnerPortalApi.getClients();
    }
    const currentExists = clients.items.some((client) => Number(client.customer_id) === Number(selectedServiceClientId));
    if ((!selectedServiceClientId || !currentExists) && clients.items.length > 0) {
      selectServiceClient(clients.items[0].customer_id);
    } else if (selectedServiceClientId) {
      selectedServiceClientValue = String(selectedServiceClientId);
      hydrateClientEditForm();
    }
  }

  async function loadClientServices(customerId: number | null) {
    servicesLoading = true;
    servicesError = '';
    try {
      if (!customerId) {
        clientServiceCatalog = [];
        clientServiceSubscriptions = [];
        return;
      }

      const [catalogRes, subscriptionsRes] = await Promise.all([
        partnerPortalApi.getClientServiceCatalog(customerId),
        partnerPortalApi.getClientServiceSubscriptions(customerId),
      ]);
      clientServiceCatalog = catalogRes.items ?? [];
      clientServiceSubscriptions = subscriptionsRes.items ?? [];
      hydrateClientEditForm();
    } catch (err) {
      servicesError = err instanceof Error ? err.message : 'Error al cargar servicios del cliente';
    } finally {
      servicesLoading = false;
    }
  }

  async function handleServiceClientChange() {
    const nextId = selectedServiceClientValue ? Number(selectedServiceClientValue) : null;
    selectServiceClient(nextId);
    await loadClientServices(nextId);
  }

  async function switchTab(tab: typeof activeTab) {
    if (tab !== 'deployments') {
      clearDeploymentPolling();
    }
    activeTab = tab;
    error = '';
    brandingMessage = '';
    await loadTabData();
    if (tab === 'deployments' && selectedDeployment && isDeploymentProcessing(selectedDeployment)) {
      await pollDeployment(selectedDeployment.id);
    }
  }

  async function loadDeploymentCockpit() {
    const [deploymentRes, leadRes, packageRes, clientRes] = await Promise.all([
      partnerPortalApi.getDeployments(),
      partnerPortalApi.getLeads(),
      partnerPortalApi.getBlueprintPackages(),
      partnerPortalApi.getClients(),
    ]);
    deployments = deploymentRes;
    leads = leadRes;
    blueprintPackages = packageRes.items ?? [];
    clients = clientRes;
    syncSelectedDeployment();
    suggestBlueprintForIndustry();
    if (selectedDeployment && isDeploymentProcessing(selectedDeployment)) {
      await pollDeployment(selectedDeployment.id);
    }
  }

  function resetDeploymentForm() {
    deploymentForm = {
      lead_id: '',
      company_name: '',
      contact_name: '',
      contact_email: '',
      phone: '',
      country_code: 'US',
      industry: 'retail',
      blueprint_package_name: blueprintPackages.find((pkg) => pkg.is_default)?.name || blueprintPackages[0]?.name || '',
      subdomain: '',
      plan_name: 'basic',
      user_count: 1,
      billing_mode: 'partner_direct',
      notes: '',
    };
    deploymentWizardStep = 1;
  }

  async function openDeploymentWizard() {
    showDeploymentWizard = !showDeploymentWizard;
    if (showDeploymentWizard) {
      await loadDeploymentCockpit();
      resetDeploymentForm();
    }
  }

  async function saveBrandingProfile() {
    savingBranding = true;
    brandingMessage = '';
    try {
      const payload: Record<string, string> = {};
      for (const [key, value] of Object.entries(brandingForm)) {
        if (value) payload[key] = value;
      }
      const result = await partnerPortalApi.updateBranding(payload);
      brandingMessage = result.message || 'Perfil de marca guardado exitosamente';
      brandingMessageType = 'success';
      // Refresh data
      brandingData = await partnerPortalApi.getBranding();
    } catch (err) {
      brandingMessage = err instanceof Error ? err.message : 'Error al guardar';
      brandingMessageType = 'error';
    } finally {
      savingBranding = false;
    }
  }

  async function saveProfile() {
    if (!profile) return;
    savingProfile = true;
    try {
      await partnerPortalApi.saveProfile(profileForm);
      // Actualizar el objeto profile con los datos guardados
      Object.assign(profile, profileForm);
      editingProfile = false;
      // toasts.success('Perfil actualizado exitosamente');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al guardar perfil';
    } finally {
      savingProfile = false;
    }
  }

  function startEditProfile() {
    if (!profile) return;
    profileForm = {
      company_name: profile.company_name || '',
      legal_name: profile.legal_name || '',
      tax_id: profile.tax_id || '',
      contact_name: profile.contact_name || '',
      phone: profile.phone || '',
      country: profile.country || '',
      address: profile.address || '',
    };
    editingProfile = true;
  }

  function cancelEditProfile() {
    editingProfile = false;
  }

  async function saveLead() {
    if (!newLead.company_name.trim()) return;
    savingLead = true;
    try {
      if (editingLeadId) {
        await partnerPortalApi.updateLead(editingLeadId, newLead);
      } else {
        await partnerPortalApi.createLead(newLead);
      }
      newLead = { company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
      editingLeadId = null;
      showNewLead = false;
      leads = await partnerPortalApi.getLeads();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al guardar lead';
    } finally {
      savingLead = false;
    }
  }

  function startEditLead(lead: PartnerLeadItem) {
    editingLeadId = lead.id;
    newLead = { ...lead };
    showNewLead = true;
  }

  async function deleteLead(leadId: number, company: string) {
    if (!confirm(`¿Eliminar el lead "${company}"?`)) return;
    try {
      await partnerPortalApi.deleteLead(leadId);
      leads = await partnerPortalApi.getLeads();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al eliminar lead';
    }
  }

  function closeLeadForm() {
    showNewLead = false;
    editingLeadId = null;
    newLead = { company_name: '', contact_name: '', contact_email: '', phone: '', country: '', notes: '', estimated_monthly_value: 0 };
  }

  async function createClient() {
    if (!newClient.company_name.trim() || !newClient.contact_email.trim() || !newClient.subdomain.trim()) return;
    savingClient = true;
    error = '';
    try {
      const result = await partnerPortalApi.createClient(newClient);
      newClient = { company_name: '', contact_email: '', subdomain: '', plan_name: 'basic', user_count: 1, contact_name: '', notes: '' };
      showNewClient = false;
      activeTab = 'deployments';
      selectedDeployment = result.deployment;
      await loadDeploymentCockpit();
      await pollDeployment(result.deployment.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al crear cliente';
    } finally {
      savingClient = false;
    }
  }

  async function startDeployment() {
    if (!deploymentForm.company_name.trim() || !deploymentForm.contact_email.trim() || !deploymentForm.subdomain.trim()) return;
    savingDeployment = true;
    error = '';
    try {
      const result = await partnerPortalApi.startDeployment({
        company_name: deploymentForm.company_name,
        contact_email: deploymentForm.contact_email,
        subdomain: deploymentForm.subdomain,
        plan_name: deploymentForm.plan_name,
        user_count: Number(deploymentForm.user_count || 1),
        contact_name: deploymentForm.contact_name,
        phone: deploymentForm.phone,
        country_code: deploymentForm.country_code,
        industry: deploymentForm.industry,
        notes: deploymentForm.notes,
        lead_id: deploymentForm.lead_id ? Number(deploymentForm.lead_id) : null,
        blueprint_package_name: deploymentForm.blueprint_package_name,
        billing_mode: deploymentForm.billing_mode,
      });
      showDeploymentWizard = false;
      activeTab = 'deployments';
      selectedDeployment = result.deployment;
      await loadDeploymentCockpit();
      await pollDeployment(result.deployment.id);
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo iniciar el despliegue';
    } finally {
      savingDeployment = false;
    }
  }

  async function retryDeployment(dep: PartnerDeploymentItem) {
    savingDeployment = true;
    error = '';
    try {
      const result = await partnerPortalApi.retryDeploymentProvisioning(dep.id);
      selectedDeployment = result.deployment;
      await loadDeploymentCockpit();
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo reintentar el provisioning';
    } finally {
      savingDeployment = false;
    }
  }

  async function completeHandoff(dep: PartnerDeploymentItem) {
    savingDeployment = true;
    error = '';
    try {
      const result = await partnerPortalApi.completeDeploymentHandoff(dep.id);
      selectedDeployment = result.deployment;
      await loadDeploymentCockpit();
    } catch (err) {
      error = err instanceof Error ? err.message : 'No se pudo completar el handoff';
    } finally {
      savingDeployment = false;
    }
  }

  async function purchaseClientService(item: ServiceCatalogItemType) {
    if (!selectedServiceClientId) return;
    purchasingServiceId = item.id;
    servicesMessage = '';
    try {
      const result = await partnerPortalApi.purchaseClientService(selectedServiceClientId, item.id, 1);
      servicesMessage = result.message || `Servicio ${item.name} asignado al tenant`;
      servicesMessageType = 'success';
      await loadClientServices(selectedServiceClientId);
      if (result.invoice?.payment_url) {
        window.open(result.invoice.payment_url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      servicesMessage = err instanceof Error ? err.message : 'No se pudo asignar el servicio al tenant';
      servicesMessageType = 'error';
    } finally {
      purchasingServiceId = null;
    }
  }

  async function saveClientSettings() {
    const customerId = selectedServiceClientId;
    if (!customerId) return;
    savingClientSettings = true;
    servicesMessage = '';
    servicesError = '';
    try {
      const result = await partnerPortalApi.updateClient(customerId, {
        company_name: clientEditForm.company_name,
        contact_email: clientEditForm.contact_email,
        contact_name: clientEditForm.contact_name,
        phone: clientEditForm.phone,
        country: clientEditForm.country,
        plan_name: clientEditForm.plan_name,
        user_count: Number(clientEditForm.user_count || 1),
        notes: clientEditForm.notes,
      });
      clients = await partnerPortalApi.getClients();
      selectServiceClient(result.client.customer_id);
      await loadClientServices(result.client.customer_id);
      servicesMessage = result.sync?.success
        ? 'Cliente actualizado y sincronizado con Odoo.'
        : `Cliente actualizado en SAJET. Sincronización pendiente: ${result.sync?.message || 'Odoo no respondió'}`;
      servicesMessageType = result.sync?.success ? 'success' : 'error';
    } catch (err) {
      servicesError = err instanceof Error ? err.message : 'No se pudo actualizar el cliente';
    } finally {
      savingClientSettings = false;
    }
  }

  async function openStripeDashboard() {
    try {
      const result = await partnerPortalApi.getStripeDashboardLink();
      if (result.url) window.open(result.url, '_blank');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al abrir Stripe';
    }
  }

  function handleLogout() {
    auth.logout();
    goto('/login');
  }

  function handleOnboardingComplete() {
    showOnboarding = false;
    loadData();
  }

  function copyClientCredentials() {
    if (!clientCredentials) return;
    const text = `URL: ${clientCredentials.url}\nLogin: ${clientCredentials.admin_login}\nPassword: ${clientCredentials.admin_password}`;
    navigator.clipboard.writeText(text);
  }

  async function toggleClientDomains(customerId: number) {
    if (expandedClientId === customerId) {
      expandedClientId = null;
      return;
    }
    expandedClientId = customerId;
    if (!clientDomains.has(customerId)) {
      domainsLoading = customerId;
      try {
        const result = await partnerPortalApi.getClientDomains(customerId);
        clientDomains.set(customerId, result.domains);
        clientDomains = clientDomains; // trigger reactivity
      } catch (err) {
        error = err instanceof Error ? err.message : 'Error cargando dominios';
      } finally {
        domainsLoading = null;
      }
    }
  }

  function sourceLabel(source: string): string {
    switch (source) {
      case 'base': return 'Sajet';
      case 'custom': return 'Custom';
      case 'odoo': return 'Website';
      default: return source;
    }
  }

  function sourceBadge(source: string): string {
    switch (source) {
      case 'base': return 'bg-blue-100 text-blue-700';
      case 'custom': return 'bg-purple-100 text-purple-700';
      case 'odoo': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  }

  onMount(loadData);
  onDestroy(clearDeploymentPolling);
</script>

{#if loading}
  <div class="min-h-screen bg-[#F5F3EF] flex items-center justify-center">
    <div class="text-center">
      <Spinner size="lg" />
      <p class="mt-4 text-gray-500">Cargando portal...</p>
    </div>
  </div>
{:else if showOnboarding && onboardingStatus}
  <PartnerOnboarding
    {onboardingStatus}
    {profile}
    on:complete={handleOnboardingComplete}
  />
{:else}
  <div class="min-h-screen bg-[#F5F3EF]">
    <!-- Top Navbar -->
    <header class="bg-[#1a1a1a] border-b border-[#2a2a2a] sticky top-0 z-20">
      <div class="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-[#C05A3C] flex items-center justify-center">
            <span class="text-white font-bold text-sm">S</span>
          </div>
          <span class="text-white font-semibold tracking-[0.05em] text-sm">SAJET</span>
          <span class="text-gray-400 text-xs">PARTNER PORTAL</span>
        </div>

        <div class="flex items-center gap-2">
          <Building2 class="w-4 h-4 text-gray-400" />
          <span class="text-gray-300 text-sm font-medium">
            {dashboard?.partner?.company_name || $currentUser?.company_name || 'Partner'}
          </span>
        </div>

        <button
          class="flex items-center gap-1.5 text-[11px] font-semibold tracking-[0.08em] text-gray-400 hover:text-white uppercase transition-colors"
          on:click={handleLogout}
        >
          <LogOut class="w-3.5 h-3.5" />
          CERRAR SESIÓN
        </button>
      </div>
    </header>

    <!-- Tab Navigation -->
    <nav class="bg-white border-b border-gray-200 sticky top-[52px] z-10">
      <div class="max-w-7xl mx-auto px-6 flex gap-0">
        {#each [
          { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { key: 'deployments', label: 'Despliegues', icon: Rocket },
          { key: 'leads', label: 'Leads', icon: Briefcase },
          { key: 'clients', label: 'Clientes', icon: Users },
          { key: 'services', label: 'Servicios', icon: Package },
          { key: 'invoices', label: 'Facturas', icon: FileText },
          { key: 'commissions', label: 'Comisiones', icon: DollarSign },
          { key: 'stripe', label: 'Stripe', icon: CreditCard },
          { key: 'branding', label: 'Mi Marca', icon: Palette },
          { key: 'profile', label: 'Mi Perfil', icon: UserCircle },
        ] as tab}
          <button
            class="flex items-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors border-b-2
              {activeTab === tab.key
                ? 'text-[#C05A3C] border-[#C05A3C]'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'}"
            on:click={() => switchTab(tab.key as typeof activeTab)}
          >
            {#if true}{@const C = tab.icon as any}<C class="w-4 h-4" />{/if}
            {tab.label}
          </button>
        {/each}
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-6">
      {#if error}
        <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>
      {/if}

      <!-- ═══ DASHBOARD ═══ -->
      {#if activeTab === 'dashboard' && dashboard}
        <!-- KPI Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Leads Activos</span>
            <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{dashboard.kpis.active_leads}</p>
            <p class="text-xs text-gray-400 mt-0.5">{dashboard.kpis.total_leads} totales</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Conversión</span>
            <p class="text-2xl font-bold text-[#4A7C59] mt-1">{dashboard.kpis.conversion_rate}%</p>
            <p class="text-xs text-gray-400 mt-0.5">{dashboard.kpis.won_leads} ganados</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Clientes Activos</span>
            <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{dashboard.kpis.active_clients}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pipeline Estimado</span>
            <p class="text-2xl font-bold text-[#C05A3C] mt-1">{formatCurrency(dashboard.kpis.estimated_pipeline)}</p>
            <p class="text-xs text-gray-400 mt-0.5">/mes potencial</p>
          </div>
        </div>

        {#if deployments}
          <div class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <div class="flex items-center justify-between gap-3 mb-4">
              <div>
                <h2 class="text-sm font-bold text-[#1a1a1a]">Cockpit de despliegues</h2>
                <p class="text-xs text-gray-500 mt-1">Pipeline automatico desde lead hasta tenant activo.</p>
              </div>
              <button
                class="bg-[#1a1a1a] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#333] transition-colors flex items-center gap-1.5"
                on:click={() => switchTab('deployments')}
              >
                <Rocket class="w-4 h-4" /> Abrir cockpit
              </button>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-2">
              {#each deployments.phases as phase}
                <div class="rounded-lg border border-gray-200 bg-gray-50 p-3 min-h-[92px]">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Semana {phase.week}</span>
                    <span class="text-xs font-bold text-[#C05A3C]">{deployments.summary.pipeline[phase.key] || 0}</span>
                  </div>
                  <p class="text-sm font-semibold text-[#1a1a1a] mt-2">{phase.label}</p>
                  <div class="h-1.5 rounded-full bg-gray-200 mt-3 overflow-hidden">
                    <div class="h-full bg-[#C05A3C]" style={`width: ${Math.min(100, phase.target)}%`}></div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Revenue Cards -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <div class="flex items-center justify-between mb-3">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total Ganado</span>
              <TrendingUp class="w-4 h-4 text-[#4A7C59]" />
            </div>
            <p class="text-3xl font-bold text-[#1a1a1a]">{formatCurrency(dashboard.kpis.total_earned)}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Comisiones Pendientes</span>
            <p class="text-3xl font-bold text-amber-600 mt-2">{formatCurrency(dashboard.kpis.pending_commissions)}</p>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Comisiones Pagadas</span>
            <p class="text-3xl font-bold text-[#4A7C59] mt-2">{formatCurrency(dashboard.kpis.paid_commissions)}</p>
          </div>
        </div>

        <!-- Stripe Balance + Quick Actions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {#if dashboard.stripe_balance}
            <div class="bg-white rounded-xl border border-gray-200 p-5">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3 block">Balance Stripe</span>
              <div class="flex gap-8">
                <div>
                  <span class="text-xs text-gray-400">Disponible</span>
                  <p class="text-xl font-bold text-[#4A7C59]">{formatCurrency(dashboard.stripe_balance.available)}</p>
                </div>
                <div>
                  <span class="text-xs text-gray-400">Pendiente</span>
                  <p class="text-xl font-bold text-amber-600">{formatCurrency(dashboard.stripe_balance.pending)}</p>
                </div>
              </div>
              <button
                class="mt-4 text-sm text-[#635BFF] hover:underline flex items-center gap-1"
                on:click={openStripeDashboard}
              >
                <ExternalLink class="w-3 h-3" /> Abrir Dashboard Stripe
              </button>
            </div>
          {/if}

          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3 block">Acciones Rápidas</span>
            <div class="space-y-2">
              <button
                class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-200 hover:border-[#C05A3C] transition-colors flex items-center justify-between text-sm"
                on:click={openDeploymentWizard}
              >
                <span class="flex items-center gap-2"><Rocket class="w-4 h-4 text-[#C05A3C]" /> Iniciar despliegue automatico</span>
                <ChevronRight class="w-4 h-4 text-gray-400" />
              </button>
              <button
                class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-200 hover:border-[#C05A3C] transition-colors flex items-center justify-between text-sm"
                on:click={() => { switchTab('leads'); showNewLead = true; }}
              >
                <span class="flex items-center gap-2"><Plus class="w-4 h-4 text-[#C05A3C]" /> Registrar lead manual</span>
                <ChevronRight class="w-4 h-4 text-gray-400" />
              </button>
              <button
                class="w-full text-left px-3 py-2.5 rounded-lg border border-gray-200 hover:border-[#C05A3C] transition-colors flex items-center justify-between text-sm"
                on:click={() => switchTab('commissions')}
              >
                <span class="flex items-center gap-2"><DollarSign class="w-4 h-4 text-[#C05A3C]" /> Ver mis comisiones</span>
                <ChevronRight class="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>
        </div>

      <!-- ═══ DEPLOYMENTS ═══ -->
      {:else if activeTab === 'deployments'}
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-4">
          <div>
            <h2 class="text-lg font-bold text-[#1a1a1a]">Despliegues Automáticos</h2>
            <p class="text-sm text-gray-500 mt-1">Pipeline visual, tenant real, factura y handoff en un solo flujo.</p>
          </div>
          <button
            class="bg-[#C05A3C] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center gap-1.5"
            on:click={openDeploymentWizard}
          >
            <Rocket class="w-4 h-4" /> Nuevo despliegue
          </button>
        </div>

        {#if deployments}
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div class="bg-white rounded-xl border border-gray-200 p-4">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">En proceso</span>
              <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{deployments.summary.in_progress}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Activos</span>
              <p class="text-2xl font-bold text-[#4A7C59] mt-1">{deployments.summary.active}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Bloqueos</span>
              <p class="text-2xl font-bold text-red-600 mt-1">{deployments.summary.blocked}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Avance promedio</span>
              <p class="text-2xl font-bold text-[#C05A3C] mt-1">{deployments.summary.avg_progress}%</p>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-6 gap-2 mb-4">
            {#each deployments.phases as phase}
              <div class="bg-white rounded-xl border border-gray-200 p-3">
                <div class="flex items-center justify-between">
                  <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">S{phase.week}</span>
                  <span class="text-sm font-bold text-[#C05A3C]">{deployments.summary.pipeline[phase.key] || 0}</span>
                </div>
                <p class="text-sm font-semibold text-[#1a1a1a] mt-2">{phase.label}</p>
              </div>
            {/each}
          </div>
        {/if}

        {#if showDeploymentWizard}
          <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-sm font-bold text-[#1a1a1a]">Wizard de despliegue automático</h3>
                <p class="text-xs text-gray-500 mt-1">Paso {deploymentWizardStep} de 3</p>
              </div>
              <div class="flex items-center gap-2">
                {#each [1, 2, 3] as step}
                  <span class="w-8 h-1.5 rounded-full {deploymentWizardStep >= step ? 'bg-[#C05A3C]' : 'bg-gray-200'}"></span>
                {/each}
              </div>
            </div>

            {#if deploymentWizardStep === 1}
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                <select bind:value={deploymentForm.lead_id} on:change={applyLeadToDeploymentForm}
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                  <option value="">Crear desde cero</option>
                  {#each leads?.items || [] as lead}
                    <option value={lead.id}>{lead.company_name} · {lead.status || 'new'}</option>
                  {/each}
                </select>
                <input type="text" bind:value={deploymentForm.company_name} placeholder="Empresa *"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                <input type="email" bind:value={deploymentForm.contact_email} placeholder="Email contacto *"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                <input type="text" bind:value={deploymentForm.contact_name} placeholder="Contacto"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                <input type="text" bind:value={deploymentForm.phone} placeholder="Teléfono"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                <input type="text" bind:value={deploymentForm.country_code} placeholder="País (US, DO...)"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              </div>
            {:else if deploymentWizardStep === 2}
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                <select bind:value={deploymentForm.industry} on:change={suggestBlueprintForIndustry}
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                  <option value="retail">Retail / POS</option>
                  <option value="finance">Finanzas</option>
                  <option value="services">Servicios</option>
                  <option value="restaurant">Restaurante</option>
                  <option value="ecommerce">Ecommerce</option>
                </select>
                <select bind:value={deploymentForm.blueprint_package_name}
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                  <option value="">Blueprint estándar</option>
                  {#each blueprintPackages as pkg}
                    <option value={pkg.name}>{pkg.display_name} · {pkg.module_count} módulos</option>
                  {/each}
                </select>
                <select bind:value={deploymentForm.plan_name}
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                  <option value="basic">Basic</option>
                  <option value="pro">Professional</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <input type="number" min="1" max="999" bind:value={deploymentForm.user_count} placeholder="Usuarios"
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                <select bind:value={deploymentForm.billing_mode}
                  class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                  <option value="partner_direct">Partner cobra vía Connect</option>
                  <option value="partner_pays_for_client">Partner cobra externo y paga a Jeturing</option>
                </select>
                <div class="flex items-center gap-1">
                  <input type="text" bind:value={deploymentForm.subdomain} placeholder="subdominio *"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                  <span class="text-xs text-gray-400 whitespace-nowrap">.sajet.us</span>
                </div>
              </div>
            {:else}
              <div class="grid grid-cols-1 lg:grid-cols-[1fr,0.9fr] gap-4">
                <div class="rounded-xl border border-gray-200 p-4">
                  <h4 class="text-sm font-bold text-[#1a1a1a] mb-3">Resumen automático</h4>
                  <div class="grid grid-cols-2 gap-3 text-sm">
                    <div><span class="text-gray-400 block text-xs">Cliente</span>{deploymentForm.company_name || '—'}</div>
                    <div><span class="text-gray-400 block text-xs">Tenant</span>{deploymentForm.subdomain || '—'}.sajet.us</div>
                    <div><span class="text-gray-400 block text-xs">Plan</span>{deploymentForm.plan_name}</div>
                    <div><span class="text-gray-400 block text-xs">Blueprint</span>{deploymentForm.blueprint_package_name || 'estándar'}</div>
                  </div>
                </div>
                <div class="rounded-xl border border-gray-200 p-4">
                  <h4 class="text-sm font-bold text-[#1a1a1a] mb-3">KPIs iniciales</h4>
                  <div class="space-y-2 text-sm text-gray-600">
                    <div class="flex items-center gap-2"><Target class="w-4 h-4 text-[#C05A3C]" /> ROI positivo en trimestre 1</div>
                    <div class="flex items-center gap-2"><Target class="w-4 h-4 text-[#C05A3C]" /> 30% reducción de costos operativos</div>
                    <div class="flex items-center gap-2"><Target class="w-4 h-4 text-[#C05A3C]" /> Despliegue en 5 semanas</div>
                  </div>
                </div>
              </div>
              <div class="mt-4 rounded-xl border border-[#F3D8CF] bg-[#FFF8F5] p-4">
                <div class="flex items-start gap-3">
                  <div class="w-10 h-10 rounded-full bg-[#C05A3C]/10 flex items-center justify-center flex-shrink-0">
                    <Rocket class="w-5 h-5 text-[#C05A3C]" />
                  </div>
                  <div>
                    <h4 class="text-sm font-bold text-[#1a1a1a]">Seguimiento visual en vivo</h4>
                    <p class="text-sm text-gray-600 mt-1">
                      Al confirmar, el portal te mostrará una barra de progreso con las fases de creación,
                      publicación y prueba de disponibilidad del tenant para que el socio no quede a ciegas.
                    </p>
                  </div>
                </div>
              </div>
            {/if}

            <div class="flex justify-between mt-4">
              <button class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700" on:click={() => showDeploymentWizard = false}>Cancelar</button>
              <div class="flex gap-2">
                {#if deploymentWizardStep > 1}
                  <button class="text-sm px-4 py-2 rounded-lg border border-gray-300" on:click={() => deploymentWizardStep -= 1}>Atrás</button>
                {/if}
                {#if deploymentWizardStep < 3}
                  <button class="bg-[#1a1a1a] text-white text-sm font-semibold px-5 py-2 rounded-lg" on:click={() => deploymentWizardStep += 1}>Continuar</button>
                {:else}
                  <button
                    class="bg-[#4A7C59] text-white text-sm font-semibold px-5 py-2 rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center gap-1.5 disabled:opacity-60"
                    on:click={startDeployment}
                    disabled={savingDeployment || !deploymentForm.company_name || !deploymentForm.contact_email || !deploymentForm.subdomain}
                  >
                    {#if savingDeployment}<Loader2 class="w-4 h-4 animate-spin" />{:else}<Rocket class="w-4 h-4" />{/if}
                    Provisionar ahora
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        {#if deployments?.items && deployments.items.length > 0}
          <div class="grid grid-cols-1 xl:grid-cols-[1fr,0.75fr] gap-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              {#each deployments.items as dep}
                <button
                  class="text-left bg-white rounded-xl border {selectedDeployment?.id === dep.id ? 'border-[#C05A3C]' : 'border-gray-200'} p-4 hover:border-[#C05A3C] transition-colors"
                  on:click={() => selectedDeployment = dep}
                >
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <h3 class="text-sm font-bold text-[#1a1a1a]">{dep.company_name}</h3>
                      <p class="text-xs text-gray-500 mt-1">{dep.subdomain}.sajet.us · {dep.plan_name}</p>
                    </div>
                    <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(dep.status)}">{deploymentStatusLabel(dep.status)}</span>
                  </div>
                  <div class="mt-4">
                    <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
                      <span>{phaseLabel(dep.phase)} · Semana {dep.week}</span>
                      <span>{dep.progress_percent}%</span>
                    </div>
                    <div class="h-2 rounded-full bg-gray-100 overflow-hidden">
                      <div class="h-full bg-[#C05A3C]" style={`width: ${dep.progress_percent}%`}></div>
                    </div>
                  </div>
                  <div class="grid grid-cols-3 gap-2 mt-4 text-xs">
                    <span class="flex items-center gap-1 {dep.provisioning_status === 'ready' ? 'text-[#4A7C59]' : dep.provisioning_status === 'failed' ? 'text-red-600' : 'text-gray-500'}">
                      {#if dep.provisioning_status === 'failed'}<AlertTriangle class="w-3 h-3" />{:else}<CheckCircle2 class="w-3 h-3" />{/if} Tenant
                    </span>
                    <span class="flex items-center gap-1 {dep.invoice ? 'text-[#4A7C59]' : 'text-gray-500'}"><FileText class="w-3 h-3" /> Factura</span>
                    <span class="flex items-center gap-1 {dep.handoff_status === 'completed' ? 'text-[#4A7C59]' : 'text-gray-500'}"><Users class="w-3 h-3" /> Handoff</span>
                  </div>
                </button>
              {/each}
            </div>

            <div class="bg-white rounded-xl border border-gray-200 p-5">
              {#if selectedDeployment || deployments.items[0]}
                {@const dep = selectedDeployment || deployments.items[0]}
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="flex items-center gap-2 flex-wrap">
                      <h3 class="text-base font-bold text-[#1a1a1a]">{dep.company_name}</h3>
                      <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(dep.status)}">{deploymentStatusLabel(dep.status)}</span>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">{dep.subdomain}.sajet.us · {phaseLabel(dep.phase)} · Semana {dep.week}</p>
                  </div>
                  {#if isDeploymentProcessing(dep)}
                    <div class="inline-flex items-center gap-2 rounded-full border border-[#F3D8CF] bg-[#FFF8F5] px-3 py-1 text-xs font-semibold text-[#C05A3C]">
                      <Loader2 class="w-3.5 h-3.5 animate-spin" /> En curso
                    </div>
                  {/if}
                </div>

                <div class="mt-4 rounded-2xl border border-[#F3D8CF] bg-gradient-to-br from-[#FFF8F5] to-white p-4">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <p class="text-xs font-semibold uppercase tracking-[0.16em] text-[#C05A3C]">Flujo guiado</p>
                      <h4 class="text-lg font-bold text-[#1a1a1a] mt-1">{getDeploymentHeadline(dep)}</h4>
                      <p class="text-sm text-gray-600 mt-1">{getDeploymentSupportText(dep)}</p>
                    </div>
                    <div class="text-right min-w-[72px]">
                      <p class="text-2xl font-bold text-[#C05A3C]">{dep.progress_percent}%</p>
                      <p class="text-[11px] text-gray-500">avance total</p>
                    </div>
                  </div>

                  <div class="mt-4 h-3 rounded-full bg-white border border-[#F3D8CF] overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-[#C05A3C] to-[#E38A68] transition-all duration-500" style={`width: ${dep.progress_percent}%`}></div>
                  </div>

                  <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
                    {#each dep.phases as phase}
                      {@const state = getPhaseVisualState(dep, phase)}
                      <div class="rounded-xl border px-3 py-3 transition-colors
                        {state === 'done'
                          ? 'border-green-200 bg-green-50'
                          : state === 'current'
                            ? 'border-[#F3D8CF] bg-white'
                            : 'border-gray-200 bg-gray-50'}">
                        <div class="flex items-center gap-2">
                          <span class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                            {state === 'done'
                              ? 'bg-green-600 text-white'
                              : state === 'current'
                                ? 'bg-[#C05A3C] text-white'
                                : 'bg-gray-200 text-gray-500'}">
                            {#if state === 'done'}
                              <CheckCircle2 class="w-4 h-4" />
                            {:else}
                              {phase.week}
                            {/if}
                          </span>
                          <div>
                            <p class="text-[10px] uppercase tracking-widest text-gray-500">Semana {phase.week}</p>
                            <p class="text-sm font-semibold text-[#1a1a1a]">{phase.label}</p>
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                    <div class="rounded-xl border border-gray-200 bg-white px-3 py-3">
                      <p class="text-[10px] uppercase tracking-widest text-gray-500">Tenant</p>
                      <p class="text-sm font-semibold mt-1 {dep.provisioning_status === 'failed' ? 'text-red-600' : dep.provisioning_status === 'ready' ? 'text-[#4A7C59]' : 'text-[#1a1a1a]'}">
                        {dep.provisioning_status === 'failed' ? 'Bloqueado' : dep.provisioning_status === 'ready' ? 'Creado' : 'Creándose'}
                      </p>
                    </div>
                    <div class="rounded-xl border {getAvailabilityBadge(dep).tone} px-3 py-3">
                      <p class="text-[10px] uppercase tracking-widest">Disponibilidad</p>
                      <p class="text-sm font-semibold mt-1">{getAvailabilityBadge(dep).label}</p>
                      {#if dep.availability_test?.status_code}
                        <p class="text-[11px] mt-1">HTTP {dep.availability_test.status_code}</p>
                      {/if}
                    </div>
                    <div class="rounded-xl border border-gray-200 bg-white px-3 py-3">
                      <p class="text-[10px] uppercase tracking-widest text-gray-500">Siguiente paso</p>
                      <p class="text-sm font-semibold text-[#1a1a1a] mt-1">
                        {dep.handoff_status === 'completed'
                          ? 'Operación activa'
                          : dep.provisioning_status === 'ready'
                            ? 'Coordinar handoff'
                            : 'Esperar validación'}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="mt-4 space-y-2">
                  {#each dep.checklist as item}
                    <div class="flex items-start gap-2 text-sm">
                      <CheckCircle2 class="w-4 h-4 mt-0.5 {item.done ? 'text-[#4A7C59]' : 'text-gray-300'}" />
                      <span class={item.done ? 'text-gray-700' : 'text-gray-400'}>{item.label}</span>
                    </div>
                  {/each}
                </div>

                {#if dep.last_error}
                  <div class="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{dep.last_error}</div>
                {/if}

                {#if dep.availability_test && dep.availability_test.ok === false}
                  <div class="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 text-xs text-amber-700">
                    La prueba pública quedó pendiente.
                    {#if dep.availability_test.error}
                      <span class="block mt-1">Detalle: {dep.availability_test.error}</span>
                    {/if}
                  </div>
                {/if}

                <div class="flex flex-wrap gap-2 mt-4">
                  {#if dep.tenant_url}
                    <a href={dep.tenant_url} target="_blank" rel="noreferrer" class="px-3 py-2 rounded-lg bg-[#1a1a1a] text-white text-xs font-semibold flex items-center gap-1">
                      <ExternalLink class="w-3 h-3" /> Ver tenant
                    </a>
                  {/if}
                  {#if dep.invoice?.payment_url}
                    <a href={dep.invoice.payment_url} target="_blank" rel="noreferrer" class="px-3 py-2 rounded-lg bg-[#C05A3C] text-white text-xs font-semibold flex items-center gap-1">
                      <CreditCard class="w-3 h-3" /> Pagar factura
                    </a>
                  {/if}
                  {#if dep.provisioning_status === 'failed'}
                    <button class="px-3 py-2 rounded-lg border border-gray-300 text-xs font-semibold flex items-center gap-1" on:click={() => retryDeployment(dep)} disabled={savingDeployment}>
                      <RefreshCw class="w-3 h-3" /> Reintentar
                    </button>
                  {/if}
                  {#if dep.provisioning_status === 'ready' && dep.handoff_status !== 'completed'}
                    <button class="px-3 py-2 rounded-lg border border-gray-300 text-xs font-semibold flex items-center gap-1" on:click={() => completeHandoff(dep)} disabled={savingDeployment}>
                      <CheckCircle2 class="w-3 h-3" /> Completar handoff
                    </button>
                  {/if}
                </div>
              {/if}
            </div>
          </div>
        {:else}
          <div class="py-14 text-center bg-white rounded-xl border border-gray-200">
            <Rocket class="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p class="text-sm text-gray-500">No hay despliegues todavía. Inicia el primero desde el wizard automático.</p>
          </div>
        {/if}

      <!-- ═══ LEADS ═══ -->
      {:else if activeTab === 'leads'}
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-[#1a1a1a]">Mis Leads</h2>
          <button
            class="bg-[#C05A3C] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center gap-1.5"
            on:click={() => showNewLead = !showNewLead}
          >
            <Plus class="w-4 h-4" /> Nuevo Lead
          </button>
        </div>

        <!-- New Lead Form -->
        {#if showNewLead}
          <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <h3 class="text-sm font-bold text-[#1a1a1a] mb-3">Registrar Lead</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <input type="text" bind:value={newLead.company_name} placeholder="Empresa *"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.contact_name} placeholder="Contacto"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="email" bind:value={newLead.contact_email} placeholder="Email"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.phone} placeholder="Teléfono"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="text" bind:value={newLead.country} placeholder="País"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="number" bind:value={newLead.estimated_monthly_value} placeholder="Valor mensual estimado"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <textarea bind:value={newLead.notes} placeholder="Notas" rows="2"
                class="sm:col-span-2 lg:col-span-3 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none resize-none"></textarea>
            </div>
            <div class="flex gap-2 mt-3 justify-end">
              <button class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700" on:click={() => showNewLead = false}>Cancelar</button>
              <button
                class="bg-[#4A7C59] text-white text-sm font-semibold px-5 py-2 rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center gap-1.5"
                on:click={createLead} disabled={savingLead}
              >
                {#if savingLead}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                Guardar Lead
              </button>
            </div>
          </div>
        {/if}

        <!-- Pipeline Summary -->
        {#if leads?.pipeline}
          <div class="flex flex-wrap gap-2 mb-4">
            {#each Object.entries(leads.pipeline) as [status, count]}
              {#if count > 0}
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold {statusColor(status)}">
                  {status}: {count}
                </span>
              {/if}
            {/each}
          </div>
        {/if}

        <!-- Leads Table -->
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if leads?.items && leads.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contacto</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Valor/Mes</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {#each leads.items as lead}
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3">
                        <span class="text-sm font-medium text-[#1a1a1a]">{lead.company_name}</span>
                        {#if lead.contact_email}
                          <br><span class="text-xs text-gray-400">{lead.contact_email}</span>
                        {/if}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600">{lead.contact_name || '—'}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(lead.status)}">
                          {lead.status || 'new'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-right text-sm font-medium text-[#1a1a1a]">
                        {formatCurrency(lead.estimated_monthly_value)}
                      </td>
                      <td class="px-4 py-3 text-xs text-gray-400">
                        {lead.registered_at ? formatDate(lead.registered_at) : '—'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <Briefcase class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">No tienes leads registrados. ¡Crea tu primer lead!</p>
            </div>
          {/if}
        </div>

      <!-- ═══ CLIENTS ═══ -->
      {:else if activeTab === 'clients'}
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-[#1a1a1a]">Mis Clientes</h2>
          <button
            class="bg-[#C05A3C] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#a94e33] transition-colors flex items-center gap-1.5"
            on:click={() => showNewClient = !showNewClient}
          >
            <Plus class="w-4 h-4" /> Nuevo Cliente
          </button>
        </div>

        <!-- New Client Form -->
        {#if showNewClient}
          <div class="bg-white rounded-xl border border-gray-200 p-5 mb-4">
            <h3 class="text-sm font-bold text-[#1a1a1a] mb-3">Crear Cliente y Aprovisionar Tenant</h3>
            <div class="mb-4 rounded-xl border border-[#F3D8CF] bg-[#FFF8F5] px-4 py-3 text-sm text-gray-600">
              Este flujo ahora crea la cuenta y te mueve al cockpit visual para seguir el progreso,
              la publicación y la prueba de disponibilidad del tenant en tiempo real.
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <input type="text" bind:value={newClient.company_name} placeholder="Empresa *"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <input type="email" bind:value={newClient.contact_email} placeholder="Email contacto *"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <div>
                <div class="flex items-center gap-1">
                  <input type="text" bind:value={newClient.subdomain} placeholder="subdominio *"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                  <span class="text-xs text-gray-400 whitespace-nowrap">.sajet.us</span>
                </div>
              </div>
              <input type="text" bind:value={newClient.contact_name} placeholder="Nombre contacto"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <select bind:value={newClient.plan_name}
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none bg-white">
                <option value="basic">Basic</option>
                <option value="pro">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
              <input type="number" bind:value={newClient.user_count} min="1" max="999" placeholder="# Usuarios"
                class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
              <textarea bind:value={newClient.notes} placeholder="Notas" rows="2"
                class="sm:col-span-2 lg:col-span-3 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none resize-none"></textarea>
            </div>
            <div class="flex gap-2 mt-3 justify-end">
              <button class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700" on:click={() => showNewClient = false}>Cancelar</button>
              <button
                class="bg-[#4A7C59] text-white text-sm font-semibold px-5 py-2 rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center gap-1.5"
                on:click={createClient} disabled={savingClient || !newClient.company_name || !newClient.contact_email || !newClient.subdomain}
              >
                {#if savingClient}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                Crear cuenta y seguir progreso
              </button>
            </div>
          </div>
        {/if}

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if clients?.items && clients.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Subdominio</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Plan</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Monto/Mes</th>
                    <th class="text-center px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Dominios</th>
                  </tr>
                </thead>
                <tbody>
                  {#each clients.items as client}
                    <tr
                      class="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                      on:click={() => toggleClientDomains(client.customer_id)}
                    >
                      <td class="px-4 py-3">
                        <span class="text-sm font-medium text-[#1a1a1a]">{client.company_name}</span>
                        <br><span class="text-xs text-gray-400">{client.email}</span>
                      </td>
                      <td class="px-4 py-3">
                        {#if client.subdomain}
                          <a href="https://{client.subdomain}.sajet.us" target="_blank"
                            class="text-sm text-[#C05A3C] hover:underline flex items-center gap-1"
                            on:click|stopPropagation>
                            {client.subdomain} <ExternalLink class="w-3 h-3" />
                          </a>
                        {:else}
                          <span class="text-xs text-gray-400">—</span>
                        {/if}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600 capitalize">{client.plan || '—'}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(client.status)}">
                          {client.status || '—'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-right text-sm font-medium">{formatCurrency(client.monthly_amount)}</td>
                      <td class="px-4 py-3 text-center">
                        <button
                          class="inline-flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-[#C05A3C] transition-colors"
                          on:click|stopPropagation={() => toggleClientDomains(client.customer_id)}
                        >
                          <Globe class="w-3.5 h-3.5" />
                          {#if domainsLoading === client.customer_id}
                            <Loader2 class="w-3 h-3 animate-spin" />
                          {:else if expandedClientId === client.customer_id}
                            <ChevronUp class="w-3 h-3" />
                          {:else}
                            <ChevronDown class="w-3 h-3" />
                          {/if}
                        </button>
                      </td>
                    </tr>

                    <!-- Expanded: Domains of client -->
                    {#if expandedClientId === client.customer_id}
                      <tr>
                        <td colspan="6" class="px-0 py-0">
                          <div class="bg-gray-50 border-t border-gray-200 px-6 py-4">
                            {#if domainsLoading === client.customer_id}
                              <div class="flex items-center gap-2 text-sm text-gray-500 py-2">
                                <Loader2 class="w-4 h-4 animate-spin" /> Cargando dominios...
                              </div>
                            {:else if clientDomains.has(client.customer_id)}
                              {@const domains = clientDomains.get(client.customer_id) || []}
                              <div class="flex items-center gap-2 mb-3">
                                <Link2 class="w-4 h-4 text-gray-500" />
                                <span class="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Dominios vinculados ({domains.length})
                                </span>
                              </div>
                              {#if domains.length === 0}
                                <p class="text-sm text-gray-500">Este cliente no tiene dominios registrados.</p>
                              {:else}
                                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                  {#each domains as d}
                                    <div class="flex items-center justify-between gap-2 bg-white rounded-lg border border-gray-200 px-3 py-2">
                                      <div class="flex items-center gap-2 min-w-0">
                                        <a
                                          href="https://{d.domain}"
                                          target="_blank"
                                          rel="noreferrer"
                                          class="text-sm text-[#1a1a1a] hover:text-[#C05A3C] hover:underline truncate"
                                          on:click|stopPropagation
                                        >
                                          {d.domain}
                                        </a>
                                        {#if d.is_active}
                                          <span class="flex-shrink-0 w-2 h-2 rounded-full bg-green-500" title="Activo"></span>
                                        {:else}
                                          <span class="flex-shrink-0 w-2 h-2 rounded-full bg-gray-300" title="Inactivo"></span>
                                        {/if}
                                      </div>
                                      <div class="flex gap-1 flex-shrink-0">
                                        {#each d.sources as src}
                                          <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold {sourceBadge(src)}">
                                            {sourceLabel(src)}
                                          </span>
                                        {/each}
                                      </div>
                                    </div>
                                  {/each}
                                </div>
                              {/if}
                            {:else}
                              <p class="text-sm text-gray-500">Error al cargar dominios.</p>
                            {/if}
                          </div>
                        </td>
                      </tr>
                    {/if}
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <Users class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">Aún no tienes clientes activos. ¡Crea tu primer cliente!</p>
            </div>
          {/if}
        </div>

      <!-- ═══ SERVICES ═══ -->
      {:else if activeTab === 'services'}
        <div class="space-y-4">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Servicios y Gestión del Cliente</h2>
              <p class="text-sm text-gray-500">Cambia de cliente, actualiza datos básicos y asigna servicios facturables al tenant.</p>
            </div>

            <div class="w-full lg:w-80">
              <label for="partner-service-client" class="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">Cliente</label>
              <select
                id="partner-service-client"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none"
                bind:value={selectedServiceClientValue}
                on:change={handleServiceClientChange}
              >
                {#if !clients?.items?.length}
                  <option value="">Sin clientes disponibles</option>
                {:else}
                  {#each clients.items as client}
                    <option value={String(client.customer_id)}>{client.company_name}</option>
                  {/each}
                {/if}
              </select>
            </div>
          </div>

          {#if servicesMessage}
            <div class="rounded border px-4 py-3 text-sm
              {servicesMessageType === 'success' ? 'border-green-200 bg-green-50 text-green-700' : 'border-red-200 bg-red-50 text-red-700'}">
              {servicesMessage}
            </div>
          {/if}

          {#if servicesError}
            <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{servicesError}</div>
          {/if}

          {#if selectedServiceClientId && getSelectedServiceClient()}
            {@const serviceClient = getSelectedServiceClient()}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Cliente</span>
                <p class="text-lg font-bold text-[#1a1a1a] mt-1">{serviceClient?.company_name}</p>
                <p class="text-xs text-gray-400 mt-1">{serviceClient?.email}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Plan actual</span>
                <p class="text-lg font-bold text-[#C05A3C] mt-1 capitalize">{serviceClient?.plan || '—'}</p>
                <p class="text-xs text-gray-400 mt-1">{serviceClient?.subdomain ? `${serviceClient.subdomain}.sajet.us` : 'Sin subdominio'}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Servicios activos</span>
                <p class="text-lg font-bold text-[#1a1a1a] mt-1">{activeClientServices.length}</p>
                <p class="text-xs text-gray-400 mt-1">Add-ons activos</p>
              </div>
            </div>

            <form on:submit|preventDefault={saveClientSettings} class="bg-white rounded-xl border border-gray-200 p-5">
              <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3 mb-4">
                <div>
                  <h3 class="text-sm font-bold text-[#1a1a1a]">Gestionar datos del cliente</h3>
                  <p class="text-xs text-gray-500 mt-1">Se actualiza SAJET y se intenta sincronizar al tenant Odoo vía jeturing_erp_sync.</p>
                </div>
                <button
                  type="submit"
                  class="bg-[#1a1a1a] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#333] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                  disabled={savingClientSettings || servicesLoading}
                >
                  {#if savingClientSettings}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                  Guardar y sincronizar
                </button>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                <div>
                  <label for="client-company-name" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Empresa</label>
                  <input id="client-company-name" bind:value={clientEditForm.company_name} required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-contact-email" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Email</label>
                  <input id="client-contact-email" type="email" bind:value={clientEditForm.contact_email} required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-contact-name" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Contacto</label>
                  <input id="client-contact-name" bind:value={clientEditForm.contact_name}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-phone" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Teléfono</label>
                  <input id="client-phone" bind:value={clientEditForm.phone}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-country" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">País</label>
                  <input id="client-country" bind:value={clientEditForm.country} placeholder="DO, US..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-plan" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Plan</label>
                  <select id="client-plan" bind:value={clientEditForm.plan_name}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none">
                    <option value="basic">Basic</option>
                    <option value="pro">Professional</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>
                <div>
                  <label for="client-users" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Usuarios</label>
                  <input id="client-users" type="number" min="1" max="999" bind:value={clientEditForm.user_count}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label for="client-subdomain" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Subdominio</label>
                  <input id="client-subdomain" value={serviceClient?.subdomain ? `${serviceClient.subdomain}.sajet.us` : 'Sin subdominio'} disabled
                    class="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg text-sm text-gray-500" />
                </div>
                <div class="md:col-span-2 lg:col-span-4">
                  <label for="client-notes" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Notas internas del socio</label>
                  <textarea id="client-notes" bind:value={clientEditForm.notes} rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none resize-none"></textarea>
                </div>
              </div>
            </form>

            {#if servicesLoading}
              <div class="py-12 flex justify-center">
                <Spinner size="lg" />
              </div>
            {:else}
              <div class="grid grid-cols-1 xl:grid-cols-[0.9fr,1.1fr] gap-6">
                <div class="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 class="text-sm font-bold text-[#1a1a1a] mb-4">Servicios activos</h3>

                  {#if activeClientServices.length === 0}
                    <div class="py-10 text-center">
                      <Package class="w-8 h-8 text-gray-300 mx-auto mb-2" />
                      <p class="text-sm text-gray-500">Este cliente no tiene servicios adicionales activos.</p>
                    </div>
                  {:else}
                    <div class="space-y-3">
                      {#each activeClientServices as addon}
                        <div class="rounded-lg border border-gray-200 bg-gray-50 p-4">
                          <div class="flex items-start justify-between gap-3">
                            <div>
                              <div class="flex items-center gap-2 flex-wrap">
                                <p class="text-sm font-semibold text-[#1a1a1a]">{addon.catalog_item?.name || addon.service_code || 'Servicio adicional'}</p>
                                {#if addon.catalog_item && isEmailPackage(addon.catalog_item)}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">Correo</span>
                                {:else if addon.catalog_item?.category}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-600">{addon.catalog_item.category}</span>
                                {/if}
                              </div>
                              {#if addon.catalog_item?.description}
                                <p class="text-xs text-gray-500 mt-1">{addon.catalog_item.description}</p>
                              {/if}
                            </div>
                            <div class="text-right">
                              <p class="text-sm font-semibold text-[#C05A3C]">{formatCurrency(addon.unit_price_monthly)}</p>
                              <p class="text-xs text-gray-500">x {addon.quantity} / mes</p>
                            </div>
                          </div>

                          {#if addon.catalog_item && isEmailPackage(addon.catalog_item)}
                            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                              <div class="rounded border border-blue-100 bg-blue-50 px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-blue-700">Cuota mensual</p>
                                <p class="text-sm font-semibold text-blue-900">{formatInteger(Number(addon.catalog_item.metadata_json?.email_quota_monthly || 0))} emails</p>
                              </div>
                              <div class="rounded border border-emerald-100 bg-emerald-50 px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-emerald-700">Ventana 60 min</p>
                                <p class="text-sm font-semibold text-emerald-900">{formatInteger(Number(addon.catalog_item.metadata_json?.email_burst_limit_60m || 0))} envíos</p>
                              </div>
                              <div class="rounded border border-amber-100 bg-amber-50 px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-amber-700">Sobreuso</p>
                                <p class="text-sm font-semibold text-amber-900">{formatCurrency(Number(addon.catalog_item.metadata_json?.email_overage_price || 0))}</p>
                              </div>
                            </div>
                          {:else if addon.catalog_item}
                            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                              <div class="rounded border border-gray-200 bg-white px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-gray-500">Categoría</p>
                                <p class="text-sm font-semibold text-gray-800">{addon.catalog_item.category || 'Servicio'}</p>
                              </div>
                              <div class="rounded border border-gray-200 bg-white px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-gray-500">Unidad</p>
                                <p class="text-sm font-semibold text-gray-800">{addon.catalog_item.unit}</p>
                              </div>
                              <div class="rounded border border-gray-200 bg-white px-3 py-2">
                                <p class="text-[10px] uppercase tracking-widest text-gray-500">Adquirido vía</p>
                                <p class="text-sm font-semibold text-gray-800">{addon.acquired_via}</p>
                              </div>
                            </div>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>

                <div class="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 class="text-sm font-bold text-[#1a1a1a] mb-4">Catálogo de servicios disponibles</h3>

                  {#if availableClientServices.length === 0}
                    <div class="py-10 text-center">
                      <Package class="w-8 h-8 text-gray-300 mx-auto mb-2" />
                      <p class="text-sm text-gray-500">No hay servicios adicionales configurados para este cliente.</p>
                    </div>
                  {:else}
                    <div class="space-y-4">
                      {#each availableClientServices as item}
                        <div class="rounded-xl border border-gray-200 p-4">
                          <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                            <div class="flex-1">
                              <div class="flex items-center gap-2 flex-wrap">
                                <p class="text-sm font-semibold text-[#1a1a1a]">{item.name}</p>
                                {#if item.is_included_in_plan}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-100 text-green-700">Incluido</span>
                                {/if}
                                {#if item.discount_percent && item.discount_percent > 0}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700">-{item.discount_percent}%</span>
                                {/if}
                                {#if isEmailPackage(item)}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">Correo</span>
                                {:else if item.category}
                                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-600">{item.category}</span>
                                {/if}
                              </div>

                              {#if item.description}
                                <p class="text-sm text-gray-500 mt-1">{item.description}</p>
                              {/if}

                              {#if isEmailPackage(item)}
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                                  <div class="rounded border border-blue-100 bg-blue-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-blue-700">Cuota mensual</p>
                                    <p class="text-sm font-semibold text-blue-900">{formatInteger(Number(item.metadata_json?.email_quota_monthly || 0))} emails</p>
                                  </div>
                                  <div class="rounded border border-emerald-100 bg-emerald-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-emerald-700">Ventana 60 min</p>
                                    <p class="text-sm font-semibold text-emerald-900">{formatInteger(Number(item.metadata_json?.email_burst_limit_60m || 0))} envíos</p>
                                  </div>
                                  <div class="rounded border border-amber-100 bg-amber-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-amber-700">Sobreuso</p>
                                    <p class="text-sm font-semibold text-amber-900">{formatCurrency(Number(item.metadata_json?.email_overage_price || 0))}</p>
                                  </div>
                                </div>
                              {:else}
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                                  <div class="rounded border border-gray-200 bg-gray-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-gray-500">Categoría</p>
                                    <p class="text-sm font-semibold text-gray-800">{item.category || 'Servicio'}</p>
                                  </div>
                                  <div class="rounded border border-gray-200 bg-gray-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-gray-500">Unidad</p>
                                    <p class="text-sm font-semibold text-gray-800">{item.unit}</p>
                                  </div>
                                  <div class="rounded border border-gray-200 bg-gray-50 px-3 py-2">
                                    <p class="text-[10px] uppercase tracking-widest text-gray-500">Cantidad mínima</p>
                                    <p class="text-sm font-semibold text-gray-800">{item.min_quantity || 1}</p>
                                  </div>
                                </div>
                              {/if}
                            </div>

                            <div class="w-full lg:w-56 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
                              <p class="text-[10px] uppercase tracking-widest text-gray-500">Precio mensual</p>
                              <p class="text-2xl font-bold text-[#C05A3C] mt-1">{formatCurrency(item.effective_price_monthly ?? item.price_monthly)}</p>
                              <p class="text-xs text-gray-500 mt-1">
                                {#if item.active_quantity && item.active_quantity > 0}
                                  Activo: {item.active_quantity} paquete(s)
                                {:else}
                                  Compra para el cliente
                                {/if}
                              </p>

                              <button
                                class="mt-4 w-full bg-[#C05A3C] text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-[#a94e33] transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                disabled={Boolean(item.is_included_in_plan) || purchasingServiceId === item.id}
                                on:click={() => purchaseClientService(item)}
                              >
                                {#if purchasingServiceId === item.id}
                                  <Loader2 class="w-4 h-4 animate-spin" />
                                {/if}
                                {item.is_included_in_plan ? 'Incluido' : item.active_quantity && item.active_quantity > 0 ? 'Asignar otro' : 'Asignar servicio'}
                              </button>
                            </div>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          {:else}
            <div class="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <Users class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">Primero crea o selecciona un cliente para gestionar servicios adicionales.</p>
            </div>
          {/if}
        </div>

      <!-- ═══ INVOICES ═══ -->
      {:else if activeTab === 'invoices'}
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Facturas de clientes</h2>
              <p class="text-sm text-gray-500">Facturas reales emitidas para clientes del partner, con acceso directo a pago o PDF según su estado.</p>
            </div>
            <button
              class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:border-[#C05A3C] hover:text-[#C05A3C] transition-colors"
              on:click={() => loadTabData()}
            >
              <RefreshCw class="w-4 h-4" /> Actualizar
            </button>
          </div>

          {#if invoices?.summary}
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total facturado</span>
                <p class="text-2xl font-bold text-[#1a1a1a] mt-1">{formatCurrency(invoices.summary.total_billed)}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Cobrado</span>
                <p class="text-2xl font-bold text-[#4A7C59] mt-1">{formatCurrency(invoices.summary.total_paid)}</p>
              </div>
              <div class="bg-white rounded-xl border border-gray-200 p-4">
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pendiente</span>
                <p class="text-2xl font-bold text-[#C05A3C] mt-1">{formatCurrency(invoices.summary.total_pending)}</p>
              </div>
            </div>
          {/if}

          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {#if invoices?.items && invoices.items.length > 0}
              <div class="overflow-x-auto">
                <table class="w-full">
                  <thead>
                    <tr class="border-b border-gray-200 bg-gray-50">
                      <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Factura</th>
                      <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Cliente</th>
                      <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                      <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Monto</th>
                      <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Fecha</th>
                      <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each invoices.items as invoice}
                      <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td class="px-4 py-3">
                          <div class="flex flex-col">
                            <span class="text-sm font-semibold text-[#1a1a1a]">{invoice.invoice_number}</span>
                            {#if invoice.stripe_invoice_id}
                              <span class="text-[11px] font-mono text-gray-400">{invoice.stripe_invoice_id}</span>
                            {/if}
                          </div>
                        </td>
                        <td class="px-4 py-3">
                          <div class="flex flex-col">
                            <span class="text-sm text-[#1a1a1a]">{invoice.customer_name || '—'}</span>
                            <span class="text-[11px] text-gray-500">{invoice.customer_email || '—'}</span>
                          </div>
                        </td>
                        <td class="px-4 py-3">
                          <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(invoice.status)}">
                            {invoice.status || '—'}
                          </span>
                        </td>
                        <td class="px-4 py-3 text-right text-sm font-semibold text-[#1a1a1a]">{formatCurrency(invoice.total)}</td>
                        <td class="px-4 py-3 text-xs text-gray-500">{formatDate(invoice.issued_at || invoice.due_date || invoice.paid_at)}</td>
                        <td class="px-4 py-3">
                          {#if partnerInvoicePrimaryAction(invoice)}
                            <div class="flex items-center gap-2">
                              <a
                                href={partnerInvoicePrimaryAction(invoice)?.href}
                                target="_blank"
                                rel="noreferrer"
                                class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:border-[#C05A3C] hover:text-[#C05A3C] transition-colors"
                              >
                                <Download class="w-4 h-4" /> {partnerInvoicePrimaryAction(invoice)?.label}
                              </a>
                              {#if partnerInvoiceSecondaryDownload(invoice)}
                                <a
                                  href={partnerInvoiceSecondaryDownload(invoice) || undefined}
                                  target="_blank"
                                  rel="noreferrer"
                                  class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:border-[#C05A3C] hover:text-[#C05A3C] transition-colors"
                                >
                                  <FileText class="w-4 h-4" /> PDF
                                </a>
                              {/if}
                            </div>
                          {:else}
                            <span class="text-xs text-gray-400">—</span>
                          {/if}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {:else}
              <div class="py-12 text-center">
                <FileText class="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p class="text-sm text-gray-500">No hay facturas registradas para tus clientes.</p>
              </div>
            {/if}
          </div>
        </div>

      <!-- ═══ COMMISSIONS ═══ -->
      {:else if activeTab === 'commissions'}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Mis Comisiones</h2>

        {#if commissions?.summary}
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total Ganado</span>
              <p class="text-xl font-bold text-[#1a1a1a] mt-1">{formatCurrency(commissions.summary.total_earned)}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pendiente</span>
              <p class="text-xl font-bold text-amber-600 mt-1">{formatCurrency(commissions.summary.pending)}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pagado</span>
              <p class="text-xl font-bold text-[#4A7C59] mt-1">{formatCurrency(commissions.summary.paid)}</p>
            </div>
          </div>
        {/if}

        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {#if commissions?.items && commissions.items.length > 0}
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-gray-200 bg-gray-50">
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Período</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Bruto</th>
                    <th class="text-right px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Mi Comisión</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                    <th class="text-left px-4 py-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Pagado</th>
                  </tr>
                </thead>
                <tbody>
                  {#each commissions.items as c}
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="px-4 py-3 text-sm text-gray-600">
                        {c.period_start ? formatDate(c.period_start) : '—'} — {c.period_end ? formatDate(c.period_end) : '—'}
                      </td>
                      <td class="px-4 py-3 text-right text-sm">{formatCurrency(c.gross_revenue)}</td>
                      <td class="px-4 py-3 text-right text-sm font-bold text-[#C05A3C]">{formatCurrency(c.partner_amount)}</td>
                      <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(c.status)}">
                          {c.status || '—'}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-xs text-gray-400">{c.paid_at ? formatDate(c.paid_at) : '—'}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="py-12 text-center">
              <DollarSign class="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p class="text-sm text-gray-500">No hay comisiones registradas</p>
            </div>
          {/if}
        </div>

      <!-- ═══ STRIPE ═══ -->
      {:else if activeTab === 'stripe'}
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">Stripe Connect</h2>
        <div class="bg-white rounded-xl border border-gray-200 p-6">
          {#if dashboard?.partner?.stripe_onboarding_complete}
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-full bg-[#4A7C59] flex items-center justify-center">
                <CreditCard class="w-5 h-5 text-white" />
              </div>
              <div>
                <p class="text-sm font-bold text-[#1a1a1a]">Cuenta Stripe Lista</p>
                <p class="text-xs text-gray-500">Tu onboarding KYC está completo y la cuenta está lista para operar</p>
              </div>
            </div>
            <button
              class="bg-[#635BFF] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#5851e0] transition-colors flex items-center gap-2"
              on:click={openStripeDashboard}
            >
              <ExternalLink class="w-4 h-4" /> Abrir Dashboard de Stripe
            </button>
          {:else}
            <div class="text-center py-6">
              <CreditCard class="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p class="text-sm text-gray-500 mb-4">No tienes una cuenta Stripe Connect activa</p>
              <button
                class="bg-[#635BFF] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#5851e0] transition-colors"
                on:click={async () => { try { const r = await partnerPortalApi.startStripe(); if (r.onboarding_url) window.open(r.onboarding_url, '_blank'); } catch (e) { error = e instanceof Error ? e.message : 'Error'; } }}
              >
                Conectar con Stripe
              </button>
            </div>
          {/if}
        </div>

      <!-- ═══ BRANDING (Mi Marca) ═══ -->
      {:else if activeTab === 'branding'}
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-[#1a1a1a]">Mi Marca</h2>
              <p class="text-sm text-gray-500">Personaliza la apariencia de tu marca para tus clientes</p>
            </div>
            {#if brandingData?.white_label_enabled}
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">White-Label Activo</span>
            {:else}
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-500">White-Label Inactivo</span>
            {/if}
          </div>

          {#if !brandingData?.white_label_enabled}
            <div class="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
              <Palette class="w-12 h-12 text-amber-500 mx-auto mb-3" />
              <h3 class="text-base font-bold text-[#1a1a1a] mb-2">Marca Blanca no habilitada</h3>
              <p class="text-sm text-gray-600 max-w-md mx-auto">
                Para personalizar la apariencia de tu marca en los portales de tus clientes,
                contacta a soporte para activar la función de Marca Blanca en tu cuenta.
              </p>
              <a href="mailto:help@jeturing.com" class="mt-4 inline-block text-sm text-[#C05A3C] font-semibold hover:underline">
                Contactar Soporte
              </a>
            </div>
          {:else}
            {#if brandingMessage}
              <div class="rounded border px-4 py-3 text-sm {brandingMessageType === 'success'
                ? 'border-green-200 bg-green-50 text-green-700'
                : 'border-red-200 bg-red-50 text-red-700'}">
                {brandingMessage}
              </div>
            {/if}

            <!-- Preview Card -->
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div class="h-2" style="background: linear-gradient(90deg, {brandingForm.primary_color}, {brandingForm.secondary_color})"></div>
              <div class="p-6">
                <div class="flex items-center gap-4 mb-4">
                  {#if brandingForm.logo_url}
                    <img src={brandingForm.logo_url} alt={brandingForm.brand_name} class="h-10 max-w-[160px] object-contain" />
                  {:else}
                    <div class="w-10 h-10 rounded flex items-center justify-center text-white font-bold text-lg"
                         style="background-color: {brandingForm.primary_color}">
                      {brandingForm.brand_name.charAt(0).toUpperCase() || 'M'}
                    </div>
                  {/if}
                  <div>
                    <h3 class="font-bold text-[#1a1a1a]">{brandingForm.brand_name || 'Tu Marca'}</h3>
                    <span class="text-[10px] text-gray-400">Vista previa</span>
                  </div>
                </div>
                <div class="flex gap-3 text-xs text-gray-500">
                  {#if brandingForm.support_email}
                    <span>✉ {brandingForm.support_email}</span>
                  {/if}
                  {#if brandingForm.support_url}
                    <span>🔗 {brandingForm.support_url}</span>
                  {/if}
                </div>
              </div>
            </div>

            <!-- Form -->
            <form on:submit|preventDefault={saveBrandingProfile} class="bg-white rounded-xl border border-gray-200 p-6">
              <h3 class="text-sm font-bold text-[#1a1a1a] uppercase tracking-wider mb-4">Configuración de Marca</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label for="wl-brand-name" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Nombre de Marca *</label>
                  <input id="wl-brand-name" type="text" bind:value={brandingForm.brand_name} required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="Mi Empresa" />
                </div>
                <div>
                  <label for="wl-support-email" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Email de Soporte</label>
                  <input id="wl-support-email" type="email" bind:value={brandingForm.support_email}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="soporte@miempresa.com" />
                </div>
                <div>
                  <label for="wl-logo-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL del Logo</label>
                  <input id="wl-logo-url" type="url" bind:value={brandingForm.logo_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://miempresa.com/logo.png" />
                </div>
                <div>
                  <label for="wl-favicon-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL del Favicon</label>
                  <input id="wl-favicon-url" type="url" bind:value={brandingForm.favicon_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://miempresa.com/favicon.ico" />
                </div>
                <div>
                  <label for="wl-primary-color" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Color Primario</label>
                  <div class="flex gap-2 items-center">
                    <input type="color" bind:value={brandingForm.primary_color} class="w-10 h-10 cursor-pointer border border-gray-200 rounded" />
                    <input id="wl-primary-color" type="text" bind:value={brandingForm.primary_color} class="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono" />
                  </div>
                </div>
                <div>
                  <label for="wl-secondary-color" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Color Secundario</label>
                  <div class="flex gap-2 items-center">
                    <input type="color" bind:value={brandingForm.secondary_color} class="w-10 h-10 cursor-pointer border border-gray-200 rounded" />
                    <input id="wl-secondary-color" type="text" bind:value={brandingForm.secondary_color} class="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono" />
                  </div>
                </div>
                <div>
                  <label for="wl-support-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL de Soporte</label>
                  <input id="wl-support-url" type="url" bind:value={brandingForm.support_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://soporte.miempresa.com" />
                </div>
                <div>
                  <label for="wl-portal-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL del Portal</label>
                  <input id="wl-portal-url" type="url" bind:value={brandingForm.portal_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://erp.miempresa.com" />
                </div>
                <div>
                  <label for="wl-terms-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL Términos de Servicio</label>
                  <input id="wl-terms-url" type="url" bind:value={brandingForm.terms_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://miempresa.com/terminos" />
                </div>
                <div>
                  <label for="wl-privacy-url" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">URL Política de Privacidad</label>
                  <input id="wl-privacy-url" type="url" bind:value={brandingForm.privacy_url}
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]" placeholder="https://miempresa.com/privacidad" />
                </div>
                <div class="md:col-span-2">
                  <label for="wl-custom-css" class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">CSS Personalizado</label>
                  <textarea id="wl-custom-css" bind:value={brandingForm.custom_css} rows="4"
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:border-[#C05A3C] focus:ring-1 focus:ring-[#C05A3C]"
                    placeholder={":root { --brand-primary: #C05A3C; }"}></textarea>
                  <p class="text-[10px] text-gray-400 mt-1">CSS que se inyectará en el portal Odoo de tus clientes</p>
                </div>
              </div>
              <div class="flex gap-3 mt-6 pt-4 border-t border-gray-100">
                <button type="submit" class="bg-[#1a1a1a] text-white text-sm font-semibold px-6 py-2.5 rounded-lg hover:bg-[#333] transition-colors" disabled={savingBranding}>
                  {savingBranding ? 'Guardando...' : brandingData?.is_configured ? 'Guardar Cambios' : 'Crear Perfil de Marca'}
                </button>
              </div>
            </form>

            {#if brandingData?.updated_at}
              <p class="text-[10px] text-gray-400 text-right">Última actualización: {formatDate(brandingData.updated_at)}</p>
            {/if}
          {/if}
        </div>

      <!-- ═══ PROFILE ═══ -->
      {:else if activeTab === 'profile' && profile}
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold text-[#1a1a1a]">Mi Perfil</h2>
          <button
            class="text-sm font-semibold px-4 py-2 rounded-lg transition-colors {editingProfile ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' : 'bg-[#C05A3C] text-white hover:bg-[#a94e33]'}"
            on:click={() => editingProfile ? cancelEditProfile() : startEditProfile()}
          >
            {editingProfile ? 'Cancelar' : 'Editar Perfil'}
          </button>
        </div>

        {#if !editingProfile}
          <div class="bg-white rounded-xl border border-gray-200 p-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Empresa</span>
                <p class="text-sm font-medium text-[#1a1a1a]">{profile.company_name}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Razón Social</span>
                <p class="text-sm text-gray-600">{profile.legal_name || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Email de Portal</span>
                <p class="text-sm text-gray-600">{profile.portal_email || profile.contact_email}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contacto</span>
                <p class="text-sm text-gray-600">{profile.contact_name || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Teléfono</span>
                <p class="text-sm text-gray-600">{profile.phone || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">País</span>
                <p class="text-sm text-gray-600">{profile.country || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Dirección</span>
                <p class="text-sm text-gray-600">{profile.address || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">RNC/Tax ID</span>
                <p class="text-sm text-gray-600">{profile.tax_id || '—'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Tasa de Comisión</span>
                <p class="text-sm font-bold text-[#C05A3C]">{profile.commission_rate ? (profile.commission_rate * 100).toFixed(1) : '0'}%</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Estado</span>
                <span class="px-2 py-0.5 rounded-full text-xs font-semibold {statusColor(profile.status)}">
                  {profile.status}
                </span>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Stripe Connect</span>
                <p class="text-sm">{profile.stripe_charges_enabled ? '✅ Activo' : '❌ No configurado'}</p>
              </div>
              <div>
                <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Contrato</span>
                <p class="text-sm text-gray-600">{profile.contract_reference || '—'}</p>
              </div>
            </div>
          </div>
        {:else}
          <div class="bg-white rounded-xl border border-gray-200 p-6">
            <form on:submit|preventDefault={saveProfile} class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Empresa *</label>
                  <input type="text" bind:value={profileForm.company_name} required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Razón Social</label>
                  <input type="text" bind:value={profileForm.legal_name}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">RNC/Tax ID</label>
                  <input type="text" bind:value={profileForm.tax_id}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Contacto</label>
                  <input type="text" bind:value={profileForm.contact_name}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Teléfono</label>
                  <input type="text" bind:value={profileForm.phone}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div>
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">País</label>
                  <input type="text" bind:value={profileForm.country}
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none" />
                </div>
                <div class="sm:col-span-2">
                  <label class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1">Dirección</label>
                  <textarea bind:value={profileForm.address} rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#C05A3C] focus:border-transparent outline-none resize-none"></textarea>
                </div>
              </div>
              <div class="flex gap-2 justify-end pt-4 border-t border-gray-200">
                <button type="button" class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700" on:click={cancelEditProfile}>
                  Cancelar
                </button>
                <button type="submit" disabled={savingProfile}
                  class="text-sm font-semibold px-5 py-2 bg-[#4A7C59] text-white rounded-lg hover:bg-[#3d6a4b] transition-colors flex items-center gap-1.5">
                  {#if savingProfile}<Loader2 class="w-4 h-4 animate-spin" />{/if}
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        {/if}
      {/if}
    </main>
  </div>

  <!-- Credentials Modal -->
  {#if showClientCredentials && clientCredentials}
    <div
      class="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      role="button"
      tabindex="0"
      on:click|self={() => showClientCredentials = false}
      on:keydown={(event) => {
        if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
          showClientCredentials = false;
        }
      }}
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-full bg-[#4A7C59] flex items-center justify-center">
            <Users class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="text-lg font-bold text-[#1a1a1a]">¡Tenant Creado!</h3>
            <p class="text-xs text-gray-500">Guarda estas credenciales — solo se muestran una vez</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-xl p-4 space-y-3 font-mono text-sm">
          <div>
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-0.5">URL</span>
            <a href={clientCredentials.url} target="_blank" class="text-[#C05A3C] hover:underline flex items-center gap-1">
              {clientCredentials.url} <ExternalLink class="w-3 h-3" />
            </a>
          </div>
          <div>
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-0.5">Login</span>
            <span class="text-[#1a1a1a] select-all">{clientCredentials.admin_login}</span>
          </div>
          <div>
            <span class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-0.5">Contraseña</span>
            <span class="text-[#1a1a1a] select-all">{clientCredentials.admin_password}</span>
          </div>
        </div>

        <div class="flex gap-2 mt-4 justify-end">
          <button
            class="text-sm text-gray-500 px-4 py-2 hover:text-gray-700"
            on:click={copyClientCredentials}
          >
            📋 Copiar
          </button>
          <button
            class="bg-[#1a1a1a] text-white text-sm font-semibold px-5 py-2 rounded-lg hover:bg-[#333] transition-colors"
            on:click={() => { showClientCredentials = false; clientCredentials = null; }}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  {/if}
{/if}
