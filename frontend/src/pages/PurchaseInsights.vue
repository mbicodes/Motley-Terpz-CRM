<template>
  <div class="pi-root">
    <div class="pi-top">
      <span class="pi-title">Customer Purchase Insights</span>
      <span class="pi-sub" v-if="!loading">{{ d.count }} accounts to watch</span>
    </div>
    <div v-if="loading" class="pi-loading"><div class="pi-spin"></div></div>
    <template v-else>
      <div class="pi-section-h">Slowing down <span>{{ d.count }}</span></div>
      <div v-if="!d.rows.length" class="pi-empty">No slipping accounts right now. 👍</div>
      <div v-else class="pi-list">
        <div v-for="r in d.rows" :key="r.customer" class="pi-card">
          <div class="pi-card-head">
            <a :href="`/app/customer/${encodeURIComponent(r.customer)}`" target="_blank" class="pi-name">{{ r.customer_name }}</a>
            <span v-if="r.days_since_last_order != null" class="pi-since">last order {{ r.days_since_last_order }}d ago</span>
          </div>
          <div class="pi-reasons">
            <span v-for="(reason,i) in r.reasons" :key="i" class="pi-reason">{{ reason }}</span>
          </div>
          <div class="pi-nums">
            <span>Prior 90d: <b>{{ money(r.rev_prior) }}</b> ({{ r.orders_prior }} orders)</span>
            <span>→ Recent 90d: <b>{{ money(r.rev_recent) }}</b> ({{ r.orders_recent }} orders)</span>
          </div>
        </div>
      </div>

      <div class="pi-section-h">Due to reorder <span>{{ reorder.count }}</span></div>
      <div v-if="!reorder.rows.length" class="pi-empty">No accounts due to reorder.</div>
      <div v-else class="pi-list">
        <div v-for="r in reorder.rows" :key="r.customer" class="pi-card">
          <div class="pi-card-head">
            <a :href="`/app/customer/${encodeURIComponent(r.customer)}`" target="_blank" class="pi-name">{{ r.customer_name }}</a>
            <span class="pi-since">every ~{{ r.avg_gap_days }}d</span>
          </div>
          <div class="pi-reasons">
            <span class="pi-reason pi-reorder">Due to reorder — {{ r.overdue_by }}d past their usual cadence</span>
          </div>
          <div class="pi-nums">
            <span>Last order <b>{{ r.days_since_last_order }}d</b> ago · {{ r.orders }} orders on record</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
const d = ref({ rows: [], count: 0 })
const reorder = ref({ rows: [], count: 0 })
const loading = ref(true)
function money(v){ return '$ ' + parseFloat(v||0).toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:0}) }
onMounted(async () => {
  try {
    d.value = await call('crm.motley_terpz.batch_d.get_purchase_insights')
    reorder.value = await call('crm.motley_terpz.batch_d.get_reorder_due')
  } finally { loading.value = false }
})
</script>

<style scoped>
.pi-root{padding:16px;background:#f1f5f9;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;gap:14px;}
.pi-top{display:flex;justify-content:space-between;align-items:center;background:#7c2d12;border-radius:12px;padding:14px 20px;}
.pi-title{font-size:16px;font-weight:800;color:#fff;}
.pi-sub{font-size:13px;color:#fed7aa;}
.pi-list{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
@media(max-width:680px){.pi-list{grid-template-columns:1fr;}}
.pi-card{background:#fff;border:1px solid #e2e8f0;border-radius:11px;padding:14px 16px;display:flex;flex-direction:column;gap:8px;}
.pi-card-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;}
.pi-name{font-weight:750;color:#1e293b;text-decoration:none;}
.pi-name:hover{text-decoration:underline;}
.pi-since{font-size:11px;color:#94a3b8;white-space:nowrap;}
.pi-reasons{display:flex;flex-wrap:wrap;gap:6px;}
.pi-reason{background:#fef3c7;color:#92400e;font-size:11px;font-weight:600;padding:3px 9px;border-radius:8px;}
.pi-reorder{background:#dbeafe;color:#1d4ed8;}
.pi-section-h{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#475569;margin-top:6px;display:flex;gap:8px;align-items:center;}
.pi-section-h span{background:#e2e8f0;color:#475569;border-radius:999px;padding:1px 9px;font-size:11px;}
.pi-nums{display:flex;flex-direction:column;gap:2px;font-size:12px;color:#64748b;}
.pi-nums b{color:#1e293b;}
.pi-empty{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:40px;text-align:center;color:#64748b;font-weight:600;}
.pi-loading{display:flex;justify-content:center;padding:60px;}
.pi-spin{width:30px;height:30px;border:3px solid #e2e8f0;border-top-color:#7c2d12;border-radius:50%;animation:pis .8s linear infinite;}
@keyframes pis{to{transform:rotate(360deg);}}
</style>
