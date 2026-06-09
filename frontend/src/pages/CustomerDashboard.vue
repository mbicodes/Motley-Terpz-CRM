<template>
  <div class="cd-root" ref="root">
    <!-- ── Top Bar ─────────────────────────────────────────────────────────── -->
    <div class="cd-topbar">
      <button class="cd-back" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>
      <div class="cd-topbar-title">
        <span class="cd-customer-name">{{ d.customer?.customer_name || customerId }}</span>
        <span class="cd-badge" :class="arStatusClass(d.crm?.custom_ar_status)">{{ displayArStatus(d.crm?.custom_ar_status) }}</span>
        <span v-if="d.crm?.custom_relationship_tier" class="cd-badge cd-badge-tier">{{ d.crm.custom_relationship_tier }}</span>
        <span v-if="d.customer?.is_frozen && !['Blocked','Frozen'].includes(d.crm?.custom_ar_status)" class="cd-badge cd-badge-frozen">⛔ Frozen</span>
      </div>
      <div class="cd-topbar-meta">
        <span v-if="d.crm?.custom_pipeline">{{ d.crm.custom_pipeline }}</span>
        <span v-if="d.customer?.payment_terms" class="cd-dot">·</span>
        <span v-if="d.customer?.payment_terms">{{ d.customer.payment_terms }}</span>
        <span v-if="d.crm?.custom_account_owner" class="cd-dot">·</span>
        <span v-if="d.crm?.custom_account_owner">{{ ownerName(d.crm.custom_account_owner) }}</span>
      </div>
      <button class="cd-erp-btn" @click="openERP">Open in ERPNext ↗</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="cd-loading">
      <div class="cd-spinner"></div>
    </div>

    <template v-else>
      <!-- ── KPI Row ───────────────────────────────────────────────────────── -->
      <div class="cd-kpi-row">
        <div class="cd-kpi cd-kpi-lifetime">
          <div class="cd-kpi-label">Lifetime Revenue</div>
          <div class="cd-kpi-val">{{ fmt(d.kpis?.lifetime_revenue) }}</div>
          <div class="cd-kpi-sub">{{ d.kpis?.invoice_count }} invoices total</div>
        </div>
        <div class="cd-kpi cd-kpi-ar">
          <div class="cd-kpi-label">Outstanding AR</div>
          <div class="cd-kpi-val" :class="d.kpis?.outstanding_ar > 0 ? 'cd-red' : ''">{{ fmt(d.kpis?.outstanding_ar) }}</div>
          <div class="cd-kpi-sub">Aging {{ d.crm?.custom_ar_aging_days || 0 }} days</div>
        </div>
        <div class="cd-kpi cd-kpi-ytd">
          <div class="cd-kpi-label">YTD {{ d.current_year }}</div>
          <div class="cd-kpi-val">{{ fmt(d.kpis?.ytd_revenue) }}</div>
          <div class="cd-kpi-sub">vs {{ fmt(d.kpis?.last_year_revenue) }} last year</div>
        </div>
        <div class="cd-kpi cd-kpi-avg">
          <div class="cd-kpi-label">Avg Order Value</div>
          <div class="cd-kpi-val">{{ fmt(d.kpis?.avg_order_value) }}</div>
          <div class="cd-kpi-sub">per invoice</div>
        </div>
        <div class="cd-kpi cd-kpi-pay">
          <div class="cd-kpi-label">Payment Rate</div>
          <div class="cd-kpi-val" :class="d.kpis?.payment_rate_pct >= 80 ? 'cd-green' : 'cd-amber'">{{ d.kpis?.payment_rate_pct?.toFixed(1) }}%</div>
          <div class="cd-kpi-sub">{{ fmt(d.kpis?.total_paid) }} collected</div>
        </div>
        <div class="cd-kpi cd-kpi-last">
          <div class="cd-kpi-label">Last Order</div>
          <div class="cd-kpi-val cd-kpi-date">{{ d.kpis?.last_invoice_date?.slice(0,10) || '—' }}</div>
          <div class="cd-kpi-sub" :class="d.kpis?.days_since_last_order > 60 ? 'cd-amber' : ''">
            {{ d.kpis?.days_since_last_order != null ? d.kpis.days_since_last_order + ' days ago' : 'No orders' }}
          </div>
        </div>
      </div>

      <!-- ── Charts Row ────────────────────────────────────────────────────── -->
      <div class="cd-charts-row">

        <!-- Revenue Trend -->
        <div class="cd-card cd-card-wide">
          <div class="cd-card-hdr">
            <span class="cd-card-title">Revenue Trend</span>
            <div class="cd-legend">
              <span class="cd-legend-dot cd-legend-cy"></span> {{ d.current_year }}
              <span class="cd-legend-dot cd-legend-py"></span> {{ (d.current_year||2026) - 1 }}
            </div>
          </div>
          <svg class="cd-linechart" viewBox="0 0 560 160" preserveAspectRatio="none">
            <!-- Grid lines -->
            <g stroke="#e2e8f0" stroke-width="0.5">
              <line x1="40" y1="10" x2="550" y2="10"/>
              <line x1="40" y1="50" x2="550" y2="50"/>
              <line x1="40" y1="90" x2="550" y2="90"/>
              <line x1="40" y1="130" x2="550" y2="130"/>
            </g>
            <!-- Y axis labels -->
            <g fill="#94a3b8" font-size="8" text-anchor="end">
              <text x="36" y="13">{{ fmtK(chartMax) }}</text>
              <text x="36" y="53">{{ fmtK(chartMax*0.67) }}</text>
              <text x="36" y="93">{{ fmtK(chartMax*0.33) }}</text>
              <text x="36" y="133">0</text>
            </g>
            <!-- Previous year line (gray) -->
            <polyline :points="linePoints(d.previous_year_trend)" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4 2"/>
            <!-- Current year line (blue) -->
            <polyline :points="linePoints(d.current_year_trend)" fill="none" stroke="#6366f1" stroke-width="2.5"/>
            <!-- Area fill -->
            <polygon :points="areaPoints(d.current_year_trend)" fill="url(#cdGrad)" opacity="0.2"/>
            <defs>
              <linearGradient id="cdGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <!-- Data points -->
            <g v-for="(p,i) in chartPoints(d.current_year_trend)" :key="i">
              <circle :cx="p.x" :cy="p.y" r="3" fill="#6366f1" stroke="white" stroke-width="1.5"/>
            </g>
            <!-- X labels -->
            <g fill="#94a3b8" font-size="8" text-anchor="middle">
              <text v-for="(m,i) in (d.current_year_trend||[])" :key="i"
                    :x="40 + (i * 510/11)" y="148">{{ m.month }}</text>
            </g>
          </svg>
        </div>

        <!-- AR Aging -->
        <div class="cd-card cd-card-narrow">
          <div class="cd-card-hdr"><span class="cd-card-title">AR Aging</span></div>
          <div class="cd-aging-total">{{ fmt(d.kpis?.outstanding_ar) }}</div>
          <div class="cd-aging-buckets">
            <div class="cd-ab" v-for="b in agingBuckets" :key="b.label">
              <div class="cd-ab-label">{{ b.label }}</div>
              <div class="cd-ab-bar-bg">
                <div class="cd-ab-bar" :style="{width: b.pct+'%', background: b.color}"></div>
              </div>
              <div class="cd-ab-val" :style="{color: b.color}">{{ fmt(b.val) }}</div>
            </div>
          </div>
          <div class="cd-aging-note">
            <span :class="['Blocked','Frozen'].includes(d.crm?.custom_ar_status) ? 'cd-red' : d.crm?.custom_ar_status === 'Overdue' ? 'cd-amber' : 'cd-green'">
              {{ d.crm?.custom_ar_aging_days || 0 }} days since oldest unpaid invoice
            </span>
          </div>
        </div>
      </div>

      <!-- ── Second Row ────────────────────────────────────────────────────── -->
      <div class="cd-charts-row">

        <!-- Category Breakdown -->
        <div class="cd-card cd-card-med">
          <div class="cd-card-hdr"><span class="cd-card-title">Revenue by Category</span></div>
          <div class="cd-cat-list">
            <div v-for="(cat, i) in (d.category_breakdown||[]).slice(0,8)" :key="i" class="cd-cat-row">
              <div class="cd-cat-name">{{ cat.item_group }}</div>
              <div class="cd-cat-bar-bg">
                <div class="cd-cat-bar" :style="{width: catPct(cat)+'%', background: catColor(i)}"></div>
              </div>
              <div class="cd-cat-val">{{ fmt(cat.revenue) }}</div>
            </div>
            <div v-if="!d.category_breakdown?.length" class="cd-empty">No data</div>
          </div>
        </div>

        <!-- Top Items -->
        <div class="cd-card cd-card-med">
          <div class="cd-card-hdr"><span class="cd-card-title">Top Products</span></div>
          <div class="cd-top-items">
            <div v-for="(item,i) in (d.top_items||[]).slice(0,6)" :key="i" class="cd-top-item">
              <div class="cd-top-rank">{{ i+1 }}</div>
              <div class="cd-top-info">
                <div class="cd-top-name">{{ item.item_name }}</div>
                <div class="cd-top-meta">{{ item.item_group }} · {{ item.times_ordered }}× ordered</div>
              </div>
              <div class="cd-top-rev">{{ fmt(item.revenue) }}</div>
            </div>
            <div v-if="!d.top_items?.length" class="cd-empty">No data</div>
          </div>
        </div>

        <!-- CRM Profile -->
        <div class="cd-card cd-card-narrow">
          <div class="cd-card-hdr"><span class="cd-card-title">CRM Profile</span></div>
          <div class="cd-profile-rows">
            <div class="cd-pr"><span class="cd-pr-l">Tier</span><span class="cd-pr-v cd-tier">{{ d.crm?.custom_relationship_tier || '—' }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Pipeline</span><span class="cd-pr-v">{{ d.crm?.custom_pipeline || '—' }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Activity</span><span class="cd-pr-v">{{ d.crm?.custom_buyer_activity || '—' }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Owner</span><span class="cd-pr-v">{{ ownerName(d.crm?.custom_account_owner) }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Group</span><span class="cd-pr-v">{{ d.customer?.customer_group || '—' }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">COD</span><span class="cd-pr-v" :class="d.crm?.custom_cod_flag ? 'cd-amber' : ''">{{ d.crm?.custom_cod_flag ? 'Yes' : 'No' }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Single Source</span><span class="cd-pr-v">{{ d.crm?.custom_single_source ? 'Yes' : 'No' }}</span></div>
            <div class="cd-pr" v-if="d.crm?.custom_next_followup_date"><span class="cd-pr-l">Next Follow-up</span><span class="cd-pr-v cd-amber">{{ d.crm.custom_next_followup_date }}</span></div>
            <div class="cd-pr"><span class="cd-pr-l">Last Synced</span><span class="cd-pr-v cd-muted">{{ (d.crm?.custom_last_sync||'').slice(0,10) || '—' }}</span></div>
          </div>
        </div>
      </div>

      <!-- ── Recent Invoices ───────────────────────────────────────────────── -->
      <div class="cd-card cd-card-full">
        <div class="cd-card-hdr">
          <span class="cd-card-title">Recent Invoices</span>
          <span class="cd-card-sub">{{ d.recent_invoices?.length }} most recent</span>
        </div>
        <div class="cd-invoice-table-wrap">
          <table class="cd-invoice-table">
            <thead>
              <tr>
                <th class="cd-th-inv">Invoice</th>
                <th class="cd-th-date">Date</th>
                <th class="cd-th-num">Amount</th>
                <th class="cd-th-num">Outstanding</th>
                <th class="cd-th-date">Due Date</th>
                <th class="cd-th-date">Terms</th>
                <th class="cd-th-status">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in (d.recent_invoices||[])" :key="inv.name"
                  @click="openInvoice(inv.name)" class="cd-inv-row">
                <td class="cd-inv-id">{{ inv.name }}</td>
                <td>{{ inv.posting_date }}</td>
                <td class="cd-num">{{ fmt(inv.grand_total) }}</td>
                <td class="cd-num" :class="inv.outstanding_amount > 0 ? 'cd-red' : 'cd-green'">
                  {{ inv.outstanding_amount > 0 ? fmt(inv.outstanding_amount) : '✓ Paid' }}
                </td>
                <td :class="isDuePast(inv.due_date) ? 'cd-red' : ''">{{ inv.due_date || '—' }}</td>
                <td class="cd-muted">{{ inv.payment_terms_template || '—' }}</td>
                <td><span class="cd-inv-status" :class="invStatusCls(inv)">{{ inv.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── See Records button ────────────────────────────────────────────── -->
      <div style="display:flex;justify-content:center;padding:8px 0 16px;">
        <button class="cd-records-btn" @click="$router.push({name:'CustomerRecords',params:{customerId}})">
          📋 See Records — Orders · Invoices · Delivery Notes
        </button>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'

const route  = useRoute()
const customerId = computed(() => route.params.customerId)
const loading = ref(true)
const d = ref({})

async function load() {
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.customer_dashboard.get_customer_dashboard', {
      customer: customerId.value
    })
  } catch(e) { console.error(e) }
  finally { loading.value = false }
}
onMounted(load)


// ── Formatters ────────────────────────────────────────────────────────────────
function fmt(v) {
  if (!v) return '$ 0'
  return '$ ' + parseFloat(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtK(v) {
  if (!v) return '0'
  if (v >= 1000000) return (v/1000000).toFixed(1) + 'M'
  if (v >= 1000) return (v/1000).toFixed(0) + 'k'
  return Math.round(v)
}
function ownerName(email) {
  if (!email) return '—'
  return email.split('@')[0].split('.').map(p => p.charAt(0).toUpperCase()+p.slice(1)).join(' ')
}
function openERP() { window.open(`/app/customer/${encodeURIComponent(customerId.value)}`, '_blank') }
function openInvoice(name) { window.open(`/app/sales-invoice/${encodeURIComponent(name)}`, '_blank') }
function isDuePast(dt) { return dt && new Date(dt) < new Date() }

function displayArStatus(s) {
  if (s === 'Blocked') return 'Frozen'
  return s || '—'
}
function arStatusClass(s) {
  return { 'cd-badge-frozen': s==='Blocked' || s==='Frozen',
           'cd-badge-overdue': s==='Overdue',
           'cd-badge-watch': s==='Watch',
           'cd-badge-clean': s==='Clean' }
}
function invStatusCls(inv) {
  if (inv.outstanding_amount <= 0) return 'cd-inv-paid'
  if (isDuePast(inv.due_date)) return 'cd-inv-overdue'
  return 'cd-inv-unpaid'
}

const CAT_COLORS = ['#6366f1','#0ea5e9','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16']
function catColor(i) { return CAT_COLORS[i % CAT_COLORS.length] }
function catPct(cat) {
  const max = Math.max(...(d.value.category_breakdown||[]).map(c => c.revenue), 1)
  return Math.round((cat.revenue / max) * 100)
}

// ── AR Aging buckets ──────────────────────────────────────────────────────────
const agingBuckets = computed(() => {
  const ag = d.value.ar_aging || {}
  const total = Object.values(ag).reduce((s,v)=>s+v,0) || 1
  return [
    { label: 'Current (0–30d)',  val: ag.current||0, color: '#10b981', pct: Math.round((ag.current||0)/total*100) },
    { label: '31–60 days',       val: ag['30']||0,   color: '#f59e0b', pct: Math.round(((ag['30']||0)/total)*100) },
    { label: '61–90 days',       val: ag['60']||0,   color: '#f97316', pct: Math.round(((ag['60']||0)/total)*100) },
    { label: '90+ days',         val: ag['90']||0,   color: '#ef4444', pct: Math.round(((ag['90']||0)/total)*100) },
  ]
})

// ── SVG Chart helpers ─────────────────────────────────────────────────────────
const chartMax = computed(() => {
  const all = [...(d.value.current_year_trend||[]), ...(d.value.previous_year_trend||[])]
  return Math.max(...all.map(p => p.revenue), 1)
})

function xPos(i) { return 40 + i * (510 / 11) }
function yPos(val) { return 130 - ((val / chartMax.value) * 120) }

function chartPoints(trend) {
  return (trend||[]).map((p,i) => ({ x: xPos(i), y: yPos(p.revenue) }))
}
function linePoints(trend) {
  return (trend||[]).map((p,i) => `${xPos(i)},${yPos(p.revenue)}`).join(' ')
}
function areaPoints(trend) {
  if (!trend?.length) return ''
  const pts = trend.map((p,i) => `${xPos(i)},${yPos(p.revenue)}`).join(' ')
  return `${xPos(0)},130 ${pts} ${xPos(trend.length-1)},130`
}
</script>

<style scoped>
.cd-root { display:flex; flex-direction:column; gap:12px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }

/* Topbar */
.cd-topbar { display:flex; align-items:center; gap:12px; background:#1e293b; border-radius:12px; padding:12px 20px; flex-wrap:wrap; }
.cd-back { display:flex; align-items:center; gap:6px; color:#94a3b8; background:transparent; border:none; cursor:pointer; font-size:13px; white-space:nowrap; }
.cd-back svg { width:16px; height:16px; }
.cd-topbar-title { display:flex; align-items:center; gap:8px; flex:1; min-width:0; }
.cd-customer-name { font-size:18px; font-weight:800; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cd-topbar-meta { display:flex; align-items:center; gap:4px; color:#64748b; font-size:12px; }
.cd-dot { margin:0 2px; }
.cd-erp-btn { background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.15); color:#e2e8f0; border-radius:8px; padding:6px 14px; cursor:pointer; font-size:12px; font-weight:600; white-space:nowrap; }
.cd-erp-btn:hover { background:rgba(255,255,255,.2); }

/* Badges */
.cd-badge { padding:2px 10px; border-radius:20px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; }
.cd-badge-frozen  { background:#fecaca; color:#b91c1c; }
.cd-badge-overdue { background:#fef3c7; color:#92400e; }
.cd-badge-watch   { background:#dbeafe; color:#1d4ed8; }
.cd-badge-clean   { background:#d1fae5; color:#065f46; }
.cd-badge-tier    { background:#ede9fe; color:#6d28d9; }

/* Loading */
.cd-loading { display:flex; justify-content:center; padding:80px; }
.cd-spinner { width:40px; height:40px; border:3px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:cd-spin .8s linear infinite; }
@keyframes cd-spin { to { transform:rotate(360deg); } }

/* KPI Row */
.cd-kpi-row { display:grid; grid-template-columns:repeat(6,1fr); gap:10px; }
.cd-kpi { background:#fff; border-radius:12px; padding:14px 16px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,.05); }
.cd-kpi-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:#64748b; margin-bottom:6px; }
.cd-kpi-val { font-size:18px; font-weight:800; color:#0f172a; line-height:1; margin-bottom:4px; }
.cd-kpi-date { font-size:14px; }
.cd-kpi-sub { font-size:11px; color:#94a3b8; }
.cd-kpi-ar .cd-kpi-val { color:#64748b; }
.cd-red  { color:#dc2626 !important; }
.cd-green{ color:#059669 !important; }
.cd-amber{ color:#d97706 !important; }
.cd-muted{ color:#94a3b8 !important; }

/* Charts row */
.cd-charts-row { display:flex; gap:12px; }
.cd-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,.05); padding:16px; overflow:hidden; }
.cd-card-wide   { flex:3; min-width:0; }
.cd-card-med    { flex:2; min-width:0; }
.cd-card-narrow { flex:1.2; min-width:0; }
.cd-card-full   { width:100%; }
.cd-card-hdr    { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.cd-card-title  { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#0f172a; }
.cd-card-sub    { font-size:11px; color:#94a3b8; }

/* Line chart */
.cd-linechart { width:100%; height:160px; display:block; }
.cd-legend { display:flex; align-items:center; gap:10px; font-size:11px; color:#64748b; }
.cd-legend-dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
.cd-legend-cy { background:#6366f1; }
.cd-legend-py { background:#cbd5e1; }

/* AR Aging */
.cd-aging-total { font-size:22px; font-weight:800; color:#dc2626; margin-bottom:12px; }
.cd-aging-buckets { display:flex; flex-direction:column; gap:8px; }
.cd-ab { display:flex; align-items:center; gap:8px; }
.cd-ab-label { font-size:11px; color:#64748b; width:100px; flex-shrink:0; }
.cd-ab-bar-bg { flex:1; height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; }
.cd-ab-bar { height:100%; border-radius:4px; transition:width .4s; }
.cd-ab-val { font-size:11px; font-weight:600; width:80px; text-align:right; flex-shrink:0; }
.cd-aging-note { margin-top:12px; font-size:11px; }

/* Category breakdown */
.cd-cat-list { display:flex; flex-direction:column; gap:7px; }
.cd-cat-row { display:flex; align-items:center; gap:8px; }
.cd-cat-name { font-size:11px; color:#475569; width:110px; flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cd-cat-bar-bg { flex:1; height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; }
.cd-cat-bar { height:100%; border-radius:4px; transition:width .4s; }
.cd-cat-val { font-size:11px; font-weight:600; color:#475569; width:80px; text-align:right; flex-shrink:0; }

/* Top items */
.cd-top-items { display:flex; flex-direction:column; gap:8px; }
.cd-top-item { display:flex; align-items:center; gap:10px; }
.cd-top-rank { width:20px; height:20px; border-radius:50%; background:#f1f5f9; color:#64748b; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.cd-top-info { flex:1; min-width:0; }
.cd-top-name { font-size:12px; font-weight:600; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cd-top-meta { font-size:10px; color:#94a3b8; }
.cd-top-rev  { font-size:12px; font-weight:700; color:#0f172a; flex-shrink:0; }

/* CRM Profile */
.cd-profile-rows { display:flex; flex-direction:column; gap:6px; }
.cd-pr { display:flex; justify-content:space-between; align-items:center; padding:4px 0; border-bottom:1px solid #f8fafc; font-size:12px; }
.cd-pr-l { color:#94a3b8; }
.cd-pr-v { font-weight:600; color:#0f172a; text-align:right; }
.cd-tier { background:#ede9fe; color:#6d28d9; padding:1px 8px; border-radius:8px; font-size:10px; }

/* Invoice table */
.cd-invoice-table-wrap { overflow-x:auto; }
.cd-invoice-table { width:100%; border-collapse:collapse; font-size:12px; table-layout:fixed; }
.cd-invoice-table th { padding:8px 12px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.cd-inv-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:background .15s; }
.cd-inv-row:hover { background:#f8fafc; }
.cd-invoice-table td { padding:8px 12px; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cd-inv-id { font-family:monospace; font-size:11px; color:#64748b; }
.cd-num    { text-align:right; font-weight:600; }
.cd-th-inv    { width:22%; }
.cd-th-date   { width:12%; }
.cd-th-num    { width:14%; text-align:right !important; }
.cd-th-status { width:10%; }
.cd-inv-status { padding:2px 8px; border-radius:8px; font-size:10px; font-weight:700; }
.cd-inv-paid    { background:#d1fae5; color:#065f46; }
.cd-inv-overdue { background:#fee2e2; color:#991b1b; }
.cd-inv-unpaid  { background:#fef3c7; color:#92400e; }
.cd-empty { color:#94a3b8; font-size:12px; padding:12px 0; }

/* See Records button */
.cd-records-btn { background:#1e293b; color:#fff; border:none; border-radius:10px; padding:12px 28px; font-size:13px; font-weight:700; cursor:pointer; letter-spacing:.3px; transition:background .2s; }
.cd-records-btn:hover { background:#334155; }

/* Responsive */
@media (max-width: 900px) {
  .cd-kpi-row { grid-template-columns: repeat(3,1fr); }
  .cd-charts-row { flex-wrap:wrap; }
  .cd-card-wide, .cd-card-med, .cd-card-narrow { flex:1 1 100%; }
}
</style>
