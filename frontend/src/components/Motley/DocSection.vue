<template>
  <div class="px-5 py-4">
    <!-- Section header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <FeatherIcon :name="icon" class="h-4 w-4" :class="`text-${color}-600`" />
        <span class="font-semibold text-sm text-ink-gray-8">{{ label }}</span>
        <span v-if="total > 0" class="text-xs text-ink-gray-4">({{ total }})</span>
      </div>
      <!-- Pagination controls -->
      <div v-if="totalPages > 1" class="flex items-center gap-1 text-xs">
        <button
          class="flex items-center justify-center h-6 w-6 rounded border transition-colors"
          :class="page > 1 ? 'border-ink-gray-3 hover:bg-surface-gray-2 text-ink-gray-7 cursor-pointer' : 'border-ink-gray-1 text-ink-gray-2 cursor-not-allowed'"
          :disabled="page <= 1"
          @click="go(page - 1)">
          <FeatherIcon name="chevron-left" class="h-3 w-3" />
        </button>
        <span class="px-2 text-ink-gray-5">{{ page }} / {{ totalPages }}</span>
        <button
          class="flex items-center justify-center h-6 w-6 rounded border transition-colors"
          :class="page < totalPages ? 'border-ink-gray-3 hover:bg-surface-gray-2 text-ink-gray-7 cursor-pointer' : 'border-ink-gray-1 text-ink-gray-2 cursor-not-allowed'"
          :disabled="page >= totalPages"
          @click="go(page + 1)">
          <FeatherIcon name="chevron-right" class="h-3 w-3" />
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <Spinner class="h-5 w-5 text-ink-gray-3" />
    </div>

    <!-- Empty -->
    <div v-else-if="!rows.length" class="py-4 text-center text-xs text-ink-gray-3">
      No {{ label.toLowerCase() }} found.
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto rounded border border-ink-gray-1">
      <table class="w-full border-collapse text-xs">
        <thead>
          <tr class="bg-surface-gray-1">
            <th v-for="col in columns" :key="col.key"
                class="whitespace-nowrap px-3 py-2 text-left font-semibold uppercase tracking-wide text-ink-gray-4 border-b border-ink-gray-1">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.name"
              class="cursor-pointer border-b border-ink-gray-1 last:border-0 transition-colors hover:bg-surface-gray-1"
              @click="openDoc(row.name)">
            <td v-for="col in columns" :key="col.key"
                class="px-3 py-2"
                :class="[
                  col.key === 'name' ? 'font-mono text-blue-600 hover:underline' : '',
                  col.key === 'status' ? '' : '',
                  col.currency ? 'text-right font-semibold' : '',
                ]">
              <template v-if="col.key === 'status'">
                <span :class="statusClass(row.status)"
                      class="rounded px-1.5 py-0.5 text-xs font-semibold">
                  {{ row.status }}
                </span>
              </template>
              <template v-else-if="col.currency">
                {{ row[col.key] > 0 ? fmtCurrency(row[col.key]) : '—' }}
              </template>
              <template v-else>
                {{ row[col.key] || '—' }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bottom pagination (for convenience on large sections) -->
    <div v-if="totalPages > 1" class="flex items-center justify-end gap-1 mt-2 text-xs">
      <button
        class="px-2 py-1 rounded border transition-colors"
        :class="page > 1 ? 'border-ink-gray-3 hover:bg-surface-gray-2 text-ink-gray-7 cursor-pointer' : 'border-ink-gray-1 text-ink-gray-2 cursor-not-allowed'"
        :disabled="page <= 1"
        @click="go(page - 1)">
        &lsaquo; Prev
      </button>
      <span class="px-2 text-ink-gray-4">{{ page }} of {{ totalPages }}</span>
      <button
        class="px-2 py-1 rounded border transition-colors"
        :class="page < totalPages ? 'border-ink-gray-3 hover:bg-surface-gray-2 text-ink-gray-7 cursor-pointer' : 'border-ink-gray-1 text-ink-gray-2 cursor-not-allowed'"
        :disabled="page >= totalPages"
        @click="go(page + 1)">
        Next &rsaquo;
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { call, FeatherIcon, Spinner } from 'frappe-ui'

const props = defineProps({
  customer: { type: String, required: true },
  doctype:  { type: String, required: true },
  label:    { type: String, required: true },
  icon:     { type: String, default: 'file' },
  color:    { type: String, default: 'blue' },
})

const loading    = ref(false)
const rows       = ref([])
const columns    = ref([])
const page       = ref(1)
const total      = ref(0)
const totalPages = ref(1)

const STATUS_MAP = {
  'Submitted': 'bg-green-100 text-green-700',
  'Paid':      'bg-green-100 text-green-700',
  'Unpaid':    'bg-red-100 text-red-700',
  'Overdue':   'bg-red-100 text-red-700',
  'Draft':     'bg-gray-100 text-gray-500',
  'Cancelled': 'bg-gray-100 text-gray-400 line-through',
  'To Deliver and Bill': 'bg-blue-100 text-blue-700',
  'To Bill':   'bg-amber-100 text-amber-700',
  'To Deliver':'bg-violet-100 text-violet-700',
  'Completed': 'bg-green-100 text-green-700',
  'Closed':    'bg-gray-100 text-gray-500',
  'Partly Paid': 'bg-amber-100 text-amber-700',
  'Return Issued': 'bg-orange-100 text-orange-700',
}
function statusClass(s) { return STATUS_MAP[s] || 'bg-gray-100 text-gray-600' }

function fmtCurrency(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const DOCTYPE_ROUTES = {
  'Sales Order':   'sales-order',
  'Sales Invoice': 'sales-invoice',
  'Delivery Note': 'delivery-note',
}
function openDoc(name) {
  const route = DOCTYPE_ROUTES[props.doctype] || props.doctype.toLowerCase().replace(/ /g, '-')
  window.open(`/app/${route}/${encodeURIComponent(name)}`, '_blank')
}

async function load() {
  loading.value = true
  try {
    const res = await call('crm.motley_terpz.customer_dashboard.get_customer_docs', {
      customer: props.customer,
      doctype:  props.doctype,
      page:     page.value,
    })
    rows.value       = res.rows || []
    columns.value    = res.columns || []
    total.value      = res.total || 0
    totalPages.value = res.total_pages || 1
  } catch (e) {
    console.error(`Failed to load ${props.doctype}:`, e)
    rows.value = []
  } finally {
    loading.value = false
  }
}

function go(p) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  load()
}

onMounted(load)
watch(() => props.customer, () => { page.value = 1; load() })
</script>
