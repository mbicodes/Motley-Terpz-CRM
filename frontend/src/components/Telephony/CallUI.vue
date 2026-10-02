<template>
  <TwilioCallUI v-if="isEnabled('twilio')" ref="twilio" />
  <ExotelCallUI v-if="isEnabled('exotel')" ref="exotel" />
  <Dialog
    v-model="show"
    :options="{
      title: __('Make Call'),
      actions: [
        {
          label: __('Call using {0}', [callMedium]),
          variant: 'solid',
          onClick: makeCallUsing,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="mobileNumber"
          type="text"
          :label="__('Mobile Number')"
        />
        <FormControl
          v-model="callMedium"
          type="select"
          :label="__('Calling Medium')"
          :options="['Twilio', 'Exotel']"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            v-model="isDefaultMedium"
            type="checkbox"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __('You can change the default calling medium from the settings')
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { defaultCallingMedium, useTelephony } from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { computed, defineAsyncComponent, nextTick, ref, watch } from 'vue'

// Lazy-loaded: these pull in the full Twilio/Exotel calling SDKs, which most
// sites never enable. Gated by v-if="isEnabled(...)" below so the SDK is only
// fetched for sites that actually have that integration turned on.
const TwilioCallUI = defineAsyncComponent(
  () => import('@/components/Telephony/TwilioCallUI.vue'),
)
const ExotelCallUI = defineAsyncComponent(
  () => import('@/components/Telephony/ExotelCallUI.vue'),
)

const { setMakeCall } = globalStore()
const { isEnabled, isAnyEnabled } = useTelephony()

const twilio = ref(null)
const exotel = ref(null)

const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')

const enabledIntegrations = computed(() =>
  [
    { key: 'twilio', label: 'Twilio', ref: twilio },
    { key: 'exotel', label: 'Exotel', ref: exotel },
  ].filter(({ key }) => isEnabled(key)),
)

function makeCall(number) {
  if (enabledIntegrations.value.length > 1 && !defaultCallingMedium.value) {
    mobileNumber.value = number
    show.value = true
    return
  }

  callMedium.value = enabledIntegrations.value[0]?.label ?? 'Twilio'
  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value
  }

  mobileNumber.value = number
  makeCallUsing()
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium()
  }

  if (callMedium.value === 'Twilio') {
    twilio.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'Exotel') {
    exotel.value.makeOutgoingCall(mobileNumber.value)
  }
  show.value = false
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

watch(
  isAnyEnabled,
  async () => {
    // TwilioCallUI/ExotelCallUI are lazy-loaded (see imports above) and only
    // rendered once their integration is enabled. Preload the chunk here so
    // it's already resolved by the time nextTick() below lets us reach the
    // ref below — otherwise the ref could still be null on first activation
    // while the dynamic import is in flight.
    await Promise.all(
      enabledIntegrations.value.map(({ key }) =>
        key === 'twilio'
          ? import('@/components/Telephony/TwilioCallUI.vue')
          : import('@/components/Telephony/ExotelCallUI.vue'),
      ),
    )

    await nextTick()

    for (const {
      key,
      label,
      ref: integrationRef,
    } of enabledIntegrations.value) {
      integrationRef.value?.setup()
      callMedium.value = label
    }

    if (isAnyEnabled.value) {
      callMedium.value = enabledIntegrations.value[0]?.label ?? 'Twilio'
      setMakeCall(makeCall)
    }
  },
  { immediate: true },
)
</script>
