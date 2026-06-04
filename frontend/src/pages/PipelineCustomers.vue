<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-5 py-3">
      <div class="flex items-center gap-2">
        <span class="text-lg font-semibold text-ink-gray-9">{{ pipelineLabel }}</span>
        <Badge v-if="customers.length" :label="String(customers.length)" variant="subtle" />
      </div>
      <Button :loading="loading" variant="ghost" size="sm" @click="reload">
        <template #icon><FeatherIcon name="refresh-cw" class="h-4 w-4" /></template>
      </Button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <Spinner class="h-6 w-6 text-ink-gray-4" />
    </div>

    <!-- Empty -->
    <div v-else-if="!customers.length" class="flex flex-1 flex-col items-center justify-center gap-2 text-ink-gray-4">
      <FeatherIcon name="users" class="h-10 w-10" />
      <p class="text-sm">No customers found for this pipeline.</p>
    </div>

    <!-- Table -->
    <div v-else class="flex-1 overflow-auto">
      <table class="w-full border-collapse text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-1">
          <tr>
            <th v-for="col in columns" :key="col.key"
                class="whitespace-nowrap border-b px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-ink-gray-5"
                :style="col.width ? `min-width:${col.width}` : ''">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in customers" :key="row.customer"
              class="cursor-pointer border-b transition-colors hover:bg-surface-gray-1"
              @click="openDashboard(row.customer)">
            <td class="px-3 py-2 font-semibold text-ink-gray-9">{{ row.customer_name || row.customer }}</td>
            <td class="px-3 py-2 font-mono text-xs text-ink-gray-5">{{ row.customer }}</td>
            <td class="px-3 py-2">
              <span :class="arStatusClass(row.ar_status)" class="rounded px-2 py-0.5 text-xs font-semibold">
                {{ row.ar_status }}
              </span>
            </td>
            <td class="px-3 py-2 text-right font-semibold" :class="row.ar_balance > 0 ? 'text-red-600' : 'text-ink-gray-5'">
              {{ row.ar_balance > 0 ? fmtCurrency(row.ar_balance) : '—' }}
            </td>
            <td class="px-3 py-2 text-right" :class="row.ar_aging_days > 90 ? 'text-red-600 font-bold' : row.ar_aging_days > 30 ? 'text-amber-600' : 'text-ink-gray-5'">
              {{ row.ar_aging_days > 0 ? row.ar_aging_days : '—' }}
            </td>
            <td class="px-3 py-2 text-ink-gray-5">{{ row.last_invoice_date || '—' }}</td>
            <td class="px-3 py-2 text-right text-ink-gray-7">{{ row.last_invoice_amount > 0 ? fmtCurrency(row.last_invoice_amount) : '—' }}</td>
            <td class="px-3 py-2 text-ink-gray-5">{{ row.last_payment_date || '—' }}</td>
            <td class="px-3 py-2 text-right text-ink-gray-7">{{ row.mtd_revenue > 0 ? fmtCurrency(row.mtd_revenue) : '—' }}</td>
            <td class="px-3 py-2 text-right text-ink-gray-7">{{ row.trailing_8w_revenue > 0 ? fmtCurrency(row.trailing_8w_revenue) : '—' }}</td>
            <td class="px-3 py-2 text-ink-gray-5 text-xs">{{ row.payment_terms || '—' }}</td>
            <td class="px-3 py-2 text-center">
              <span v-if="row.cod_flag" class="rounded bg-amber-100 px-1.5 py-0.5 text-xs font-bold text-amber-800">COD</span>
              <span v-else class="text-ink-gray-3">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { FeatherIcon, Badge, Button, Spinner } from 'frappe-ui'

const route = useRoute()
const loading = ref(false)
const customers = ref([])

const PIPELINE_LABELS = {
  fresh_frozen:      '❄️ Fresh Frozen Customers',
  rosin_solventless: '🌿 Rosin / Solventless Customers',
  retail_distro:     '🏪 Retail / Distro Customers',
  tolling:           '⚙️ Tolling Customers',
}

const pipeline = computed(() => route.params.pipeline || '')
const pipelineLabel = computed(() => PIPELINE_LABELS[pipeline.value] || 'Customers')

const columns = [
  { key: 'customer_name',       label: 'Account',        width: '160px' },
  { key: 'customer',            label: 'ERP Customer',   width: '140px' },
  { key: 'ar_status',           label: 'AR Status',      width: '90px'  },
  { key: 'ar_balance',          label: 'AR Balance',     width: '110px' },
  { key: 'ar_aging_days',       label: 'Aging (days)',   width: '90px'  },
  { key: 'last_invoice_date',   label: 'Last Invoice',   width: '100px' },
  { key: 'last_invoice_amount', label: 'Invoice Amt',    width: '100px' },
  { key: 'last_payment_date',   label: 'Last Payment',   width: '100px' },
  { key: 'mtd_revenue',         label: 'MTD Revenue',    width: '100px' },
  { key: 'trailing_8w_revenue', label: '8-Wk Revenue',   width: '100px' },
  { key: 'payment_terms',       label: 'Payment Terms',  width: '100px' },
  { key: 'cod_flag',            label: 'COD',            width: '60px'  },
]

function fmtCurrency(val) {
  return '$ ' + parseFloat(val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function arStatusClass(status) {
  switch (status) {
    case 'Blocked':  return 'bg-red-100 text-red-700'
    case 'Overdue':  return 'bg-amber-100 text-amber-700'
    case 'Watch':    return 'bg-blue-100 text-blue-700'
    case 'Clean':    return 'bg-green-100 text-green-700'
    default:         return 'bg-gray-100 text-gray-500'
  }
}

const router = useRouter()
function openDashboard(customerName) {
  router.push({ name: 'CustomerDashboard', params: { customerId: customerName } })
}
function openCustomer(customerName) {
  window.open(`/app/customer/${encodeURIComponent(customerName)}`, '_blank')
}

async function reload() {
  if (!pipeline.value) return
  loading.value = true
  customers.value = []
  try {
    const result = await call('crm.motley_terpz.customer_pipelines.get_pipeline_customers', {
      pipeline: pipeline.value,
      page_length: 200,
    })
    customers.value = result || []
  } catch (e) {
    console.error('Failed to load pipeline customers:', e)
  } finally {
    loading.value = false
  }
}

onMounted(reload)
watch(pipeline, reload)
</script>
