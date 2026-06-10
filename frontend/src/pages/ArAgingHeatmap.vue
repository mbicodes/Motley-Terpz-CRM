<template>
  <div class="ar-root">
    <div class="ar-topbar">
      <span class="ar-title">AR Aging Heatmap</span>
      <div class="ar-topbar-right">
        <select v-model="selectedCompany" class="ar-company-select" @change="load">
          <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
        </select>
        <div class="ar-legend">
          <span class="ar-leg-label">Intensity:</span>
          <span class="ar-leg-swatch ar-leg-lo">Low</span>
          <span class="ar-leg-swatch ar-leg-mid">Mid</span>
          <span class="ar-leg-swatch ar-leg-hi">High</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="ar-loading"><div class="ar-spinner"></div></div>
    <template v-else>

      <!-- Summary stats -->
      <div class="ar-summary">
        <div class="ar-sum-tile" v-for="b in BUCKETS" :key="b.key">
          <div class="ar-sum-label">{{ b.label }}</div>
          <div class="ar-sum-val" :class="b.cls">{{ fmt(d.col_totals?.[b.key]) }}</div>
        </div>
        <div class="ar-sum-tile ar-sum-total">
          <div class="ar-sum-label">Total AR</div>
          <div class="ar-sum-val ar-redtxt">{{ fmt(d.col_totals?.total) }}</div>
        </div>
      </div>

      <!-- Search -->
      <input v-model="search" class="ar-search" placeholder="Filter customers…" />

      <!-- Heatmap grid -->
      <div class="ar-card">
        <table class="ar-table">
          <thead>
            <tr>
              <th class="ar-th-cust">Customer</th>
              <th v-for="b in BUCKETS" :key="b.key" class="ar-th-bucket">{{ b.label }}</th>
              <th class="ar-th-total">Total AR</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredGrid" :key="row.customer" class="ar-row" @click="openDash(row.customer)">
              <td class="ar-td-name">{{ row.customer_name }}</td>
              <td v-for="b in BUCKETS" :key="b.key" class="ar-td-cell"
                  :style="cellStyle(row[b.key], b.key)"
                  :title="`${row.customer_name} — ${b.label}: ${fmt(row[b.key])}`">
                <span v-if="row[b.key] > 0" class="ar-cell-val">{{ fmtK(row[b.key]) }}</span>
                <span v-else class="ar-cell-empty">—</span>
              </td>
              <td class="ar-td-total">{{ fmt(row.total) }}</td>
            </tr>
            <!-- Totals row -->
            <tr class="ar-totals-row">
              <td class="ar-td-name ar-bold">TOTAL</td>
              <td v-for="b in BUCKETS" :key="b.key" class="ar-td-cell ar-td-total-cell">
                {{ fmt(d.col_totals?.[b.key]) }}
              </td>
              <td class="ar-td-total ar-bold">{{ fmt(d.col_totals?.total) }}</td>
            </tr>
            <tr v-if="!filteredGrid.length">
              <td :colspan="BUCKETS.length + 2" class="ar-empty">No outstanding AR found</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(true)
const d = ref({})
const search = ref('')
const companies = ref([])
const selectedCompany = ref('')

const BUCKETS = [
  { key: 'current', label: 'Current',  cls: 'ar-ok'   },
  { key: '1_30',    label: '1–30 d',   cls: 'ar-warn' },
  { key: '31_60',   label: '31–60 d',  cls: 'ar-warn' },
  { key: '61_90',   label: '61–90 d',  cls: 'ar-bad'  },
  { key: '90_plus', label: '90+ d',    cls: 'ar-bad'  },
]

// Colors per bucket (low → high intensity)
const BUCKET_COLORS = {
  current: ['#f0fdf4', '#bbf7d0', '#4ade80', '#16a34a'],
  '1_30':  ['#fffbeb', '#fde68a', '#fbbf24', '#d97706'],
  '31_60': ['#fff7ed', '#fed7aa', '#fb923c', '#ea580c'],
  '61_90': ['#fef2f2', '#fecaca', '#f87171', '#dc2626'],
  '90_plus':['#fdf2f8','#f5d0fe','#d946ef','#9d174d'],
}

function cellStyle(val, bucket) {
  if (!val || val <= 0) return {}
  const max = d.value.max_per_bucket?.[bucket] || 1
  const ratio = Math.min(val / max, 1)
  const colors = BUCKET_COLORS[bucket] || BUCKET_COLORS['current']
  const idx = Math.floor(ratio * (colors.length - 1))
  return { background: colors[idx], color: idx >= 2 ? '#fff' : '#0f172a' }
}

const filteredGrid = computed(() => {
  const g = d.value.grid || []
  if (!search.value) return g
  const q = search.value.toLowerCase()
  return g.filter(r => r.customer_name.toLowerCase().includes(q) || r.customer.toLowerCase().includes(q))
})

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtK(v) {
  const n = parseFloat(v || 0)
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000)    return '$' + (n / 1000).toFixed(1) + 'k'
  return '$' + n.toFixed(0)
}

function openDash(customerId) {
  router.push({ name: 'CustomerDashboard', params: { customerId } })
}

async function loadCompanies() {
  const list = await call('crm.motley_terpz.sales_intelligence.get_companies')
  companies.value = list || []
  const mt = (list || []).find(c => c.name === 'Motley Terpz')
  selectedCompany.value = mt ? mt.name : (list?.[0]?.name || '')
}

async function load() {
  if (!selectedCompany.value) return
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.sales_intelligence.get_ar_aging_heatmap', {
      company: selectedCompany.value,
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCompanies()
  await load()
})
</script>

<style scoped>
.ar-root { display:flex; flex-direction:column; gap:14px; padding:16px; background:#f1f5f9; height:100%; overflow-y:auto; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.ar-topbar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; background:#1e293b; border-radius:12px; padding:14px 20px; }
.ar-title { font-size:16px; font-weight:800; color:#fff; }
.ar-topbar-right { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.ar-company-select { padding:5px 10px; border-radius:6px; border:1px solid #475569; background:#0f172a; color:#e2e8f0; font-size:12px; font-weight:600; cursor:pointer; outline:none; }
.ar-company-select:focus { border-color:#6366f1; }
.ar-legend { display:flex; align-items:center; gap:8px; }
.ar-leg-label { font-size:11px; color:#94a3b8; }
.ar-leg-swatch { padding:2px 10px; border-radius:4px; font-size:10px; font-weight:700; }
.ar-leg-lo  { background:#d1fae5; color:#065f46; }
.ar-leg-mid { background:#fde68a; color:#92400e; }
.ar-leg-hi  { background:#dc2626; color:#fff; }

/* Summary */
.ar-summary { display:grid; grid-template-columns:repeat(6,1fr); gap:10px; }
.ar-sum-tile { background:#fff; border-radius:10px; border:1px solid #e2e8f0; padding:12px 14px; }
.ar-sum-total { border-color:#fca5a5; }
.ar-sum-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; margin-bottom:4px; }
.ar-sum-val { font-size:18px; font-weight:800; }
.ar-ok   { color:#059669; }
.ar-warn { color:#d97706; }
.ar-bad  { color:#dc2626; }
.ar-redtxt { color:#dc2626; }

/* Search */
.ar-search { width:100%; padding:9px 14px; border:1px solid #e2e8f0; border-radius:8px; font-size:13px; outline:none; background:#fff; }
.ar-search:focus { border-color:#6366f1; }

/* Card + table */
.ar-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:auto; }
.ar-table { width:100%; border-collapse:collapse; font-size:12px; }
.ar-table th { padding:9px 12px; text-align:center; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.ar-th-cust  { text-align:left; min-width:180px; position:sticky; left:0; background:#f8fafc; z-index:2; }
.ar-th-bucket { min-width:100px; }
.ar-th-total  { text-align:right; min-width:120px; }
.ar-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:filter .1s; }
.ar-row:hover { filter:brightness(.96); }
.ar-totals-row { border-top:2px solid #e2e8f0; background:#f8fafc; }
.ar-td-name { padding:9px 12px; font-size:12px; color:#0f172a; position:sticky; left:0; background:inherit; z-index:1; white-space:nowrap; min-width:180px; }
.ar-td-cell { padding:6px 8px; text-align:center; font-size:11px; min-width:100px; }
.ar-td-total { padding:9px 12px; text-align:right; font-weight:700; font-size:12px; color:#0f172a; min-width:120px; white-space:nowrap; }
.ar-td-total-cell { font-weight:700; }
.ar-cell-val   { font-weight:700; font-size:11px; }
.ar-cell-empty { color:#cbd5e1; }
.ar-bold { font-weight:800; }
.ar-empty { text-align:center; padding:20px; color:#94a3b8; font-size:12px; }

/* Loading */
.ar-loading { display:flex; justify-content:center; padding:60px; }
.ar-spinner { width:32px; height:32px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:ar-spin .7s linear infinite; }
@keyframes ar-spin { to { transform:rotate(360deg); } }
</style>
