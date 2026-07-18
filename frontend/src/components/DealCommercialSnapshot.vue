<template>
  <div
    v-if="loading || hasAnyData"
    class="flex flex-col gap-3 border-b p-4"
  >
    <div class="text-sm font-medium text-ink-gray-6">{{ __('Commercial Snapshot') }}</div>

    <div v-if="loading" class="flex items-center gap-2 text-sm text-ink-gray-4">
      <LoadingIndicator class="h-4 w-4" />
      <span>{{ __('Loading...') }}</span>
    </div>

    <template v-else>
      <!-- License status -->
      <div v-if="data.license && data.license.status !== 'not_set'" class="flex items-center justify-between text-sm">
        <span class="text-ink-gray-5">{{ __('License') }}</span>
        <div class="flex items-center gap-1.5">
          <span v-if="data.license.license_number" class="text-ink-gray-7">{{ data.license.license_number }}</span>
          <Badge :theme="licenseTheme" :label="licenseLabel" variant="subtle" />
        </div>
      </div>

      <!-- AR -->
      <div v-if="data.ar" class="flex flex-col gap-1 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-ink-gray-5">{{ __('Outstanding AR') }}</span>
          <span class="font-medium" :class="data.ar.overdue_total > 0 ? 'text-ink-red-4' : 'text-ink-gray-8'">
            {{ money(data.ar.outstanding_total) }}
          </span>
        </div>
        <div v-if="data.ar.overdue_total > 0" class="text-xs text-ink-red-3">
          {{ __('{0} overdue (90+ days: {1})', [money(data.ar.overdue_total), money(data.ar.buckets['90_plus'])]) }}
        </div>
      </div>

      <!-- Manifest / logistics -->
      <div v-if="data.manifest" class="flex flex-col gap-1 text-sm">
        <div v-if="data.manifest.logistic_status" class="flex items-center justify-between">
          <span class="text-ink-gray-5">{{ __('Logistic Status') }}</span>
          <Badge variant="subtle" theme="blue" :label="data.manifest.logistic_status" />
        </div>
        <a
          v-if="data.manifest.manifest_url"
          :href="data.manifest.manifest_url"
          target="_blank"
          rel="noopener"
          class="text-xs text-ink-blue-3 hover:underline"
        >
          {{ __('View manifest ({0})', [data.manifest.delivery_note]) }}
        </a>
      </div>

      <!-- Stock -->
      <div v-if="data.stock" class="flex items-center justify-between text-sm">
        <span class="text-ink-gray-5">{{ __('Live Stock') }} ({{ data.stock.item_code }})</span>
        <div class="flex items-center gap-1.5">
          <span class="font-medium" :class="data.stock.actual_qty > 0 ? 'text-ink-gray-8' : 'text-ink-red-4'">
            {{ formatNumber(data.stock.actual_qty) }} {{ data.stock.stock_uom }}
          </span>
          <Badge v-if="data.stock.pre_order_only" theme="orange" variant="subtle" :label="__('Pre-Order Only')" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Badge, LoadingIndicator, call } from 'frappe-ui'

const props = defineProps({
  dealId: { type: String, required: true },
})

const loading = ref(true)
const data = ref({ organization: null, customer: null, ar: null, license: null, manifest: null, stock: null })

const hasAnyData = computed(() =>
  !!(data.value.ar || (data.value.license && data.value.license.status !== 'not_set') || data.value.manifest || data.value.stock),
)

const licenseTheme = computed(() => {
  let s = data.value.license?.status
  if (s === 'expired') return 'red'
  if (s === 'expiring_soon') return 'orange'
  if (s === 'valid') return 'green'
  return 'gray'
})

const licenseLabel = computed(() => {
  let s = data.value.license?.status
  if (s === 'expired') return __('Expired')
  if (s === 'expiring_soon') return __('Expiring Soon')
  if (s === 'valid') return __('Valid')
  return __('Not Set')
})

function money(v) {
  return '$' + parseFloat(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatNumber(v) {
  return parseFloat(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

async function load() {
  if (!props.dealId) return
  loading.value = true
  try {
    data.value = await call('crm.motley_terpz.deal_commercial.get_deal_commercial_snapshot', {
      deal_name: props.dealId,
    })
  } catch (e) {
    data.value = { organization: null, customer: null, ar: null, license: null, manifest: null, stock: null }
  } finally {
    loading.value = false
  }
}

watch(() => props.dealId, load, { immediate: true })

defineExpose({ reload: load })
</script>
