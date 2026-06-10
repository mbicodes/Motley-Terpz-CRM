<template>
  <div class="scc-root">

    <!-- ── Top Bar ────────────────────────────────────────────────────────── -->
    <div class="scc-topbar">
      <span class="scc-title">Sales Command Center</span>
      <div class="scc-topbar-right">
        <select v-model="company" class="scc-company-sel" @change="load" :disabled="loadingCompanies">
          <option value="" disabled>Select company…</option>
          <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
        </select>
        <div class="scc-quick-actions">
          <button class="scc-btn scc-btn-primary"   @click="openNew('crm-lead')">+ Add Lead</button>
          <button class="scc-btn scc-btn-secondary" @click="openNew('sales-order', company)">+ Create SO</button>
          <button class="scc-btn scc-btn-ghost"     @click="openNew('crm-call-log')">Log Call</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="scc-loading"><div class="scc-spinner"></div></div>
    <template v-else-if="!company">
      <div class="scc-no-company">Select a company above to load data.</div>
    </template>
    <template v-else>

      <!-- ── KPI Strip ─────────────────────────────────────────────────────── -->
      <div class="scc-kpi-row">

        <div class="scc-kpi scc-kpi-rev">
          <div class="scc-kpi-icon">💰</div>
          <div class="scc-kpi-body">
            <div class="scc-kpi-label">Revenue This Week</div>
            <div class="scc-kpi-value" :class="d.revenue_trend === 'up' ? 'scc-c-green' : 'scc-c-red'">
              {{ fmt(d.revenue_this_week) }}
            </div>
            <div class="scc-kpi-sub">
              <span class="scc-chip" :class="d.revenue_trend === 'up' ? 'scc-chip-up' : 'scc-chip-dn'">
                {{ d.revenue_trend === 'up' ? '▲' : '▼' }} {{ Math.abs(d.revenue_change_pct) }}%
              </span>
              <span class="scc-muted">vs last week {{ fmt(d.revenue_last_week) }}</span>
            </div>
          </div>
        </div>

        <div class="scc-kpi scc-kpi-ar">
          <div class="scc-kpi-icon">📋</div>
          <div class="scc-kpi-body">
            <div class="scc-kpi-label">Open AR</div>
            <div class="scc-kpi-value scc-c-red">{{ fmt(d.ar_total) }}</div>
            <div class="scc-aging-row">
              <div class="scc-aging-bucket scc-aging-ok">
                <div class="scc-aging-amt">{{ fmtK(d.ar_aging?.current) }}</div>
                <div class="scc-aging-lbl">Current</div>
              </div>
              <div class="scc-aging-bucket scc-aging-warn">
                <div class="scc-aging-amt">{{ fmtK(d.ar_aging?.['1_30']) }}</div>
                <div class="scc-aging-lbl">1–30d</div>
              </div>
              <div class="scc-aging-bucket scc-aging-warn">
                <div class="scc-aging-amt">{{ fmtK(d.ar_aging?.['31_60']) }}</div>
                <div class="scc-aging-lbl">31–60d</div>
              </div>
              <div class="scc-aging-bucket scc-aging-bad">
                <div class="scc-aging-amt">{{ fmtK(d.ar_aging?.['61_90']) }}</div>
                <div class="scc-aging-lbl">61–90d</div>
              </div>
              <div class="scc-aging-bucket scc-aging-bad">
                <div class="scc-aging-amt">{{ fmtK(d.ar_aging?.['90_plus']) }}</div>
                <div class="scc-aging-lbl">90+ d</div>
              </div>
            </div>
          </div>
        </div>

        <div class="scc-kpi scc-kpi-so">
          <div class="scc-kpi-icon">📦</div>
          <div class="scc-kpi-body">
            <div class="scc-kpi-label">Open Sales Orders</div>
            <div class="scc-kpi-value scc-c-blue">{{ fmt(d.open_so_value) }}</div>
            <div class="scc-kpi-sub">
              <span class="scc-chip scc-chip-blue">{{ d.open_so_count }} orders</span>
              <span class="scc-muted">pending billing</span>
            </div>
          </div>
        </div>

      </div>

      <!-- ── Main Content Grid ─────────────────────────────────────────────── -->
      <div class="scc-content-grid">

        <!-- Left col: Top Customers + Recent Leads -->
        <div class="scc-left-col">

          <!-- Top Customers -->
          <div class="scc-card">
            <div class="scc-card-hdr">
              <span>Top 5 Customers — Last 30 Days</span>
            </div>
            <div v-if="!d.top_customers?.length" class="scc-empty">No invoice data in last 30 days</div>
            <table v-else class="scc-table">
              <colgroup>
                <col style="width:50%">
                <col style="width:30%">
                <col style="width:20%">
              </colgroup>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th style="text-align:right">Revenue</th>
                  <th style="text-align:right">Invoices</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(c, idx) in d.top_customers" :key="c.customer"
                    class="scc-row" @click="openDash(c.customer)">
                  <td>
                    <span class="scc-rank">{{ idx + 1 }}</span>
                    {{ c.customer_name }}
                  </td>
                  <td style="text-align:right;font-weight:700">{{ fmt(c.revenue) }}</td>
                  <td style="text-align:right;color:#94a3b8">{{ c.inv_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Recent Leads -->
          <div class="scc-card">
            <div class="scc-card-hdr">
              <span>Recent Leads</span>
              <button class="scc-hdr-link" @click="$router.push({name:'Leads'})">View all →</button>
            </div>
            <div v-if="!d.recent_leads?.length" class="scc-empty">No leads found</div>
            <div v-for="lead in d.recent_leads" :key="lead.name"
                 class="scc-lead-row" @click="openLead(lead.name)">
              <div class="scc-lead-avatar">{{ lead.lead_name?.[0]?.toUpperCase() || '?' }}</div>
              <div class="scc-lead-info">
                <div class="scc-lead-name">{{ lead.lead_name }}</div>
                <div class="scc-lead-meta">
                  <span v-if="lead.source" class="scc-muted">{{ lead.source }}</span>
                </div>
              </div>
              <div class="scc-lead-right">
                <span class="scc-status scc-status-lead">{{ lead.status }}</span>
                <span class="scc-muted scc-small">{{ timeAgo(lead.creation) }}</span>
              </div>
            </div>
          </div>

        </div>

        <!-- Right col: Recent Invoices -->
        <div class="scc-right-col">
          <div class="scc-card scc-card-full">
            <div class="scc-card-hdr">
              <span>Recent Invoices</span>
              <button class="scc-hdr-link" @click="openErpList('sales-invoice', company)">Open in ERP →</button>
            </div>
            <div v-if="!d.recent_invoices?.length" class="scc-empty">No invoices found</div>
            <table v-else class="scc-table" style="table-layout:fixed">
              <colgroup>
                <col style="width:20%">
                <col style="width:22%">
                <col style="width:12%">
                <col style="width:16%">
                <col style="width:14%">
                <col style="width:16%">
              </colgroup>
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th style="text-align:right">Amount</th>
                  <th>Status</th>
                  <th style="text-align:right">Outstanding</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="inv in d.recent_invoices" :key="inv.name"
                    class="scc-row" @click="openErpDoc('sales-invoice', inv.name)">
                  <td class="scc-mono">{{ inv.name }}</td>
                  <td class="scc-overflow">{{ inv.customer_name }}</td>
                  <td class="scc-muted">{{ inv.posting_date }}</td>
                  <td style="text-align:right;font-weight:700">{{ fmt(inv.grand_total) }}</td>
                  <td><span class="scc-status" :class="invStatusCls(inv.status)">{{ inv.status }}</span></td>
                  <td style="text-align:right" :class="inv.outstanding_amount > 0 ? 'scc-c-red' : 'scc-c-green'">
                    {{ inv.outstanding_amount > 0 ? fmt(inv.outstanding_amount) : '✓ Paid' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const loadingCompanies = ref(true)
const companies = ref([])
const company = ref('')
const d = ref({})

async function loadCompanies() {
  loadingCompanies.value = true
  try {
    companies.value = await call('crm.motley_terpz.sales_intelligence.get_companies')
    // Auto-select Motley Terpz if present, otherwise first
    const mt = companies.value.find(c => c.name === 'Motley Terpz')
    company.value = mt ? mt.name : (companies.value[0]?.name || '')
    if (company.value) await load()
  } finally {
    loadingCompanies.value = false
  }
}

async function load() {
  if (!company.value) return
  loading.value = true
  try {
    const raw = await call('crm.motley_terpz.sales_intelligence.get_command_center',
      { company: company.value })
    // Attach outstanding_amount from the API (need to add to backend)
    d.value = raw
  } finally {
    loading.value = false
  }
}

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtK(v) {
  const n = parseFloat(v || 0)
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000)    return '$' + (n / 1000).toFixed(0) + 'k'
  return '$' + n.toFixed(0)
}

function invStatusCls(s) {
  if (['Paid'].includes(s))              return 'scc-s-paid'
  if (['Overdue','Unpaid'].includes(s))  return 'scc-s-bad'
  if (['Partly Paid'].includes(s))       return 'scc-s-warn'
  if (['Cancelled'].includes(s))         return 'scc-s-muted'
  return 'scc-s-draft'
}

function timeAgo(dt) {
  if (!dt) return ''
  const ms = Date.now() - new Date(dt).getTime()
  const mins = Math.floor(ms / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function openNew(doctype, company) {
  const url = company
    ? `/app/${doctype}/new-${doctype}-1?customer_company=${encodeURIComponent(company)}`
    : `/app/${doctype}/new-${doctype}-1`
  window.open(url, '_blank')
}
function openErpDoc(type, name) {
  window.open(`/app/${type}/${encodeURIComponent(name)}`, '_blank')
}
function openErpList(type, company) {
  window.open(`/app/${type}?company=${encodeURIComponent(company)}`, '_blank')
}
function openDash(customerId) {
  router.push({ name: 'CustomerDashboard', params: { customerId } })
}
function openLead(leadId) {
  router.push({ name: 'Lead', params: { leadId } })
}

onMounted(loadCompanies)
</script>

<style scoped>
.scc-root { display:flex; flex-direction:column; gap:16px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }

/* Top bar */
.scc-topbar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; background:#1e293b; border-radius:12px; padding:14px 20px; }
.scc-title { font-size:18px; font-weight:800; color:#fff; }
.scc-topbar-right { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.scc-company-sel { padding:6px 12px; border-radius:8px; border:1px solid #475569; background:#334155; color:#e2e8f0; font-size:13px; font-weight:600; cursor:pointer; outline:none; min-width:180px; }
.scc-company-sel:focus { border-color:#6366f1; }
.scc-quick-actions { display:flex; gap:6px; }
.scc-btn { padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; border:none; transition:all .15s; white-space:nowrap; }
.scc-btn-primary   { background:#6366f1; color:#fff; }
.scc-btn-primary:hover { background:#4f46e5; }
.scc-btn-secondary { background:#334155; color:#e2e8f0; }
.scc-btn-secondary:hover { background:#475569; }
.scc-btn-ghost     { background:transparent; border:1px solid #475569; color:#94a3b8; }
.scc-btn-ghost:hover { border-color:#6366f1; color:#fff; }

/* No company */
.scc-no-company { background:#fff; border-radius:12px; padding:48px; text-align:center; color:#94a3b8; font-size:14px; }

/* KPI Row */
.scc-kpi-row { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
.scc-kpi { display:flex; gap:14px; align-items:flex-start; background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
.scc-kpi-rev { border-top:3px solid #059669; }
.scc-kpi-ar  { border-top:3px solid #dc2626; }
.scc-kpi-so  { border-top:3px solid #2563eb; }
.scc-kpi-icon { font-size:22px; margin-top:2px; }
.scc-kpi-body { flex:1; min-width:0; }
.scc-kpi-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:#64748b; margin-bottom:4px; }
.scc-kpi-value { font-size:28px; font-weight:800; margin-bottom:8px; line-height:1.1; }
.scc-kpi-sub { display:flex; align-items:center; gap:6px; flex-wrap:wrap; font-size:11px; }
.scc-c-green { color:#059669; }
.scc-c-red   { color:#dc2626; }
.scc-c-blue  { color:#2563eb; }
.scc-chip { padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700; }
.scc-chip-up   { background:#d1fae5; color:#065f46; }
.scc-chip-dn   { background:#fee2e2; color:#991b1b; }
.scc-chip-blue { background:#dbeafe; color:#1d4ed8; }
.scc-muted { color:#94a3b8; font-size:11px; }
.scc-small { font-size:10px; }

/* AR aging buckets */
.scc-aging-row { display:flex; gap:6px; margin-top:4px; }
.scc-aging-bucket { flex:1; padding:5px 6px; border-radius:6px; text-align:center; }
.scc-aging-ok   { background:#f0fdf4; }
.scc-aging-warn { background:#fffbeb; }
.scc-aging-bad  { background:#fff5f5; }
.scc-aging-amt  { font-size:11px; font-weight:700; color:#0f172a; white-space:nowrap; }
.scc-aging-lbl  { font-size:9px; color:#94a3b8; margin-top:1px; text-transform:uppercase; letter-spacing:.3px; }

/* Content grid */
.scc-content-grid { display:grid; grid-template-columns:380px 1fr; gap:14px; align-items:start; }
.scc-left-col { display:flex; flex-direction:column; gap:14px; }
.scc-right-col { display:flex; flex-direction:column; }

/* Cards */
.scc-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.04); }
.scc-card-full { flex:1; }
.scc-card-hdr { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#0f172a; background:#f8fafc; border-bottom:1px solid #e2e8f0; }
.scc-hdr-link { background:none; border:none; color:#6366f1; font-size:11px; font-weight:600; cursor:pointer; padding:0; }
.scc-hdr-link:hover { text-decoration:underline; }
.scc-empty { padding:20px; text-align:center; color:#94a3b8; font-size:12px; }

/* Tables */
.scc-table { width:100%; border-collapse:collapse; font-size:12px; }
.scc-table th { padding:7px 14px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.scc-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:background .1s; }
.scc-row:hover { background:#f8fafc; }
.scc-table td { padding:9px 14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.scc-mono { font-family:monospace; font-size:11px; color:#64748b; }
.scc-overflow { max-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.scc-rank { display:inline-flex; align-items:center; justify-content:center; width:18px; height:18px; border-radius:50%; background:#f1f5f9; font-size:10px; font-weight:700; color:#64748b; margin-right:6px; flex-shrink:0; }

/* Lead rows */
.scc-lead-row { display:flex; align-items:center; gap:10px; padding:10px 16px; border-bottom:1px solid #f8fafc; cursor:pointer; transition:background .1s; }
.scc-lead-row:hover { background:#f8fafc; }
.scc-lead-avatar { width:32px; height:32px; border-radius:50%; background:#6366f1; color:#fff; font-size:13px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.scc-lead-info { flex:1; min-width:0; }
.scc-lead-name { font-size:13px; font-weight:600; color:#0f172a; }
.scc-lead-meta { font-size:11px; color:#94a3b8; }
.scc-lead-right { display:flex; flex-direction:column; align-items:flex-end; gap:3px; }

/* Status badges */
.scc-status { padding:2px 8px; border-radius:6px; font-size:10px; font-weight:700; white-space:nowrap; }
.scc-s-paid  { background:#d1fae5; color:#065f46; }
.scc-s-bad   { background:#fee2e2; color:#991b1b; }
.scc-s-warn  { background:#fef3c7; color:#92400e; }
.scc-s-draft { background:#f1f5f9; color:#475569; }
.scc-s-muted { background:#f8fafc; color:#94a3b8; }
.scc-status-lead { background:#dbeafe; color:#1d4ed8; }

/* Loading */
.scc-loading { display:flex; justify-content:center; padding:80px; }
.scc-spinner { width:36px; height:36px; border:3px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:scc-spin .7s linear infinite; }
@keyframes scc-spin { to { transform:rotate(360deg); } }
</style>
