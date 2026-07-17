<template>
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    :event="activeEvent"
    :doctype="doctype"
    :docname="doc?.name"
  />
</template>
<script setup>
import EventModal from '@/components/Modals/EventModal.vue'
import { showEventModal, activeEvent } from '@/composables/event'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
})

const activities = defineModel({ type: Object })

const { showModal } = useDoctypeModal()
const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// Event
function showEvent(e) {
  showEventModal.value = true
  activeEvent.value = e
}

// Tasks
function showTask(task) {
  showModal({
    name: task?.name,
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  activities.value.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    activities.value.reload()
  })
}

// Notes
function showNote(note) {
  showModal({
    name: note?.name,
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

function afterDoctype(d, isInsert = false) {
  activities.value.reload()

  let name =
    d.doctype == 'FCRM Note'
      ? 'note'
      : d.doctype == 'CRM Task'
        ? 'task'
        : 'call_log'

  let redirectHash = name + 's'
  if (d.doctype == 'CRM Call Log') {
    redirectHash = 'calls'
  }

  if (isInsert) {
    updateOnboardingStep('create_first_' + name)
    capture(name + '_created')
  } else {
    capture(name + '_updated')
  }

  redirect(redirectHash)
}

// Call Logs
// Salesperson's own number — fetched once per session, then cached.
let myPhoneNumber = null
async function getMyPhoneNumber() {
  if (myPhoneNumber !== null) return myPhoneNumber
  try {
    const r = await call('frappe.client.get_value', {
      doctype: 'User',
      filters: { name: getUser().name },
      fieldname: ['mobile_no', 'phone'],
    })
    myPhoneNumber = r?.mobile_no || r?.phone || ''
  } catch (e) {
    myPhoneNumber = ''
  }
  return myPhoneNumber
}

function nowDatetime() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  )
}

async function createCallLog() {
  // Prefill: From = salesperson's cell, To = number on file for this record,
  // Start Time = now (editable, so calls can be back-dated).
  const from = await getMyPhoneNumber()
  const to = props.doc?.mobile_no || props.doc?.phone || ''
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
      reference_doc: { ...props.doc },
      from,
      to,
      start_time: nowDatetime(),
      type: 'Outgoing',
      status: 'Completed',
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

// common
const route = useRoute()
const router = useRouter()

function redirect(tabName) {
  if (route.name == 'Lead' || route.name == 'Deal') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showEvent,
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  createCallLog,
})
</script>
