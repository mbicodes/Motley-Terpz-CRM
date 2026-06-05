<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">

    <!-- Header -->
    <div class="flex items-center gap-3 border-b px-5 py-3">
      <button class="flex items-center gap-1 text-sm text-ink-gray-5 hover:text-ink-gray-9 transition-colors"
              @click="$router.back()">
        <FeatherIcon name="arrow-left" class="h-4 w-4" />
        Back
      </button>
      <div class="h-4 w-px bg-ink-gray-2" />
      <div class="flex flex-1 items-center gap-3">
        <span class="text-base font-bold text-ink-gray-9">
          {{ info?.customer_name || customerId }}
        </span>
        <span v-if="info?.customer_group"
              class="rounded bg-surface-gray-2 px-2 py-0.5 text-xs text-ink-gray-5">
          {{ info.customer_group }}
        </span>
        <span v-if="info?.is_frozen"
              class="rounded bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700">
          FROZEN
        </span>
      </div>
      <!-- AR snapshot pills -->
      <div v-if="info" class="flex items-center gap-2 text-xs">
        <span :class="arStatusClass(info.ar_status)"
              class="rounded px-2 py-1 font-semibold">
          {{ info.ar_status }}
        </span>
        <span class="rounded bg-surface-gray-1 px-2 py-1 text-ink-gray-6">
          AR: <strong>{{ fmtCurrency(info.ar_balance) }}</strong>
        </span>
        <span class="rounded bg-surface-gray-1 px-2 py-1 text-ink-gray-6">
          Aging: <strong>{{ info.ar_aging_days }}d</strong>
        </span>
        <span class="rounded bg-surface-gray-1 px-2 py-1 text-ink-gray-6">
          MTD: <strong>{{ fmtCurrency(info.mtd_revenue) }}</strong>
        </span>
      </div>
    </div>

    <!-- 3 sections -->
    <div class="flex-1 overflow-y-auto divide-y">
      <DocSection
        v-for="dt in doctypes"
        :key="dt.doctype"
        :customer="customerId"
        :doctype="dt.doctype"
        :label="dt.label"
        :icon="dt.icon"
        :color="dt.color"
      />
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call, FeatherIcon } from 'frappe-ui'
import DocSection from '@/components/Motley/DocSection.vue'

const props  = defineProps({ customerId: { type: String, required: true } })
const route  = useRoute()
const info   = ref(null)

const doctypes = [
  { doctype: 'Sales Order',   label: 'Sales Orders',    icon: 'shopping-cart', color: 'violet' },
  { doctype: 'Sales Invoice', label: 'Sales Invoices',  icon: 'file-text',     color: 'blue'   },
  { doctype: 'Delivery Note', label: 'Delivery Notes',  icon: 'truck',         color: 'green'  },
]

const STATUS_COLORS = {
  'Blocked': 'bg-red-100 text-red-700',
  'Overdue': 'bg-amber-100 text-amber-700',
  'Watch':   'bg-blue-100 text-blue-700',
  'Clean':   'bg-green-100 text-green-700',
}
function arStatusClass(s) { return STATUS_COLORS[s] || 'bg-gray-100 text-gray-500' }
function fmtCurrency(v) {
  return '$ ' + parseFloat(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(async () => {
  try {
    info.value = await call('crm.motley_terpz.customer_dashboard.get_customer_info', {
      customer: props.customerId,
    })
  } catch (e) {
    console.error('Failed to load customer info:', e)
  }
})
</script>
