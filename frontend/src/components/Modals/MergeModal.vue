<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Merge {0}', [doctypeLabel]) }}
          </h3>
          <Button variant="ghost" icon="x" @click="show = false" />
        </div>

        <!-- Step 1: pick the duplicate -->
        <div v-if="step == 'pick'" class="flex flex-col gap-4">
          <p class="text-p-base text-ink-gray-6">
            {{
              __(
                'Pick the duplicate {0} to merge into {1}. The duplicate will be deleted; its notes, tasks, calls and deals move over automatically.',
                [doctypeLabel.toLowerCase(), primaryTitle],
              )
            }}
          </p>
          <div>
            <label class="mb-1.5 block text-sm text-ink-gray-5">
              {{ __('Duplicate {0}', [doctypeLabel.toLowerCase()]) }}
            </label>
            <Link
              :doctype="doctype"
              :filters="{ name: ['!=', primaryName] }"
              :value="duplicateName"
              :placeholder="__('Search for the duplicate record...')"
              @change="(v) => (duplicateName = v)"
            />
          </div>
          <ErrorMessage :message="errorMessage" />
          <div class="flex justify-end gap-2">
            <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
            <Button
              variant="solid"
              :label="__('Compare')"
              :disabled="!duplicateName"
              :loading="loadingPreview"
              @click="loadPreview"
            />
          </div>
        </div>

        <!-- Step 2: review diff & resolve conflicts -->
        <div v-else-if="step == 'review'" class="flex flex-col gap-4">
          <div class="flex items-center gap-3 rounded-lg bg-surface-gray-1 p-3 text-sm">
            <div class="flex-1">
              <div class="text-ink-gray-5">{{ __('Keeping') }}</div>
              <div class="font-medium text-ink-gray-9">{{ preview.survivor.title }}</div>
            </div>
            <FeatherIcon name="arrow-right" class="size-4 text-ink-gray-4" />
            <div class="flex-1">
              <div class="text-ink-gray-5">{{ __('Deleting (merges into above)') }}</div>
              <div class="font-medium text-ink-gray-9">{{ preview.duplicate.title }}</div>
            </div>
            <Button size="sm" variant="ghost" :label="__('Swap')" @click="swap" />
          </div>

          <div
            v-if="linkedSummary"
            class="rounded-lg border border-outline-gray-modals p-3 text-sm text-ink-gray-6"
          >
            {{ __('Will move over: {0}', [linkedSummary]) }}
          </div>

          <div v-if="!preview.fields.length" class="text-p-base text-ink-gray-6">
            {{ __('No conflicting fields — the records are otherwise identical.') }}
          </div>
          <div v-else class="flex flex-col divide-y divide-outline-gray-modals rounded-lg border border-outline-gray-modals">
            <div
              v-for="f in preview.fields"
              :key="f.fieldname"
              class="flex flex-col gap-2 p-3"
            >
              <div class="text-sm font-medium text-ink-gray-8">{{ __(f.label) }}</div>
              <div class="flex gap-2">
                <label
                  class="flex flex-1 cursor-pointer items-start gap-2 rounded-md border p-2 text-sm"
                  :class="
                    resolved[f.fieldname] == 'survivor'
                      ? 'border-outline-gray-4 bg-surface-gray-2'
                      : 'border-outline-gray-modals'
                  "
                >
                  <input
                    type="radio"
                    class="mt-1"
                    :name="f.fieldname"
                    :checked="resolved[f.fieldname] == 'survivor'"
                    @change="resolved[f.fieldname] = 'survivor'"
                  />
                  <span class="truncate text-ink-gray-7">
                    {{ f.survivor_value || __('(empty)') }}
                  </span>
                </label>
                <label
                  class="flex flex-1 cursor-pointer items-start gap-2 rounded-md border p-2 text-sm"
                  :class="
                    resolved[f.fieldname] == 'duplicate'
                      ? 'border-outline-gray-4 bg-surface-gray-2'
                      : 'border-outline-gray-modals'
                  "
                >
                  <input
                    type="radio"
                    class="mt-1"
                    :name="f.fieldname"
                    :checked="resolved[f.fieldname] == 'duplicate'"
                    @change="resolved[f.fieldname] = 'duplicate'"
                  />
                  <span class="truncate text-ink-gray-7">
                    {{ f.duplicate_value || __('(empty)') }}
                  </span>
                </label>
              </div>
            </div>
          </div>

          <ErrorMessage :message="errorMessage" />
          <div class="flex justify-between gap-2">
            <Button variant="subtle" :label="__('Back')" @click="step = 'pick'" />
            <div class="flex gap-2">
              <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
              <Button
                variant="solid"
                theme="red"
                :label="__('Merge & Delete Duplicate')"
                :loading="merging"
                @click="doMerge"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { Dialog, Button, ErrorMessage, FeatherIcon, call, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, required: true },
  primaryName: { type: String, required: true },
  primaryTitle: { type: String, default: '' },
})

const emit = defineEmits(['merged'])
const show = defineModel({ type: Boolean, default: false })
const router = useRouter()

const doctypeLabel = computed(() =>
  props.doctype == 'CRM Lead' ? __('Leads') : __('Contacts'),
)

const step = ref('pick')
const duplicateName = ref('')
const errorMessage = ref('')
const loadingPreview = ref(false)
const merging = ref(false)

const preview = ref(null)
const resolved = reactive({})
// which side is currently the survivor (swappable before merging)
const survivorName = ref(props.primaryName)
const duplicateForMerge = ref('')

const linkedSummary = computed(() => {
  if (!preview.value) return ''
  const l = preview.value.linked_records
  const parts = []
  if (l.notes) parts.push(__('{0} note(s)', [l.notes]))
  if (l.tasks) parts.push(__('{0} task(s)', [l.tasks]))
  if (l.calls) parts.push(__('{0} call(s)', [l.calls]))
  if (l.deals) parts.push(__('{0} deal(s)', [l.deals]))
  return parts.join(', ')
})

async function loadPreview() {
  errorMessage.value = ''
  loadingPreview.value = true
  try {
    const r = await call('crm.motley_terpz.merge.preview', {
      doctype: props.doctype,
      survivor: survivorName.value,
      duplicate: duplicateName.value,
    })
    preview.value = r
    duplicateForMerge.value = duplicateName.value
    for (const f of r.fields) {
      resolved[f.fieldname] = f.suggested
    }
    step.value = 'review'
  } catch (e) {
    errorMessage.value = e.messages?.[0] || __('Failed to compare records')
  } finally {
    loadingPreview.value = false
  }
}

function swap() {
  const oldSurvivor = survivorName.value
  survivorName.value = duplicateForMerge.value
  duplicateForMerge.value = oldSurvivor
  const t = preview.value.survivor
  preview.value.survivor = preview.value.duplicate
  preview.value.duplicate = t
  for (const f of preview.value.fields) {
    const sv = f.survivor_value
    f.survivor_value = f.duplicate_value
    f.duplicate_value = sv
    resolved[f.fieldname] = resolved[f.fieldname] == 'survivor' ? 'duplicate' : 'survivor'
  }
}

async function doMerge() {
  errorMessage.value = ''
  merging.value = true
  try {
    const resolvedValues = {}
    for (const f of preview.value.fields) {
      resolvedValues[f.fieldname] =
        resolved[f.fieldname] == 'survivor' ? f.survivor_value : f.duplicate_value
    }
    const r = await call('crm.motley_terpz.merge.execute', {
      doctype: props.doctype,
      survivor: survivorName.value,
      duplicate: duplicateForMerge.value,
      resolved_values: JSON.stringify(resolvedValues),
    })
    toast.success(__('Merged successfully'))
    show.value = false
    emit('merged', r.name)
    if (r.name !== props.primaryName) {
      // the record being viewed was the one deleted — follow to the survivor
      const routeName = props.doctype == 'CRM Lead' ? 'Lead' : 'Contact'
      const param = props.doctype == 'CRM Lead' ? 'leadId' : 'contactId'
      router.replace({ name: routeName, params: { [param]: r.name } })
    }
  } catch (e) {
    errorMessage.value = e.messages?.[0] || __('Failed to merge records')
  } finally {
    merging.value = false
  }
}
</script>
