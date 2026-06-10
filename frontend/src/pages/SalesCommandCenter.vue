<template>
  <div class="scc-root">
    <!-- ── Top Bar ────────────────────────────────────────────────────────── -->
    <div class="scc-topbar">
      <span class="scc-title">Sales Command Center</span>
      <div class="scc-actions">
        <button class="scc-btn scc-btn-primary" @click="openErp('CRM Lead','new-crm-lead-1')">+ Add Lead</button>
        <button class="scc-btn scc-btn-secondary" @click="openErp('Sales Order','new-sales-order-1')">+ Create SO</button>
        <button class="scc-btn scc-btn-secondary" @click="openErp('CRM Call Log','new-crm-call-log-1')">Log Call</button>
      </div>
    </div>

    <div v-if="loading" class="scc-loading"><div class="scc-spinner"></div></div>
    <template v-else>

      <!-- ── KPI Row ───────────────────────────────────────────────────────── -->
      <div class="scc-kpi-row">
        <!-- Revenue this week -->
        <div class="scc-kpi">
          <div class="scc-kpi-label">Revenue This Week</div>
          <div class="scc-kpi-value" :class="d.revenue_trend === 'up' ? 'scc-green' : 'scc-red'">
            {{ fmt(d.revenue_this_week) }}
          </div>
          <div class="scc-kpi-sub">
            <span :class="d.revenue_trend === 'up' ? 'scc-badge-up' : 'scc-badge-dn'">
              {{ d.revenue_trend === 'up' ? '▲' : '▼' }} {{ Math.abs(d.revenue_change_pct) }}%
            </span>
            vs last week {{ fmt(d.revenue_last_week) }}
          </div>
        </div>

        <!-- AR Total -->
        <div class="scc-kpi">
          <div class="scc-kpi-label">Open AR</div>
          <div class="scc-kpi-value scc-red">{{ fmt(d.ar_total) }}</div>
          <div class="scc-kpi-sub scc-aging-pills">
            <span class="scc-pill scc-pill-ok"  title="Current">Cur {{ fmtK(d.ar_aging?.current) }}</span>
            <span class="scc-pill scc-pill-warn" title="1–30 days">30d {{ fmtK(d.ar_aging?.['1_30']) }}</span>
            <span class="scc-pill scc-pill-warn" title="31–60 days">60d {{ fmtK(d.ar_aging?.['31_60']) }}</span>
            <span class="scc-pill scc-pill-bad"  title="61–90 days">90d {{ fmtK(d.ar_aging?.['61_90']) }}</span>
            <span class="scc-pill scc-pill-bad"  title="90+ days">90+ {{ fmtK(d.ar_aging?.['90_plus']) }}</span>
          </div>
        </div>

        <!-- Open SOs -->
        <div class="scc-kpi">
          <div class="scc-kpi-label">Open Sales Orders</div>
          <div class="scc-kpi-value scc-blue">{{ fmt(d.open_so_value) }}</div>
          <div class="scc-kpi-sub">{{ d.open_so_count }} orders pending billing</div>
        </div>
      </div>

      <!-- ── Main Grid ─────────────────────────────────────────────────────── -->
      <div class="scc-grid">

        <!-- Top Customers -->
        <div class="scc-card">
          <div class="scc-card-hdr">Top 5 Customers — Last 30 Days</div>
          <table class="scc-table">
            <thead><tr><th>Customer</th><th class="scc-r">Revenue</th><th class="scc-r">Invoices</th></tr></thead>
            <tbody>
              <tr v-for="c in d.top_customers" :key="c.customer" class="scc-row" @click="openDash(c.customer)">
                <td>{{ c.customer_name }}</td>
                <td class="scc-r scc-bold">{{ fmt(c.revenue) }}</td>
                <td class="scc-r scc-muted">{{ c.inv_count }}</td>
              </tr>
              <tr v-if="!d.top_customers?.length">
                <td colspan="3" class="scc-empty">No invoices in last 30 days</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Recent Invoices -->
        <div class="scc-card">
          <div class="scc-card-hdr">Recent Invoices</div>
          <table class="scc-table">
            <thead><tr><th>Invoice</th><th>Customer</th><th>Date</th><th class="scc-r">Amount</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-for="inv in d.recent_invoices" :key="inv.name" class="scc-row" @click="openErpDoc('sales-invoice', inv.name)">
                <td class="scc-mono">{{ inv.name }}</td>
                <td>{{ inv.customer_name }}</td>
                <td class="scc-muted">{{ inv.posting_date }}</td>
                <td class="scc-r scc-bold">{{ fmt(inv.grand_total) }}</td>
                <td><span class="scc-status" :class="statusCls(inv.status)">{{ inv.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Recent Leads -->
        <div class="scc-card scc-card-sm">
          <div class="scc-card-hdr">Recent Leads</div>
          <div v-for="lead in d.recent_leads" :key="lead.name" class="scc-lead-row" @click="openLead(lead.name)">
            <div class="scc-lead-name">{{ lead.lead_name }}</div>
            <div class="scc-lead-meta">
              <span class="scc-status scc-status-lead">{{ lead.status }}</span>
              <span class="scc-muted">{{ timeAgo(lead.creation) }}</span>
            </div>
          </div>
          <div v-if="!d.recent_leads?.length" class="scc-empty">No recent leads</div>
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
const loading = ref(true)
const d = ref({})

async function load() {
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.sales_intelligence.get_command_center')
  } finally {
    loading.value = false
  }
}

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtK(v) {
  const n = parseFloat(v || 0)
  return n >= 1000 ? '$' + (n / 1000).toFixed(1) + 'k' : '$' + n.toFixed(0)
}

const PAID = ['Paid', 'Completed']
const BAD  = ['Overdue', 'Unpaid', 'Cancelled']
function statusCls(s) {
  if (PAID.includes(s)) return 'scc-s-paid'
  if (BAD.includes(s))  return 'scc-s-bad'
  return 'scc-s-warn'
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

function openErp(doctype, name) {
  const slug = doctype.toLowerCase().replace(/ /g, '-')
  window.open(`/app/${slug}/${name}`, '_blank')
}
function openErpDoc(type, name) {
  window.open(`/app/${type}/${encodeURIComponent(name)}`, '_blank')
}
function openDash(customerId) {
  router.push({ name: 'CustomerDashboard', params: { customerId } })
}
function openLead(leadId) {
  router.push({ name: 'Lead', params: { leadId } })
}

onMounted(load)
</script>

<style scoped>
.scc-root { display:flex; flex-direction:column; gap:16px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.scc-topbar { display:flex; align-items:center; justify-content:space-between; background:#1e293b; border-radius:12px; padding:14px 20px; }
.scc-title { font-size:16px; font-weight:800; color:#fff; }
.scc-actions { display:flex; gap:8px; }
.scc-btn { padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; border:none; transition:background .15s; }
.scc-btn-primary   { background:#6366f1; color:#fff; }
.scc-btn-primary:hover { background:#4f46e5; }
.scc-btn-secondary { background:#334155; color:#cbd5e1; }
.scc-btn-secondary:hover { background:#475569; }

/* KPI Row */
.scc-kpi-row { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
.scc-kpi { background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:18px 20px; }
.scc-kpi-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#64748b; margin-bottom:6px; }
.scc-kpi-value { font-size:26px; font-weight:800; margin-bottom:6px; }
.scc-kpi-sub { font-size:11px; color:#64748b; display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.scc-green { color:#059669; }
.scc-red   { color:#dc2626; }
.scc-blue  { color:#2563eb; }
.scc-badge-up { background:#d1fae5; color:#065f46; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:700; }
.scc-badge-dn { background:#fee2e2; color:#991b1b; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:700; }

/* AR aging pills */
.scc-aging-pills { display:flex; gap:4px; flex-wrap:wrap; }
.scc-pill { padding:2px 6px; border-radius:4px; font-size:10px; font-weight:600; white-space:nowrap; }
.scc-pill-ok   { background:#d1fae5; color:#065f46; }
.scc-pill-warn { background:#fef3c7; color:#92400e; }
.scc-pill-bad  { background:#fee2e2; color:#991b1b; }

/* Cards grid */
.scc-grid { display:grid; grid-template-columns:1fr 1.6fr 0.8fr; gap:14px; align-items:start; }
.scc-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; }
.scc-card-hdr { padding:12px 16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#0f172a; background:#f8fafc; border-bottom:1px solid #e2e8f0; }

/* Tables */
.scc-table { width:100%; border-collapse:collapse; font-size:12px; }
.scc-table th { padding:7px 14px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.scc-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:background .1s; }
.scc-row:hover { background:#f8fafc; }
.scc-table td { padding:9px 14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.scc-r    { text-align:right !important; }
.scc-bold { font-weight:700; }
.scc-mono { font-family:monospace; font-size:11px; color:#64748b; }
.scc-muted { color:#94a3b8; }
.scc-empty { text-align:center; padding:16px; color:#94a3b8; font-size:12px; }

/* Lead list */
.scc-lead-row { padding:10px 16px; border-bottom:1px solid #f8fafc; cursor:pointer; transition:background .1s; }
.scc-lead-row:hover { background:#f8fafc; }
.scc-lead-name { font-size:13px; font-weight:600; color:#0f172a; }
.scc-lead-meta { display:flex; align-items:center; gap:8px; margin-top:4px; }

/* Status badges */
.scc-status { padding:2px 7px; border-radius:6px; font-size:10px; font-weight:700; }
.scc-s-paid { background:#d1fae5; color:#065f46; }
.scc-s-bad  { background:#fee2e2; color:#991b1b; }
.scc-s-warn { background:#fef3c7; color:#92400e; }
.scc-status-lead { background:#dbeafe; color:#1d4ed8; }

/* Loading */
.scc-loading { display:flex; justify-content:center; padding:60px; }
.scc-spinner { width:32px; height:32px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:scc-spin .7s linear infinite; }
@keyframes scc-spin { to { transform:rotate(360deg); } }
</style>
