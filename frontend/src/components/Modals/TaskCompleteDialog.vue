<template>
  <Dialog v-model="show" :options="{ size: 'sm' }">
    <template #body-header>
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ __('Complete Task') }}
        </h3>
        <Button variant="ghost" @click="show = false">
          <template #icon>
            <LucideX class="h-4 w-4 text-ink-gray-9" />
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-2">
        <div class="text-p-base text-ink-gray-7">{{ task?.title }}</div>
        <FormControl
          type="textarea"
          :placeholder="__('Add a note about how this went (optional)')"
          v-model="note"
          :rows="4"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex flex-row-reverse gap-2">
        <Button
          variant="solid"
          :label="__('Mark Done')"
          :loading="completing"
          @click="submit"
        />
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Dialog, Button, FormControl, call } from 'frappe-ui'

const props = defineProps({
  task: { type: Object, default: null },
})
const emit = defineEmits(['completed'])

const show = defineModel({ type: Boolean })
const note = ref('')
const completing = ref(false)

watch(show, (val) => {
  if (val) note.value = ''
})

async function submit() {
  completing.value = true
  try {
    await call('crm.api.task.complete_task', {
      task: props.task.name,
      note: note.value,
    })
    show.value = false
    emit('completed')
  } finally {
    completing.value = false
  }
}
</script>
