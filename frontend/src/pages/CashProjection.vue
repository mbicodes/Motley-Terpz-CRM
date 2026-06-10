<template>
  <div class="cp-root">
    <div class="cp-topbar">
      <span class="cp-title">Weekly Cash Projection</span>
      <div style="display:flex;gap:8px;align-items:center;">
        <span class="cp-legend cp-legend-inv">■ Invoice</span>
        <span class="cp-legend cp-legend-so">■ Sales Order</span>
      </div>
    </div>

    <div v-if="loading" class="cp-loading"><div class="cp-spinner"></div></div>
    <template v-else>

      <!-- Summary tiles -->
      <div class="cp-tiles">
        <div v-for="col in COLS" :key="col.key" class="cp-tile" :class="`cp-tile-${col.color}`">
          <div class="cp-tile-label">{{ col.label }}</div>
          <div class="cp-tile-val">{{ fmt(d.totals?.[col.key]) }}</div>
          <div class="cp-tile-count">{{ (d.rows?.[col.key] || []).length }} items</div>
        </div>
      </div>

      <!-- Week tables -->
      <div v-for="col in COLS" :key="col.key" class="cp-section">
        <div class="cp-sec-hdr" :class="`cp-hdr-${col.color}`">
          <span>{{ col.label }}
            <span class="cp-sec-count">{{ (d.rows?.[col.key] || []).length }} items</span>
          </span>
          <div class="cp-sec-right">
            <span class="cp-sec-total">{{ fmt(d.totals?.[col.key]) }}</span>
            <div class="cp-pager" v-if="(d.rows?.[col.key] || []).length > PAGE_SIZE">
              <button class="cp-pbtn" :disabled="pages[col.key] <= 1" @click="pages[col.key]--">&lsaquo;</button>
              <span class="cp-pinfo">{{ pages[col.key] }} / {{ totalPages(col.key) }}</span>
              <button class="cp-pbtn" :disabled="pages[col.key] >= totalPages(col.key)" @click="pages[col.key]++">&rsaquo;</button>
            </div>
          </div>
        </div>
        <table class="cp-table">
          <thead>
            <tr>
              <th style="width:14%">Document</th>
              <th style="width:22%">Customer</th>
              <th style="width:10%">Company</th>
              <th style="width:10%">Due Date</th>
              <th style="width:8%">Type</th>
              <th style="width:13%;text-align:right">Amount</th>
              <th style="width:13%;text-align:right">Total</th>
              <th style="width:10%">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in pagedRows(col.key)" :key="r.name"
                class="cp-row" :class="`cp-row-${col.color}`"
                @click="openDoc(r)">
              <td class="cp-mono">{{ r.name }}</td>
              <td>{{ r.customer }}</td>
              <td><span class="cp-company">{{ companyAbbr(r.company) }}</span></td>
              <td :class="col.key === 'overdue' ? 'cp-redtxt' : ''">{{ r.due_date || '—' }}</td>
              <td>
                <span class="cp-type" :class="r.type === 'invoice' ? 'cp-type-inv' : 'cp-type-so'">
                  {{ r.type === 'invoice' ? 'Invoice' : 'SO' }}
                </span>
              </td>
              <td style="text-align:right;font-weight:700">{{ fmt(r.amount) }}</td>
              <td style="text-align:right;color:#64748b">{{ fmt(r.total) }}</td>
              <td><span class="cp-status" :class="statusCls(r.status)">{{ r.status }}</span></td>
            </tr>
            <tr v-if="!(d.rows?.[col.key] || []).length">
              <td colspan="8" class="cp-empty">Nothing due {{ col.label.toLowerCase() }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { call } from 'frappe-ui'

const loading = ref(true)
const d = ref({})

const PAGE_SIZE = 6

const COLS = [
  { key: 'overdue',  label: 'Overdue',    color: 'red'   },
  { key: 'week1',    label: 'This Week',  color: 'amber' },
  { key: 'week2',    label: 'Week 2',     color: 'blue'  },
  { key: 'week3',    label: 'Week 3',     color: 'green' },
  { key: 'week4plus',label: 'Week 4+',    color: 'gray'  },
]

const pages = reactive({ overdue: 1, week1: 1, week2: 1, week3: 1, week4plus: 1 })

function totalPages(key) {
  const rows = d.value.rows?.[key] || []
  return Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
}

function pagedRows(key) {
  const rows = d.value.rows?.[key] || []
  const start = (pages[key] - 1) * PAGE_SIZE
  return rows.slice(start, start + PAGE_SIZE)
}

// Map full company names to short labels
const COMPANY_ABBR = {
  'Motley Terpz':                   'MT',
  'LA Canna Distro':                'LCD',
  'Master Touch Manufacturing':     'MTM',
  'MTPZ':                           'MTPZ',
  'TMM Group':                      'TMMG',
  'TSBC Ranch':                     'TSBC',
}
function companyAbbr(name) {
  return COMPANY_ABBR[name] || (name || '').substring(0, 4).toUpperCase()
}

async function load() {
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.sales_intelligence.get_cash_projection')
    Object.keys(pages).forEach(k => pages[k] = 1)
  } finally {
    loading.value = false
  }
}

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusCls(s) {
  if (['Paid','Completed'].includes(s)) return 'cp-s-paid'
  if (['Overdue','Unpaid'].includes(s)) return 'cp-s-bad'
  return 'cp-s-warn'
}

function openDoc(r) {
  const type = r.type === 'invoice' ? 'sales-invoice' : 'sales-order'
  window.open(`/app/${type}/${encodeURIComponent(r.name)}`, '_blank')
}

onMounted(load)
</script>

<style scoped>
.cp-root { display:flex; flex-direction:column; gap:14px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.cp-topbar { display:flex; align-items:center; justify-content:space-between; background:#1e293b; border-radius:12px; padding:14px 20px; }
.cp-title { font-size:16px; font-weight:800; color:#fff; }
.cp-legend { font-size:11px; font-weight:600; color:#94a3b8; }
.cp-legend-inv { color:#6366f1; }
.cp-legend-so  { color:#f59e0b; }

/* Summary tiles */
.cp-tiles { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; }
.cp-tile { background:#fff; border-radius:10px; border:1px solid #e2e8f0; padding:14px 16px; }
.cp-tile-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; margin-bottom:4px; }
.cp-tile-val { font-size:20px; font-weight:800; margin-bottom:2px; }
.cp-tile-count { font-size:11px; color:#94a3b8; }
.cp-tile-red   .cp-tile-label { color:#dc2626; } .cp-tile-red   .cp-tile-val { color:#dc2626; }
.cp-tile-amber .cp-tile-label { color:#d97706; } .cp-tile-amber .cp-tile-val { color:#d97706; }
.cp-tile-blue  .cp-tile-label { color:#2563eb; } .cp-tile-blue  .cp-tile-val { color:#2563eb; }
.cp-tile-green .cp-tile-label { color:#059669; } .cp-tile-green .cp-tile-val { color:#059669; }
.cp-tile-gray  .cp-tile-label { color:#64748b; } .cp-tile-gray  .cp-tile-val { color:#64748b; }

/* Section */
.cp-section { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; }
.cp-sec-hdr { display:flex; align-items:center; justify-content:space-between; padding:10px 16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; border-bottom:1px solid #e2e8f0; }
.cp-sec-count { margin-left:8px; font-size:10px; font-weight:600; opacity:.6; text-transform:none; letter-spacing:0; }
.cp-sec-right { display:flex; align-items:center; gap:12px; }
.cp-sec-total { font-size:14px; }
.cp-pager { display:flex; align-items:center; gap:4px; }
.cp-pbtn { width:24px; height:24px; border-radius:4px; border:1px solid rgba(0,0,0,.15); background:rgba(255,255,255,.3); cursor:pointer; font-size:16px; line-height:1; display:flex; align-items:center; justify-content:center; transition:background .15s; }
.cp-pbtn:hover:not(:disabled) { background:rgba(255,255,255,.5); }
.cp-pbtn:disabled { opacity:.3; cursor:default; }
.cp-pinfo { font-size:11px; min-width:36px; text-align:center; }
.cp-hdr-red   { background:#fee2e2; color:#991b1b; }
.cp-hdr-amber { background:#fef3c7; color:#92400e; }
.cp-hdr-blue  { background:#dbeafe; color:#1d4ed8; }
.cp-hdr-green { background:#d1fae5; color:#065f46; }
.cp-hdr-gray  { background:#f8fafc; color:#475569; }

/* Table */
.cp-table { width:100%; border-collapse:collapse; font-size:12px; table-layout:fixed; }
.cp-table th { padding:7px 12px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cp-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:background .1s; }
.cp-row:hover { background:#f8fafc; }
.cp-row-red:hover   { background:#fff5f5; }
.cp-row-amber:hover { background:#fffbf0; }
.cp-table td { padding:8px 12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cp-mono   { font-family:monospace; font-size:11px; color:#64748b; }
.cp-redtxt { color:#dc2626; }
.cp-empty  { text-align:center; padding:14px; color:#94a3b8; font-size:12px; }
.cp-company { padding:2px 6px; border-radius:4px; font-size:10px; font-weight:700; background:#f1f5f9; color:#475569; }
.cp-type { padding:2px 6px; border-radius:4px; font-size:10px; font-weight:700; }
.cp-type-inv { background:#ede9fe; color:#6d28d9; }
.cp-type-so  { background:#fef3c7; color:#92400e; }
.cp-status { padding:2px 6px; border-radius:4px; font-size:10px; font-weight:600; }
.cp-s-paid { background:#d1fae5; color:#065f46; }
.cp-s-bad  { background:#fee2e2; color:#991b1b; }
.cp-s-warn { background:#fef3c7; color:#92400e; }
.cp-loading { display:flex; justify-content:center; padding:60px; }
.cp-spinner { width:32px; height:32px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:cp-spin .7s linear infinite; }
@keyframes cp-spin { to { transform:rotate(360deg); } }
</style>
