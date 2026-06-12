<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-5 py-3 flex-shrink-0">
      <div class="flex items-center gap-3">
        <span class="text-lg font-semibold text-ink-gray-9">{{ pipelineLabel }}</span>
        <Badge
          v-if="totalDeals"
          :label="String(totalDeals)"
          variant="subtle"
        />
      </div>
      <div class="flex items-center gap-2">
        <Button variant="ghost" size="sm" :loading="loading" @click="reload">
          <template #icon>
            <FeatherIcon name="refresh-cw" class="h-4 w-4" />
          </template>
        </Button>
        <Button variant="solid" size="sm" @click="openNewDealModal(null)">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          New Deal
        </Button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <Spinner class="h-6 w-6 text-ink-gray-4" />
    </div>

    <!-- Kanban Board -->
    <div v-else class="flex-1 overflow-x-auto overflow-y-hidden">
      <div class="flex h-full gap-3 p-4 min-w-max">
        <div
          v-for="stage in stages"
          :key="stage.name"
          class="flex flex-col w-72 flex-shrink-0 rounded-xl bg-surface-gray-1 overflow-hidden"
        >
          <!-- Column Header -->
          <div class="flex items-center justify-between px-3 pt-3 pb-2">
            <div class="flex items-center gap-2">
              <span
                class="inline-block h-2.5 w-2.5 rounded-full flex-shrink-0"
                :class="stageColorClass(stage.color)"
              />
              <span class="text-sm font-semibold text-ink-gray-8">{{ stage.name }}</span>
              <span class="text-xs text-ink-gray-4 font-medium">
                {{ (columns[stage.name] || []).length }}
              </span>
            </div>
            <Button
              variant="ghost"
              size="xs"
              @click="openNewDealModal(stage.name)"
            >
              <template #icon>
                <FeatherIcon name="plus" class="h-3.5 w-3.5" />
              </template>
            </Button>
          </div>

          <!-- Cards -->
          <div class="flex-1 overflow-y-auto px-2 pb-3">
            <Draggable
              :list="columns[stage.name] || []"
              group="pipeline-deals"
              item-key="name"
              class="flex flex-col gap-2 min-h-[40px]"
              @change="(evt) => onColumnChange(stage.name, evt)"
            >
              <template #item="{ element: deal }">
                <div
                  class="rounded-lg border bg-surface-white p-3 cursor-pointer hover:shadow-sm transition-shadow"
                  @click="openDeal(deal.name)"
                >
                  <!-- Organization -->
                  <div class="flex items-center gap-2 mb-2">
                    <Avatar
                      :image="deal.organization_logo"
                      :label="deal.organization || 'Unknown'"
                      size="sm"
                    />
                    <span class="text-sm font-semibold text-ink-gray-9 truncate">
                      {{ deal.organization || '(No Organization)' }}
                    </span>
                  </div>

                  <!-- Deal Value -->
                  <div v-if="deal.deal_value" class="text-sm text-ink-gray-7 mb-1.5">
                    <span class="font-semibold text-ink-gray-9">{{ fmtCurrency(deal.deal_value) }}</span>
                  </div>

                  <!-- Pipeline-specific highlights -->
                  <div v-if="pipelineKey === 'tolling' && deal.custom_lbs_per_run" class="text-xs text-ink-gray-5 mb-1">
                    {{ deal.custom_lbs_per_run }} lbs/run
                    <span v-if="deal.custom_rate_per_lb"> · {{ fmtCurrency(deal.custom_rate_per_lb) }}/lb</span>
                    <span v-if="deal.custom_byo_flag" class="ml-1 rounded bg-amber-100 px-1 py-0.5 text-amber-700 font-semibold">BYO</span>
                  </div>
                  <div v-if="pipelineKey === 'tolling' && deal.custom_input_material_type" class="text-xs text-ink-gray-5 mb-1">
                    {{ deal.custom_input_material_type }}
                  </div>
                  <div v-if="pipelineKey === 'tolling' && deal.custom_work_order" class="text-xs text-ink-gray-5 mb-1">
                    WO: {{ deal.custom_work_order }}
                  </div>

                  <div v-if="(pipelineKey === 'fresh_frozen' || pipelineKey === 'rosin') && deal.custom_strain_name" class="text-xs text-ink-gray-5 mb-1">
                    {{ deal.custom_strain_name }}
                    <span v-if="deal.custom_available_lbs"> · {{ deal.custom_available_lbs }} lbs</span>
                    <span v-if="deal.custom_target_output_g"> · {{ deal.custom_target_output_g }}g target</span>
                  </div>

                  <div v-if="pipelineKey === 'distro' && deal.custom_license_number" class="text-xs text-ink-gray-5 mb-1">
                    {{ deal.custom_license_number }}
                    <span v-if="deal.custom_license_verified" class="ml-1 rounded bg-green-100 px-1 py-0.5 text-green-700 font-semibold">✓ Verified</span>
                  </div>

                  <!-- Footer: owner + closure date -->
                  <div class="flex items-center justify-between mt-2 pt-2 border-t">
                    <div class="flex items-center gap-1.5">
                      <Avatar
                        :image="deal.deal_owner_image"
                        :label="deal.deal_owner_name || deal.deal_owner"
                        size="xs"
                      />
                      <span class="text-xs text-ink-gray-5 truncate max-w-[100px]">
                        {{ deal.deal_owner_name || deal.deal_owner }}
                      </span>
                    </div>
                    <span v-if="deal.expected_closure_date" class="text-xs text-ink-gray-4">
                      {{ fmtDate(deal.expected_closure_date) }}
                    </span>
                  </div>
                </div>
              </template>
            </Draggable>
          </div>
        </div>
      </div>
    </div>

    <!-- New Deal Modal -->
    <Dialog
      v-if="showNewDealModal"
      v-model="showNewDealModal"
      :options="{
        title: `New ${pipelineLabel} Deal`,
        size: 'md',
        actions: [
          { label: 'Create', variant: 'solid', loading: creating, onClick: submitNewDeal },
          { label: 'Cancel', onClick: () => (showNewDealModal = false) },
        ],
      }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3 py-2">
          <FormControl
            v-model="newDeal.organization"
            type="link"
            doctype="CRM Organization"
            label="Organization"
            placeholder="Search organization…"
          />
          <FormControl
            v-model="newDeal.deal_owner"
            type="link"
            doctype="User"
            label="Owner"
            placeholder="Assign owner"
          />
          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="newDeal.deal_value"
              type="float"
              label="Deal Value"
              placeholder="0.00"
            />
            <FormControl
              v-model="newDeal.expected_closure_date"
              type="date"
              label="Expected Close"
            />
          </div>
          <FormControl
            v-model="newDeal.custom_pipeline_stage"
            type="select"
            label="Stage"
            :options="stageOptions"
          />

          <!-- Tolling extras -->
          <template v-if="pipelineKey === 'tolling'">
            <FormControl
              v-model="newDeal.custom_input_material_type"
              type="select"
              label="Input Material Type"
              :options="[
                { label: '—', value: '' },
                { label: 'Fresh Frozen',  value: 'Fresh Frozen'  },
                { label: 'Dry Ice Sift',  value: 'Dry Ice Sift'  },
                { label: 'Dry Sift',      value: 'Dry Sift'      },
                { label: 'Kief',          value: 'Kief'          },
                { label: 'Trimmed Bud',   value: 'Trimmed Bud'   },
              ]"
            />
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="newDeal.custom_lbs_per_run"
                type="float"
                label="Lbs Per Run"
              />
              <FormControl
                v-model="newDeal.custom_rate_per_lb"
                type="float"
                label="Rate Per Lb ($)"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="newDeal.custom_run_frequency"
                type="select"
                label="Run Frequency"
                :options="[
                  { label: '—',          value: ''          },
                  { label: 'Weekly',     value: 'Weekly'    },
                  { label: 'Bi-Weekly',  value: 'Bi-Weekly' },
                  { label: 'Monthly',    value: 'Monthly'   },
                  { label: 'As-Needed',  value: 'As-Needed' },
                ]"
              />
              <FormControl
                v-model="newDeal.custom_work_order"
                type="link"
                doctype="Work Order"
                label="Work Order"
              />
            </div>
            <FormControl
              v-model="newDeal.custom_byo_flag"
              type="checkbox"
              label="BYO Material"
            />
          </template>

          <!-- Fresh Frozen / Rosin extras -->
          <template v-if="pipelineKey === 'fresh_frozen' || pipelineKey === 'rosin'">
            <FormControl
              v-model="newDeal.custom_strain_name"
              type="data"
              label="Strain Name"
            />
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-if="pipelineKey === 'fresh_frozen'"
                v-model="newDeal.custom_available_lbs"
                type="float"
                label="Available Lbs"
              />
              <FormControl
                v-model="newDeal.custom_target_output_g"
                type="float"
                label="Target Output (g)"
              />
            </div>
          </template>

          <!-- Distribution extras -->
          <template v-if="pipelineKey === 'distro'">
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="newDeal.custom_license_number"
                type="data"
                label="License Number"
              />
              <FormControl
                v-model="newDeal.custom_license_verified"
                type="checkbox"
                label="License Verified"
              />
            </div>
          </template>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { FeatherIcon, Badge, Button, Spinner, Avatar, Dialog, FormControl } from 'frappe-ui'
import Draggable from 'vuedraggable'

const props = defineProps({ pipeline: { type: String, required: true } })

const route = useRoute()
const router = useRouter()

const loading   = ref(false)
const creating  = ref(false)
const stages    = ref([])
const columns   = ref({})
const showNewDealModal = ref(false)
const newDealStage     = ref('')

const newDeal = ref({
  organization: '',
  deal_owner: '',
  deal_value: null,
  expected_closure_date: '',
  custom_pipeline_stage: '',
  custom_input_material_type: '',
  custom_lbs_per_run: null,
  custom_rate_per_lb: null,
  custom_run_frequency: '',
  custom_work_order: '',
  custom_byo_flag: 0,
  custom_strain_name: '',
  custom_available_lbs: null,
  custom_target_output_g: null,
  custom_license_number: '',
  custom_license_verified: 0,
})

const pipelineKey = computed(() => props.pipeline)

const PIPELINE_LABELS = {
  fresh_frozen: '❄️ Fresh Frozen',
  rosin:        '🌿 Solventless / Rosin',
  distro:       '🏪 Distribution',
  tolling:      '⚙️ Tolling',
}

const pipelineLabel = computed(() => PIPELINE_LABELS[pipelineKey.value] || pipelineKey.value)

const totalDeals = computed(() =>
  Object.values(columns.value).reduce((s, col) => s + col.length, 0)
)

const stageOptions = computed(() =>
  stages.value.map((s) => ({ label: s.name, value: s.name }))
)

const STAGE_COLOR_MAP = {
  blue:   'bg-blue-500',
  purple: 'bg-purple-500',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-400',
  green:  'bg-green-500',
  gray:   'bg-gray-400',
  red:    'bg-red-500',
}

function stageColorClass(color) {
  return STAGE_COLOR_MAP[color] || 'bg-gray-400'
}

function fmtCurrency(val) {
  if (!val) return ''
  return '$ ' + parseFloat(val).toLocaleString(undefined, {
    minimumFractionDigits: 0, maximumFractionDigits: 2
  })
}

function fmtDate(val) {
  if (!val) return ''
  const d = new Date(val)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

async function reload() {
  loading.value = true
  try {
    const result = await call('crm.motley_terpz.pipeline_kanban.get_pipeline_deals', {
      pipeline: pipelineKey.value,
    })
    stages.value  = result.stages || []
    columns.value = result.columns || {}
  } catch (e) {
    console.error('Pipeline load error:', e)
  } finally {
    loading.value = false
  }
}

function openDeal(dealName) {
  router.push({ name: 'Deal', params: { dealId: dealName } })
}

function openNewDealModal(stageName) {
  newDealStage.value = stageName || (stages.value[0]?.name || '')
  Object.assign(newDeal.value, {
    organization: '',
    deal_owner: '',
    deal_value: null,
    expected_closure_date: '',
    custom_pipeline_stage: newDealStage.value,
    custom_input_material_type: '',
    custom_lbs_per_run: null,
    custom_rate_per_lb: null,
    custom_run_frequency: '',
    custom_work_order: '',
    custom_byo_flag: 0,
    custom_strain_name: '',
    custom_available_lbs: null,
    custom_target_output_g: null,
    custom_license_number: '',
    custom_license_verified: 0,
  })
  showNewDealModal.value = true
}

async function submitNewDeal() {
  creating.value = true
  try {
    const args = {
      pipeline: pipelineKey.value,
      stage: newDeal.value.custom_pipeline_stage,
      organization: newDeal.value.organization || null,
      deal_value: newDeal.value.deal_value || null,
      deal_owner: newDeal.value.deal_owner || null,
      expected_closure_date: newDeal.value.expected_closure_date || null,
    }
    // Add pipeline-specific extras
    const extraFields = {
      fresh_frozen: ['custom_strain_name', 'custom_available_lbs', 'custom_target_output_g'],
      rosin:        ['custom_strain_name', 'custom_target_output_g'],
      distro:       ['custom_license_number', 'custom_license_verified'],
      tolling:      [
        'custom_input_material_type', 'custom_lbs_per_run', 'custom_rate_per_lb',
        'custom_run_frequency', 'custom_work_order', 'custom_byo_flag',
      ],
    }[pipelineKey.value] || []

    extraFields.forEach((f) => { args[f] = newDeal.value[f] })

    await call('crm.motley_terpz.pipeline_kanban.create_pipeline_deal', args)
    showNewDealModal.value = false
    await reload()
  } catch (e) {
    console.error('Create deal error:', e)
  } finally {
    creating.value = false
  }
}

async function onColumnChange(stageName, evt) {
  // Fired when a card lands in this column (added = dropped here from another col)
  if (!evt.added) return
  const deal = evt.added.element
  if (!deal?.name) return

  try {
    await call('crm.motley_terpz.pipeline_kanban.update_deal_stage', {
      deal_name: deal.name,
      new_stage: stageName,
      pipeline: pipelineKey.value,
    })
  } catch (e) {
    console.error('Stage update error:', e)
    await reload()
  }
}

onMounted(reload)
watch(() => props.pipeline, reload)
</script>
