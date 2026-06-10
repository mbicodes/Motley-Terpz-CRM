<template>
  <div class="sp-root">
    <div class="sp-topbar">
      <span class="sp-title">Sales Projection by Product Line</span>
      <div class="sp-legend">
        <span v-for="(color, name) in LINE_COLORS" :key="name" class="sp-leg-item">
          <span class="sp-leg-dot" :style="{background: color}"></span>{{ name }}
        </span>
        <span class="sp-leg-item sp-leg-proj"><span class="sp-leg-dot sp-leg-stripe"></span>Projected (SO)</span>
      </div>
    </div>

    <div v-if="loading" class="sp-loading"><div class="sp-spinner"></div></div>
    <template v-else>

      <!-- Bar Chart -->
      <div class="sp-chart-card">
        <div class="sp-chart-title">Weekly Revenue — Actuals + Projected</div>
        <div class="sp-chart">
          <div v-for="week in d.weeks" :key="week.label" class="sp-col">
            <div class="sp-bars">
              <div
                v-for="(val, name) in week.lines" :key="name"
                class="sp-bar"
                :class="week.future ? 'sp-bar-proj' : ''"
                :style="{
                  height: barHeight(val) + 'px',
                  background: week.future ? 'transparent' : lineColor(name),
                  borderColor: lineColor(name),
                  borderWidth: week.future ? '2px' : '0',
                  borderStyle: week.future ? 'dashed' : 'none',
                }"
                :title="`${name}: ${fmt(val)}`"
              ></div>
            </div>
            <div class="sp-col-label" :class="week.future ? 'sp-col-future' : ''">{{ week.label }}</div>
            <div class="sp-col-total" :class="week.future ? 'sp-col-future' : ''">{{ fmtK(week.total) }}</div>
          </div>
        </div>
      </div>

      <!-- Data Table -->
      <div class="sp-table-card">
        <div class="sp-table-title">Weekly Breakdown</div>
        <table class="sp-table">
          <thead>
            <tr>
              <th>Week</th>
              <th v-for="name in d.product_lines" :key="name" class="sp-r">{{ name }}</th>
              <th class="sp-r">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="week in d.weeks" :key="week.label" :class="week.future ? 'sp-row-future' : 'sp-row'">
              <td>
                {{ week.label }}
                <span v-if="week.future" class="sp-proj-badge">projected</span>
              </td>
              <td v-for="name in d.product_lines" :key="name" class="sp-r">
                {{ week.lines[name] > 0 ? fmt(week.lines[name]) : '—' }}
              </td>
              <td class="sp-r sp-bold">{{ fmt(week.total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const loading = ref(true)
const d = ref({ weeks: [], product_lines: [], max_value: 1 })

const LINE_COLORS = {
  'Fresh Frozen':      '#06b6d4',
  'Solventless / IWH': '#8b5cf6',
  'Rosin':             '#f59e0b',
  'Distribution':      '#10b981',
}
const FALLBACK_COLORS = ['#6366f1','#ec4899','#14b8a6','#f97316']

function lineColor(name) {
  return LINE_COLORS[name] || FALLBACK_COLORS[Object.keys(LINE_COLORS).length % FALLBACK_COLORS.length]
}

const MAX_BAR_HEIGHT = 120

function barHeight(val) {
  const maxVal = d.value.max_value || 1
  return Math.max(2, Math.round((val / maxVal) * MAX_BAR_HEIGHT))
}

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}
function fmtK(v) {
  const n = parseFloat(v || 0)
  if (n >= 1000000) return '$' + (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000)    return '$' + (n / 1000).toFixed(0) + 'k'
  return '$' + n.toFixed(0)
}

async function load() {
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.sales_intelligence.get_sales_projection')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.sp-root { display:flex; flex-direction:column; gap:14px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.sp-topbar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; background:#1e293b; border-radius:12px; padding:14px 20px; }
.sp-title { font-size:16px; font-weight:800; color:#fff; }
.sp-legend { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.sp-leg-item { display:flex; align-items:center; gap:5px; font-size:11px; color:#94a3b8; }
.sp-leg-dot { width:10px; height:10px; border-radius:2px; display:inline-block; }
.sp-leg-stripe { background:repeating-linear-gradient(45deg,#94a3b8 0,#94a3b8 2px,transparent 2px,transparent 6px); border:1px solid #94a3b8; }
.sp-leg-proj { color:#64748b; }

/* Chart */
.sp-chart-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:20px; }
.sp-chart-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; margin-bottom:16px; }
.sp-chart { display:flex; gap:6px; align-items:flex-end; height:180px; padding-bottom:40px; position:relative; overflow-x:auto; }
.sp-col { display:flex; flex-direction:column; align-items:center; flex:1; min-width:80px; }
.sp-bars { display:flex; gap:2px; align-items:flex-end; height:120px; }
.sp-bar { min-width:8px; flex:1; border-radius:3px 3px 0 0; transition:opacity .15s; cursor:default; }
.sp-bar:hover { opacity:.75; }
.sp-col-label { font-size:10px; color:#64748b; margin-top:6px; text-align:center; white-space:nowrap; }
.sp-col-total { font-size:11px; font-weight:700; color:#0f172a; text-align:center; }
.sp-col-future { color:#94a3b8 !important; }

/* Table */
.sp-table-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; }
.sp-table-title { padding:12px 16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#0f172a; background:#f8fafc; border-bottom:1px solid #e2e8f0; }
.sp-table { width:100%; border-collapse:collapse; font-size:12px; }
.sp-table th { padding:8px 14px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.sp-r { text-align:right !important; }
.sp-row { border-bottom:1px solid #f8fafc; }
.sp-row-future { border-bottom:1px solid #f8fafc; background:#fafafa; color:#94a3b8; }
.sp-table td { padding:9px 14px; }
.sp-bold { font-weight:700; }
.sp-proj-badge { margin-left:6px; padding:1px 5px; border-radius:4px; font-size:9px; font-weight:700; background:#dbeafe; color:#1d4ed8; }
.sp-loading { display:flex; justify-content:center; padding:60px; }
.sp-spinner { width:32px; height:32px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:sp-spin .7s linear infinite; }
@keyframes sp-spin { to { transform:rotate(360deg); } }
</style>
