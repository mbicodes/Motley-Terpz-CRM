<template>
  <div class="lb-root">
    <div class="lb-top">
      <span class="lb-title">Rep Performance Leaderboard</span>
      <div class="lb-dates">
        <input type="date" v-model="from_date" /> → <input type="date" v-model="to_date" />
        <button class="lb-btn" @click="load">Apply</button>
      </div>
    </div>

    <div v-if="loading" class="lb-loading"><div class="lb-spin"></div></div>
    <template v-else>
      <div class="lb-tiles">
        <div class="lb-tile"><span>Total revenue</span><b>{{ money(d.totals.revenue) }}</b></div>
        <div class="lb-tile"><span>Open pipeline</span><b>{{ money(d.totals.pipeline_value) }}</b></div>
        <div class="lb-tile"><span>AR owned</span><b>{{ money(d.totals.ar_owned) }}</b></div>
        <div class="lb-tile"><span>Deals won</span><b>{{ d.totals.deals_won }}</b></div>
      </div>

      <div class="lb-card">
        <table class="lb-table">
          <thead><tr>
            <th @click="sortBy('rep_name')">Rep</th>
            <th class="r" @click="sortBy('deals_won')">Won</th>
            <th class="r" @click="sortBy('deals_lost')">Lost</th>
            <th class="r" @click="sortBy('win_rate')">Win %</th>
            <th class="r" @click="sortBy('avg_deal_size')">Avg deal</th>
            <th class="r" @click="sortBy('pipeline_value')">Pipeline</th>
            <th class="r" @click="sortBy('revenue')">Revenue</th>
            <th class="r" @click="sortBy('ar_owned')">AR owned</th>
          </tr></thead>
          <tbody>
            <tr v-for="(r,i) in sorted" :key="r.rep">
              <td><span class="lb-rank">{{ i+1 }}</span> {{ r.rep_name }}</td>
              <td class="r">{{ r.deals_won }}</td>
              <td class="r">{{ r.deals_lost }}</td>
              <td class="r">{{ r.win_rate }}%</td>
              <td class="r">{{ money(r.avg_deal_size) }}</td>
              <td class="r">{{ money(r.pipeline_value) }}</td>
              <td class="r b">{{ money(r.revenue) }}</td>
              <td class="r">{{ money(r.ar_owned) }}</td>
            </tr>
            <tr v-if="!d.rows.length"><td colspan="8" class="lb-empty">No reps found.</td></tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'
const d = ref({ rows: [], totals: {} })
const loading = ref(true)
const from_date = ref(''); const to_date = ref('')
const sortKey = ref('revenue'); const sortDir = ref(-1)
function money(v){ return '$ ' + parseFloat(v||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}) }
function sortBy(k){ if(sortKey.value===k) sortDir.value*=-1; else { sortKey.value=k; sortDir.value=-1 } }
const sorted = computed(() => [...d.value.rows].sort((a,b)=>{
  const x=a[sortKey.value], y=b[sortKey.value]
  if(typeof x==='string') return x.localeCompare(y)*(-sortDir.value)
  return (x-y)*sortDir.value
}))
async function load(){
  loading.value=true
  try{ d.value = await call('crm.motley_terpz.batch_d.get_rep_leaderboard',
    { from_date: from_date.value||undefined, to_date: to_date.value||undefined })
    from_date.value=d.value.from_date; to_date.value=d.value.to_date
  } finally { loading.value=false }
}
onMounted(load)
</script>

<style scoped>
.lb-root{padding:16px;background:#f1f5f9;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;gap:14px;}
.lb-top{display:flex;justify-content:space-between;align-items:center;background:#1e293b;border-radius:12px;padding:14px 20px;flex-wrap:wrap;gap:10px;}
.lb-title{font-size:16px;font-weight:800;color:#fff;}
.lb-dates{display:flex;gap:6px;align-items:center;color:#cbd5e1;font-size:13px;}
.lb-dates input{border:none;border-radius:6px;padding:5px 8px;font-size:13px;}
.lb-btn{background:#6366f1;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-weight:700;cursor:pointer;}
.lb-tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
@media(max-width:680px){.lb-tiles{grid-template-columns:1fr 1fr;}}
.lb-tile{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;}
.lb-tile span{font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;}
.lb-tile b{font-size:19px;}
.lb-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow-x:auto;}
.lb-table{width:100%;border-collapse:collapse;font-size:13px;min-width:640px;}
.lb-table th{text-align:left;padding:10px 12px;font-size:10px;text-transform:uppercase;color:#64748b;font-weight:700;background:#f8fafc;cursor:pointer;white-space:nowrap;}
.lb-table th.r,.lb-table td.r{text-align:right;}
.lb-table td{padding:10px 12px;border-bottom:1px solid #f1f5f9;}
.lb-table td.b{font-weight:800;}
.lb-rank{display:inline-block;width:20px;color:#94a3b8;font-weight:700;}
.lb-empty{text-align:center;color:#94a3b8;padding:24px;}
.lb-loading{display:flex;justify-content:center;padding:60px;}
.lb-spin{width:30px;height:30px;border:3px solid #e2e8f0;border-top-color:#1e293b;border-radius:50%;animation:lbs .8s linear infinite;}
@keyframes lbs{to{transform:rotate(360deg);}}
</style>
