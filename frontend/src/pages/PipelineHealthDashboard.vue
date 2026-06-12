<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-5 py-3 flex-shrink-0">
      <span class="text-lg font-semibold text-ink-gray-9">Pipeline Health</span>
      <Button variant="ghost" size="sm" :loading="loading" @click="reload">
        <template #icon><FeatherIcon name="refresh-cw" class="h-4 w-4" /></template>
      </Button>
    </div>

    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <Spinner class="h-6 w-6 text-ink-gray-4" />
    </div>

    <div v-else class="flex-1 overflow-y-auto p-5 space-y-6">

      <!-- Summary Row -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div v-for="kpi in summaryKpis" :key="kpi.label"
             class="rounded-xl border bg-surface-white px-4 py-3 text-center">
          <div class="text-xl font-bold" :class="kpi.color">{{ kpi.value }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ kpi.label }}</div>
        </div>
      </div>

      <!-- Per-Pipeline Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div
          v-for="p in pipelines"
          :key="p.key"
          class="rounded-xl border bg-surface-white overflow-hidden"
        >
          <!-- Pipeline Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b bg-surface-gray-1">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ p.icon }}</span>
              <span class="font-semibold text-ink-gray-9">{{ p.label }}</span>
              <Badge :label="String(p.lead_count)" variant="subtle" />
            </div>
            <Button
              variant="ghost"
              size="sm"
              :label="'Open'"
              @click="openPipeline(p.key)"
            />
          </div>

          <!-- Stage pills -->
          <div class="flex flex-wrap gap-2 px-4 py-3 border-b">
            <span
              v-for="(stage, name) in p.stage_counts"
              :key="name"
              class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="stageClass(name)"
            >
              {{ name }} <span class="font-bold">{{ stage }}</span>
            </span>
          </div>

          <!-- Metrics row -->
          <div class="grid grid-cols-4 divide-x text-center py-3">
            <div>
              <div class="text-lg font-bold text-green-600">{{ p.active_count }}</div>
              <div class="text-xs text-ink-gray-4 mt-0.5">Active</div>
            </div>
            <div>
              <div class="text-lg font-bold text-blue-600">{{ p.new_this_week }}</div>
              <div class="text-xs text-ink-gray-4 mt-0.5">New / wk</div>
            </div>
            <div>
              <div class="text-lg font-bold" :class="p.no_contact_30d > 0 ? 'text-orange-500' : 'text-ink-gray-5'">{{ p.no_contact_30d }}</div>
              <div class="text-xs text-ink-gray-4 mt-0.5">No contact 30d</div>
            </div>
            <div>
              <div class="text-lg font-bold" :class="p.overdue_followups > 0 ? 'text-red-500' : 'text-ink-gray-5'">{{ p.overdue_followups }}</div>
              <div class="text-xs text-ink-gray-4 mt-0.5">Overdue f/u</div>
            </div>
          </div>

          <!-- AR bar -->
          <div class="px-4 pb-3" v-if="p.total_ar > 0">
            <div class="flex justify-between text-xs text-ink-gray-5 mb-1">
              <span>AR: <b class="text-ink-gray-8">{{ fmtCurrency(p.total_ar) }}</b></span>
              <span v-if="p.overdue_ar > 0" class="text-red-500">
                30d+ overdue: <b>{{ fmtCurrency(p.overdue_ar) }}</b>
              </span>
            </div>
            <div v-if="p.total_ar > 0" class="h-2 rounded-full bg-surface-gray-2 overflow-hidden">
              <div
                class="h-full rounded-full bg-red-400"
                :style="{ width: Math.min((p.overdue_ar / p.total_ar) * 100, 100) + '%' }"
              />
            </div>
          </div>

          <!-- Top active leads -->
          <div v-if="p.top_leads && p.top_leads.length" class="border-t">
            <div class="px-4 py-2 text-xs font-semibold text-ink-gray-5 uppercase tracking-wide">
              Top Active Accounts
            </div>
            <table class="w-full text-sm">
              <tbody>
                <tr
                  v-for="lead in p.top_leads"
                  :key="lead.name"
                  class="border-t hover:bg-surface-gray-1 cursor-pointer"
                  @click="openLead(lead.name)"
                >
                  <td class="px-4 py-2 font-medium text-ink-gray-9 truncate max-w-[160px]">
                    {{ lead.lead_name }}
                  </td>
                  <td class="px-2 py-2">
                    <span class="text-xs rounded px-1.5 py-0.5 font-semibold" :class="tierClass(lead.tier)">
                      {{ lead.tier }}
                    </span>
                  </td>
                  <td class="px-2 py-2 text-right text-xs font-mono" :class="lead.ar_balance > 0 ? 'text-red-600' : 'text-ink-gray-4'">
                    {{ lead.ar_balance > 0 ? fmtCurrency(lead.ar_balance) : '—' }}
                  </td>
                  <td class="px-4 py-2 text-xs text-ink-gray-4 text-right">
                    {{ lead.last_contact_date ? fmtDate(lead.last_contact_date) : '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, FeatherIcon, Badge, Button, Spinner } from 'frappe-ui'

const router = useRouter()
const loading  = ref(false)
const pipelines = ref([])
const summary   = ref({})

const summaryKpis = computed(() => [
  { label: 'Total Leads',      value: summary.value.total_leads      || 0,                            color: 'text-ink-gray-8'  },
  { label: 'Active Accounts',  value: summary.value.total_active     || 0,                            color: 'text-green-600'   },
  { label: 'New This Week',    value: summary.value.new_this_week    || 0,                            color: 'text-blue-600'    },
  { label: 'No Contact 30d+',  value: summary.value.total_no_contact || 0,                            color: 'text-orange-500'  },
  { label: 'Total AR',         value: fmtCurrency(summary.value.total_ar),                            color: 'text-ink-gray-8'  },
  { label: 'AR Overdue 30d+',  value: fmtCurrency(summary.value.total_ar_overdue),                    color: 'text-red-600'     },
])

const PIPELINE_ROUTE_MAP = {
  fresh_frozen:      'PipelineFreshFrozen',
  rosin_solventless: 'PipelineRosin',
  retail_distro:     'PipelineDistro',
  tolling:           'PipelineTolling',
}

function fmtCurrency(val) {
  if (!val) return '$0'
  return '$' + parseFloat(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function fmtDate(val) {
  if (!val) return ''
  return new Date(val).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const STAGE_CLASSES = {
  'Lead':       'bg-gray-100 text-gray-600',
  'Contacted':  'bg-orange-100 text-orange-700',
  'Sample/QC':  'bg-blue-100 text-blue-700',
  'Active':     'bg-green-100 text-green-700',
  'Inactive':   'bg-amber-100 text-amber-700',
  'Lost':       'bg-red-100 text-red-600',
}

function stageClass(stage) {
  return STAGE_CLASSES[stage] || 'bg-gray-100 text-gray-500'
}

const TIER_CLASSES = {
  'AAA':              'bg-yellow-100 text-yellow-800',
  'AA':               'bg-blue-100 text-blue-700',
  'A':                'bg-green-100 text-green-700',
  'Friends & Family': 'bg-purple-100 text-purple-700',
  'WIP':              'bg-gray-100 text-gray-600',
  'Lead':             'bg-gray-50 text-gray-400',
}

function tierClass(tier) {
  return TIER_CLASSES[tier] || 'bg-gray-100 text-gray-500'
}

function openPipeline(key) {
  const name = PIPELINE_ROUTE_MAP[key]
  if (name) router.push({ name })
}

function openLead(leadName) {
  router.push({ name: 'Lead', params: { leadId: leadName } })
}

async function reload() {
  loading.value = true
  try {
    const result = await call('crm.motley_terpz.pipeline_health.get_pipeline_health')
    pipelines.value = result.pipelines || []
    summary.value   = result.summary  || {}
  } catch (e) {
    console.error('Pipeline health error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

