<template>
  <div class="hs-root">
    <div class="hs-topbar">
      <span class="hs-title">Customer Health Scores</span>
      <div class="hs-topbar-right">
        <select v-model="selectedCompany" class="hs-company-select" @change="load">
          <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
        </select>
        <div class="hs-filters">
          <button v-for="f in FILTERS" :key="f.key"
            class="hs-filter-btn"
            :class="{ 'hs-filter-active': activeFilter === f.key }"
            @click="activeFilter = f.key">
            {{ f.label }} <span class="hs-count">{{ countFor(f.key) }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="hs-loading"><div class="hs-spinner"></div></div>
    <template v-else>

      <!-- Tier summary -->
      <div class="hs-tier-row">
        <div class="hs-tier-card hs-tier-green">
          <div class="hs-tier-icon">✅</div>
          <div>
            <div class="hs-tier-num">{{ countFor('green') }}</div>
            <div class="hs-tier-label">Healthy (70–100)</div>
          </div>
        </div>
        <div class="hs-tier-card hs-tier-amber">
          <div class="hs-tier-icon">⚠️</div>
          <div>
            <div class="hs-tier-num">{{ countFor('amber') }}</div>
            <div class="hs-tier-label">Watch (40–69)</div>
          </div>
        </div>
        <div class="hs-tier-card hs-tier-red">
          <div class="hs-tier-icon">🔴</div>
          <div>
            <div class="hs-tier-num">{{ countFor('red') }}</div>
            <div class="hs-tier-label">At Risk (0–39)</div>
          </div>
        </div>
        <div class="hs-tier-card hs-tier-all">
          <div class="hs-tier-icon">📊</div>
          <div>
            <div class="hs-tier-num">{{ scores.length }}</div>
            <div class="hs-tier-label">Total Customers</div>
          </div>
        </div>
      </div>

      <!-- Search -->
      <input v-model="search" class="hs-search" placeholder="Search customers…" />

      <!-- Scores list -->
      <div class="hs-list">
        <div v-for="c in filtered" :key="c.customer" class="hs-item" @click="openDash(c.customer)">
          <div class="hs-item-name">{{ c.customer_name }}</div>
          <div class="hs-bar-wrap">
            <div class="hs-bar-track">
              <div class="hs-bar-fill" :class="`hs-fill-${c.tier}`" :style="{ width: c.score + '%' }"></div>
            </div>
          </div>
          <div class="hs-score-num" :class="`hs-score-${c.tier}`">{{ c.score }}</div>
          <div class="hs-badge" :class="`hs-badge-${c.tier}`">{{ TIER_LABELS[c.tier] }}</div>
        </div>
        <div v-if="!filtered.length" class="hs-empty">No customers match this filter</div>
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
const scores = ref([])
const search = ref('')
const activeFilter = ref('all')
const companies = ref([])
const selectedCompany = ref('')

const FILTERS = [
  { key: 'all',   label: 'All'       },
  { key: 'green', label: 'Healthy'   },
  { key: 'amber', label: 'Watch'     },
  { key: 'red',   label: 'At Risk'   },
]
const TIER_LABELS = { green: 'Healthy', amber: 'Watch', red: 'At Risk' }

function countFor(tier) {
  if (tier === 'all') return scores.value.length
  return scores.value.filter(c => c.tier === tier).length
}

const filtered = computed(() => {
  let list = scores.value
  if (activeFilter.value !== 'all') {
    list = list.filter(c => c.tier === activeFilter.value)
  }
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(c => c.customer_name.toLowerCase().includes(q))
  }
  return list
})

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
    scores.value = await call('crm.motley_terpz.sales_intelligence.get_customer_health_scores', {
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
.hs-root { display:flex; flex-direction:column; gap:14px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.hs-topbar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; background:#1e293b; border-radius:12px; padding:14px 20px; }
.hs-title { font-size:16px; font-weight:800; color:#fff; }
.hs-topbar-right { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.hs-company-select { padding:5px 10px; border-radius:6px; border:1px solid #475569; background:#0f172a; color:#e2e8f0; font-size:12px; font-weight:600; cursor:pointer; outline:none; }
.hs-company-select:focus { border-color:#6366f1; }
.hs-filters { display:flex; gap:6px; }
.hs-filter-btn { padding:5px 12px; border-radius:6px; border:1px solid #475569; background:transparent; color:#94a3b8; font-size:12px; font-weight:600; cursor:pointer; transition:all .15s; display:flex; align-items:center; gap:6px; }
.hs-filter-btn:hover { border-color:#6366f1; color:#fff; }
.hs-filter-active { border-color:#6366f1 !important; background:#6366f1; color:#fff !important; }
.hs-count { background:rgba(255,255,255,.15); padding:1px 6px; border-radius:10px; font-size:10px; }

/* Tier summary */
.hs-tier-row { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.hs-tier-card { display:flex; align-items:center; gap:12px; background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:16px 20px; }
.hs-tier-icon { font-size:22px; }
.hs-tier-num  { font-size:28px; font-weight:800; line-height:1; }
.hs-tier-label { font-size:11px; color:#64748b; margin-top:2px; }
.hs-tier-green { border-left:4px solid #059669; }
.hs-tier-amber { border-left:4px solid #d97706; }
.hs-tier-red   { border-left:4px solid #dc2626; }
.hs-tier-all   { border-left:4px solid #6366f1; }

/* Search */
.hs-search { width:100%; padding:9px 14px; border:1px solid #e2e8f0; border-radius:8px; font-size:13px; outline:none; background:#fff; }
.hs-search:focus { border-color:#6366f1; }

/* List */
.hs-list { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; }
.hs-item { display:flex; align-items:center; gap:14px; padding:12px 16px; border-bottom:1px solid #f8fafc; cursor:pointer; transition:background .1s; }
.hs-item:hover { background:#f8fafc; }
.hs-item-name { flex:0 0 220px; font-size:13px; font-weight:600; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.hs-bar-wrap { flex:1; }
.hs-bar-track { height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; }
.hs-bar-fill  { height:100%; border-radius:4px; transition:width .3s ease; }
.hs-fill-green { background:#059669; }
.hs-fill-amber { background:#d97706; }
.hs-fill-red   { background:#dc2626; }
.hs-score-num { flex:0 0 36px; font-size:16px; font-weight:800; text-align:right; }
.hs-score-green { color:#059669; }
.hs-score-amber { color:#d97706; }
.hs-score-red   { color:#dc2626; }
.hs-badge { flex:0 0 68px; padding:3px 8px; border-radius:6px; font-size:10px; font-weight:700; text-align:center; }
.hs-badge-green { background:#d1fae5; color:#065f46; }
.hs-badge-amber { background:#fef3c7; color:#92400e; }
.hs-badge-red   { background:#fee2e2; color:#991b1b; }
.hs-empty { text-align:center; padding:24px; color:#94a3b8; font-size:13px; }

/* Loading */
.hs-loading { display:flex; justify-content:center; padding:60px; }
.hs-spinner { width:32px; height:32px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:hs-spin .7s linear infinite; }
@keyframes hs-spin { to { transform:rotate(360deg); } }
</style>
