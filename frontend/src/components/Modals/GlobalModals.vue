<template>
  <CreateDocumentModal
    v-if="showCreateDocumentModal"
    v-model="showCreateDocumentModal"
    :doctype="createDocumentDoctype"
    :data="createDocumentData"
    @callback="(data) => createDocumentCallback(data)"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    v-bind="quickEntryProps"
  />
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
  <AboutModal v-model="showAboutModal" />
  <FieldLayoutDialogContainer v-if="fieldLayoutDialogs.length" />
</template>
<script setup>
import { defineAsyncComponent } from 'vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
import { fieldLayoutDialogs } from '@/utils/renderFieldLayoutDialog'
import {
  showCreateDocumentModal,
  createDocumentDoctype,
  createDocumentData,
  createDocumentCallback,
} from '@/composables/document'
import {
  showQuickEntryModal,
  quickEntryProps,
  showAboutModal,
  showChangePasswordModal,
} from '@/composables/modals'

// Lazy-loaded: these (and the FieldLayout system they pull in) only need to
// download once the user actually opens one, instead of blocking every
// session's initial bundle.
const FieldLayoutDialogContainer = defineAsyncComponent(
  () => import('@/components/Modals/FieldLayoutDialogContainer.vue'),
)
const ChangePasswordModal = defineAsyncComponent(
  () => import('@/components/Modals/ChangePasswordModal.vue'),
)
const CreateDocumentModal = defineAsyncComponent(
  () => import('@/components/Modals/CreateDocumentModal.vue'),
)
const QuickEntryModal = defineAsyncComponent(
  () => import('@/components/Modals/QuickEntryModal.vue'),
)
</script>
