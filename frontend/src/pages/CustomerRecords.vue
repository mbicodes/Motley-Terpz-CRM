<template>
  <div class="cr-root">
    <div class="cr-topbar">
      <button class="cr-back" @click="$router.back()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
        Back
      </button>
      <span class="cr-title">{{ customerId }} — Records</span>
    </div>

    <!-- Sales Orders -->
    <div class="cr-section">
      <div class="cr-sec-hdr">
        <span class="cr-sec-title">Sales Orders</span>
        <div class="cr-hdr-right">
          <button class="cr-new-btn" @click="createNew('sales-order')">+ New Sales Order</button>
          <div class="cr-pager">
            <button class="cr-pbtn" :disabled="so.page<=1" @click="so.page--;loadSO()">&lsaquo;</button>
            <span class="cr-pinfo">{{ so.page }} / {{ so.totalPages }}</span>
            <button class="cr-pbtn" :disabled="so.page>=so.totalPages" @click="so.page++;loadSO()">&rsaquo;</button>
          </div>
        </div>
      </div>
      <div v-if="so.loading" class="cr-loading"><div class="cr-spinner"></div></div>
      <table v-else class="cr-table">
        <thead><tr><th>Order #</th><th>Date</th><th>Delivery Date</th><th>Status</th><th>Total</th><th>Advance Paid</th></tr></thead>
        <tbody>
          <tr v-for="r in so.rows" :key="r.name" class="cr-row" @click="open('sales-order', r.name)">
            <td class="cr-id">{{ r.name }}</td>
            <td>{{ r.transaction_date }}</td>
            <td>{{ r.delivery_date || '—' }}</td>
            <td><span class="cr-badge" :class="statusCls(r.status)">{{ r.status }}</span></td>
            <td class="cr-num">{{ fmt(r.grand_total) }}</td>
            <td class="cr-num">{{ r.advance_paid > 0 ? fmt(r.advance_paid) : '—' }}</td>
          </tr>
          <tr v-if="!so.rows.length"><td colspan="6" class="cr-empty">No sales orders found.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Invoices -->
    <div class="cr-section">
      <div class="cr-sec-hdr">
        <span class="cr-sec-title">Sales Invoices</span>
        <div class="cr-hdr-right">
          <button class="cr-new-btn" @click="createNew('sales-invoice')">+ New Sales Invoice</button>
          <div class="cr-pager">
            <button class="cr-pbtn" :disabled="inv.page<=1" @click="inv.page--;loadInv()">&lsaquo;</button>
            <span class="cr-pinfo">{{ inv.page }} / {{ inv.totalPages }}</span>
            <button class="cr-pbtn" :disabled="inv.page>=inv.totalPages" @click="inv.page++;loadInv()">&rsaquo;</button>
          </div>
        </div>
      </div>
      <div v-if="inv.loading" class="cr-loading"><div class="cr-spinner"></div></div>
      <table v-else class="cr-table">
        <thead><tr><th>Invoice #</th><th>Date</th><th>Due Date</th><th>Status</th><th>Amount</th><th>Outstanding</th><th>Terms</th></tr></thead>
        <tbody>
          <tr v-for="r in inv.rows" :key="r.name" class="cr-row" @click="open('sales-invoice', r.name)">
            <td class="cr-id">{{ r.name }}</td>
            <td>{{ r.posting_date }}</td>
            <td :class="isPast(r.due_date) && r.outstanding_amount > 0 ? 'cr-red' : ''">{{ r.due_date || '—' }}</td>
            <td><span class="cr-badge" :class="statusCls(r.status)">{{ r.status }}</span></td>
            <td class="cr-num">{{ fmt(r.grand_total) }}</td>
            <td class="cr-num" :class="r.outstanding_amount > 0 ? 'cr-red' : 'cr-green'">
              {{ r.outstanding_amount > 0 ? fmt(r.outstanding_amount) : '✓ Paid' }}
            </td>
            <td class="cr-muted">{{ r.payment_terms_template || '—' }}</td>
          </tr>
          <tr v-if="!inv.rows.length"><td colspan="7" class="cr-empty">No invoices found.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Delivery Notes -->
    <div class="cr-section">
      <div class="cr-sec-hdr">
        <span class="cr-sec-title">Delivery Notes</span>
        <div class="cr-hdr-right">
          <button class="cr-new-btn" @click="createNew('delivery-note')">+ New Delivery Note</button>
          <div class="cr-pager">
            <button class="cr-pbtn" :disabled="dn.page<=1" @click="dn.page--;loadDN()">&lsaquo;</button>
            <span class="cr-pinfo">{{ dn.page }} / {{ dn.totalPages }}</span>
            <button class="cr-pbtn" :disabled="dn.page>=dn.totalPages" @click="dn.page++;loadDN()">&rsaquo;</button>
          </div>
        </div>
      </div>
      <div v-if="dn.loading" class="cr-loading"><div class="cr-spinner"></div></div>
      <table v-else class="cr-table">
        <thead><tr><th>DN #</th><th>Date</th><th>Status</th><th>Total</th><th>LR No.</th></tr></thead>
        <tbody>
          <tr v-for="r in dn.rows" :key="r.name" class="cr-row" @click="open('delivery-note', r.name)">
            <td class="cr-id">{{ r.name }}</td>
            <td>{{ r.posting_date }}</td>
            <td><span class="cr-badge" :class="statusCls(r.status)">{{ r.status }}</span></td>
            <td class="cr-num">{{ fmt(r.grand_total) }}</td>
            <td class="cr-muted">{{ r.lr_no || '—' }}</td>
          </tr>
          <tr v-if="!dn.rows.length"><td colspan="5" class="cr-empty">No delivery notes found.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'

const route = useRoute()
const customerId = computed(() => route.params.customerId)

const so  = reactive({ rows:[], page:1, totalPages:1, loading:false })
const inv = reactive({ rows:[], page:1, totalPages:1, loading:false })
const dn  = reactive({ rows:[], page:1, totalPages:1, loading:false })

function fmt(v) { return '$ ' + parseFloat(v||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}) }
function isPast(dt) { return dt && new Date(dt) < new Date() }
function open(type, name) { window.open(`/app/${type}/${encodeURIComponent(name)}`, '_blank') }
function createNew(doctype) {
  window.open(`/app/${doctype}/new-${doctype}-1?customer=${encodeURIComponent(customerId.value)}`, '_blank')
}

const PAID  = ['Completed','Paid','Submitted']
const BAD   = ['Cancelled','Overdue','Return Issued']
function statusCls(s) {
  if (PAID.includes(s))                return 'cr-s-paid'
  if (BAD.includes(s))                 return 'cr-s-bad'
  if (s === 'To Deliver and Bill')     return 'cr-s-warn'
  if (s === 'To Bill')                 return 'cr-s-warn'
  if (s === 'Unpaid')                  return 'cr-s-bad'
  if (s === 'Partly Paid')             return 'cr-s-warn'
  return 'cr-s-draft'
}

async function loadSO() {
  so.loading = true
  try {
    const r = await call('crm.motley_terpz.customer_dashboard.get_sales_orders',
      { customer: customerId.value, page: so.page })
    so.rows = r.rows || []; so.totalPages = r.total_pages || 1
  } finally { so.loading = false }
}
async function loadInv() {
  inv.loading = true
  try {
    const r = await call('crm.motley_terpz.customer_dashboard.get_customer_invoices',
      { customer: customerId.value, page: inv.page })
    inv.rows = r.rows || []; inv.totalPages = r.total_pages || 1
  } finally { inv.loading = false }
}
async function loadDN() {
  dn.loading = true
  try {
    const r = await call('crm.motley_terpz.customer_dashboard.get_delivery_notes',
      { customer: customerId.value, page: dn.page })
    dn.rows = r.rows || []; dn.totalPages = r.total_pages || 1
  } finally { dn.loading = false }
}

onMounted(() => { loadSO(); loadInv(); loadDN() })
</script>

<style scoped>
.cr-root { display:flex; flex-direction:column; gap:16px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.cr-topbar { display:flex; align-items:center; gap:12px; background:#1e293b; border-radius:12px; padding:12px 20px; }
.cr-back { display:flex; align-items:center; gap:6px; color:#94a3b8; background:transparent; border:none; cursor:pointer; font-size:13px; }
.cr-back svg { width:16px; height:16px; }
.cr-title { font-size:16px; font-weight:800; color:#fff; }
.cr-section { background:#fff; border-radius:12px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,.05); overflow:hidden; }
.cr-sec-hdr { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #f1f5f9; }
.cr-sec-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#0f172a; }
.cr-hdr-right { display:flex; align-items:center; gap:10px; }
.cr-new-btn { display:flex; align-items:center; gap:4px; padding:5px 12px; border-radius:6px; border:1px solid #6366f1; background:#6366f1; color:#fff; font-size:11px; font-weight:600; cursor:pointer; transition:background .15s; white-space:nowrap; }
.cr-new-btn:hover { background:#4f46e5; border-color:#4f46e5; }
.cr-pager { display:flex; align-items:center; gap:6px; }
.cr-pbtn { width:28px; height:28px; border-radius:6px; border:1px solid #e2e8f0; background:#fff; cursor:pointer; font-size:18px; line-height:1; display:flex; align-items:center; justify-content:center; transition:background .15s; }
.cr-pbtn:hover:not(:disabled) { background:#f1f5f9; }
.cr-pbtn:disabled { opacity:.3; cursor:default; }
.cr-pinfo { font-size:12px; color:#64748b; min-width:44px; text-align:center; }
.cr-table { width:100%; border-collapse:collapse; font-size:12px; }
.cr-table th { padding:8px 14px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; background:#f8fafc; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
.cr-row { cursor:pointer; border-bottom:1px solid #f8fafc; transition:background .12s; }
.cr-row:hover { background:#f8fafc; }
.cr-table td { padding:9px 14px; white-space:nowrap; }
.cr-id { font-family:monospace; font-size:11px; color:#64748b; }
.cr-num { text-align:right; font-weight:600; }
.cr-muted { color:#94a3b8; }
.cr-red { color:#dc2626 !important; }
.cr-green { color:#059669 !important; }
.cr-empty { text-align:center; padding:20px; color:#94a3b8; font-size:12px; }
.cr-badge { padding:2px 8px; border-radius:8px; font-size:10px; font-weight:700; }
.cr-s-paid  { background:#d1fae5; color:#065f46; }
.cr-s-bad   { background:#fee2e2; color:#991b1b; }
.cr-s-warn  { background:#fef3c7; color:#92400e; }
.cr-s-draft { background:#f1f5f9; color:#475569; }
.cr-loading { display:flex; justify-content:center; padding:32px; }
.cr-spinner { width:28px; height:28px; border:2px solid #e2e8f0; border-top-color:#6366f1; border-radius:50%; animation:cr-spin .7s linear infinite; }
@keyframes cr-spin { to { transform:rotate(360deg); } }
</style>
