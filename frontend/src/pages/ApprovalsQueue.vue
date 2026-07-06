<template>
  <div class="aq-root">
    <div class="aq-topbar">
      <span class="aq-title">Quotation Approvals</span>
      <span class="aq-sub" v-if="!loading">{{ rows.length }} awaiting your approval</span>
    </div>

    <div v-if="loading" class="aq-loading"><div class="aq-spinner"></div></div>

    <template v-else>
      <div v-if="!rows.length" class="aq-empty">
        🎉 Nothing waiting on you. All caught up.
      </div>

      <div v-else class="aq-card">
        <table class="aq-table">
          <thead>
            <tr>
              <th style="width:15%">Quotation</th>
              <th style="width:22%">Customer</th>
              <th style="width:16%">Submitted by</th>
              <th style="width:9%;text-align:right">Discount</th>
              <th style="width:10%">Tier</th>
              <th style="width:13%;text-align:right">Total</th>
              <th style="width:15%;text-align:right">Action</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="r in rows" :key="r.name">
              <tr class="aq-row">
                <td class="aq-mono">
                  <a :href="`/app/quotation/${encodeURIComponent(r.name)}`" target="_blank">{{ r.name }}</a>
                </td>
                <td>{{ r.customer_name || r.party_name || '—' }}</td>
                <td>{{ r.owner_fullname || r.owner }}</td>
                <td style="text-align:right;font-weight:700">{{ (r.custom_discount_pct_effective || 0).toFixed(1) }}%</td>
                <td>
                  <span class="aq-tier" :class="r.custom_required_approval_level === 'Finance' ? 'aq-tier-fin' : 'aq-tier-mgr'">
                    {{ r.custom_required_approval_level }}
                  </span>
                </td>
                <td style="text-align:right">{{ fmt(r.grand_total) }}</td>
                <td style="text-align:right">
                  <button class="aq-btn aq-approve" :disabled="busy === r.name" @click="approve(r)">Approve</button>
                  <button class="aq-btn aq-reject" :disabled="busy === r.name" @click="toggleReject(r.name)">Reject</button>
                </td>
              </tr>
              <tr v-if="rejecting === r.name" class="aq-reject-row">
                <td colspan="7">
                  <div class="aq-reject-box">
                    <textarea v-model="reason" class="aq-reason" rows="2"
                      placeholder="Reason for rejection (required) — visible to the rep and on the deal timeline"></textarea>
                    <div class="aq-reject-actions">
                      <button class="aq-btn aq-reject" :disabled="busy === r.name || !reason.trim()" @click="reject(r)">Confirm Reject</button>
                      <button class="aq-btn aq-cancel" @click="cancelReject()">Cancel</button>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-if="message" class="aq-toast" :class="`aq-toast-${messageType}`">{{ message }}</div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const loading = ref(true)
const rows = ref([])
const busy = ref(null)
const rejecting = ref(null)
const reason = ref('')
const message = ref('')
const messageType = ref('green')

async function load() {
  loading.value = true
  try {
    rows.value = await call('cannabis_management.overrides.quotation_approval.get_my_pending_approvals')
  } finally {
    loading.value = false
  }
}

function fmt(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function flash(text, type = 'green') {
  message.value = text
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3500)
}

function toggleReject(name) {
  rejecting.value = rejecting.value === name ? null : name
  reason.value = ''
}
function cancelReject() {
  rejecting.value = null
  reason.value = ''
}

async function approve(r) {
  busy.value = r.name
  try {
    await call('cannabis_management.overrides.quotation_approval.approve_quotation', { name: r.name })
    flash(`Approved ${r.name}`, 'green')
    await load()
  } catch (e) {
    flash(e?.messages?.[0] || 'Approval failed', 'red')
  } finally {
    busy.value = null
  }
}

async function reject(r) {
  if (!reason.value.trim()) return
  busy.value = r.name
  try {
    await call('cannabis_management.overrides.quotation_approval.reject_quotation', {
      name: r.name, reason: reason.value.trim(),
    })
    flash(`Rejected ${r.name}`, 'orange')
    cancelReject()
    await load()
  } catch (e) {
    flash(e?.messages?.[0] || 'Rejection failed', 'red')
  } finally {
    busy.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.aq-root { display:flex; flex-direction:column; gap:14px; padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
.aq-topbar { display:flex; align-items:center; justify-content:space-between; background:#1e293b; border-radius:12px; padding:14px 20px; }
.aq-title { font-size:16px; font-weight:800; color:#fff; }
.aq-sub { font-size:12px; font-weight:600; color:#94a3b8; }
.aq-card { background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; }
.aq-table { width:100%; border-collapse:collapse; font-size:13px; }
.aq-table th { text-align:left; padding:10px 14px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:#64748b; border-bottom:1px solid #e2e8f0; background:#f8fafc; }
.aq-row td { padding:11px 14px; border-bottom:1px solid #f1f5f9; }
.aq-mono a { font-family:ui-monospace,Menlo,monospace; color:#2563eb; text-decoration:none; }
.aq-mono a:hover { text-decoration:underline; }
.aq-tier { font-size:10px; font-weight:700; padding:2px 8px; border-radius:999px; }
.aq-tier-mgr { background:#dbeafe; color:#1d4ed8; }
.aq-tier-fin { background:#fef3c7; color:#b45309; }
.aq-btn { font-size:11px; font-weight:700; padding:5px 11px; border-radius:6px; border:none; cursor:pointer; margin-left:6px; }
.aq-btn:disabled { opacity:.45; cursor:default; }
.aq-approve { background:#059669; color:#fff; }
.aq-reject { background:#dc2626; color:#fff; }
.aq-cancel { background:#e2e8f0; color:#334155; }
.aq-reject-row td { padding:0 14px 12px; }
.aq-reject-box { display:flex; flex-direction:column; gap:8px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:10px; }
.aq-reason { width:100%; border:1px solid #e2e8f0; border-radius:6px; padding:8px; font-size:13px; resize:vertical; }
.aq-reject-actions { display:flex; gap:8px; }
.aq-empty { background:#fff; border-radius:12px; border:1px solid #e2e8f0; padding:48px; text-align:center; color:#64748b; font-size:14px; font-weight:600; }
.aq-loading { display:flex; justify-content:center; padding:60px; }
.aq-spinner { width:32px; height:32px; border:3px solid #e2e8f0; border-top-color:#1e293b; border-radius:50%; animation:aq-spin .8s linear infinite; }
@keyframes aq-spin { to { transform:rotate(360deg); } }
.aq-toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); padding:10px 20px; border-radius:8px; font-size:13px; font-weight:700; color:#fff; box-shadow:0 8px 24px rgba(0,0,0,.18); }
.aq-toast-green { background:#059669; }
.aq-toast-orange { background:#d97706; }
.aq-toast-red { background:#dc2626; }
</style>
