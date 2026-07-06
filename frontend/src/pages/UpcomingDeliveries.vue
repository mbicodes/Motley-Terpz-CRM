<template>
  <div class="ud-root">
    <div class="ud-top">
      <span class="ud-title">Upcoming Deliveries</span>
      <span class="ud-sub" v-if="!loading">{{ d.total_count }} open · <b class="ud-red">{{ d.overdue_count }} past due</b></span>
    </div>
    <div v-if="loading" class="ud-loading"><div class="ud-spin"></div></div>
    <div v-else class="ud-card">
      <table class="ud-table">
        <thead><tr>
          <th>Sales Order</th><th>Customer</th><th>Delivery date</th>
          <th class="r">Delivered</th><th v-if="showMoney" class="r">Value</th><th>Status</th>
        </tr></thead>
        <tbody>
          <tr v-for="r in d.rows" :key="r.name" :class="{ 'ud-overdue': r.overdue }">
            <td><a :href="`/app/sales-order/${encodeURIComponent(r.name)}`" target="_blank" class="ud-mono">{{ r.name }}</a></td>
            <td>{{ r.customer }}</td>
            <td>
              {{ r.delivery_date }}
              <span v-if="r.overdue" class="ud-badge">{{ r.days_overdue }}d late</span>
            </td>
            <td class="r">{{ r.per_delivered }}%</td>
            <td v-if="showMoney" class="r">{{ money(r.grand_total) }}</td>
            <td><span class="ud-status">{{ r.status }}</span></td>
          </tr>
          <tr v-if="!d.rows.length"><td :colspan="showMoney?6:5" class="ud-empty">Nothing pending delivery. 🎉</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'
const d = ref({ rows: [], total_count: 0, overdue_count: 0 })
const loading = ref(true)
const showMoney = computed(() => d.value.rows.some(r => r.grand_total !== null))
function money(v){ return v==null ? '—' : '$ ' + parseFloat(v||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}) }
onMounted(async () => {
  try { d.value = await call('crm.motley_terpz.batch_d.get_upcoming_deliveries') }
  finally { loading.value = false }
})
</script>

<style scoped>
.ud-root{padding:16px;background:#f1f5f9;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;gap:14px;}
.ud-top{display:flex;justify-content:space-between;align-items:center;background:#0f766e;border-radius:12px;padding:14px 20px;}
.ud-title{font-size:16px;font-weight:800;color:#fff;}
.ud-sub{font-size:13px;color:#ccfbf1;} .ud-red{color:#fecaca;}
.ud-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow-x:auto;}
.ud-table{width:100%;border-collapse:collapse;font-size:13px;min-width:620px;}
.ud-table th{text-align:left;padding:10px 12px;font-size:10px;text-transform:uppercase;color:#64748b;font-weight:700;background:#f8fafc;}
.ud-table th.r,.ud-table td.r{text-align:right;}
.ud-table td{padding:10px 12px;border-bottom:1px solid #f1f5f9;}
.ud-overdue{background:#fef2f2;}
.ud-mono{font-family:ui-monospace,Menlo,monospace;color:#0f766e;text-decoration:none;}
.ud-badge{background:#fee2e2;color:#991b1b;font-size:10px;font-weight:700;padding:2px 7px;border-radius:8px;margin-left:6px;}
.ud-status{font-size:11px;color:#475569;}
.ud-empty{text-align:center;color:#94a3b8;padding:24px;}
.ud-loading{display:flex;justify-content:center;padding:60px;}
.ud-spin{width:30px;height:30px;border:3px solid #e2e8f0;border-top-color:#0f766e;border-radius:50%;animation:uds .8s linear infinite;}
@keyframes uds{to{transform:rotate(360deg);}}
</style>
