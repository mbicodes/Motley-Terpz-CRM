<template>
  <div class="cseg-root">
    <div class="cseg-topbar">
      <div>
        <span class="cseg-title">Customer Segmentation</span>
        <span class="cseg-subtitle">Which sales person is handling which customer &middot; read-only</span>
      </div>
      <input v-model="search" class="cseg-search" placeholder="Search customers…" />
    </div>

    <div v-if="loading" class="cseg-loading"><div class="cseg-spinner"></div></div>

    <template v-else>
      <div class="cseg-summary">
        <div
          v-for="s in sections"
          :key="s.key"
          class="cseg-chip"
          :class="[`cseg-chip-${s.key}`, { 'cseg-chip-active': activeSection === s.key }]"
          @click="activeSection = activeSection === s.key ? '' : s.key"
        >
          {{ s.label }} <span class="cseg-chip-count">{{ s.count }}</span>
        </div>
        <div class="cseg-total">{{ total }} customers</div>
      </div>

      <div class="cseg-sections">
        <div
          v-for="s in visibleSections"
          :key="s.key"
          class="cseg-section"
          :class="`cseg-section-${s.key}`"
        >
          <div class="cseg-section-head">
            <div class="cseg-avatar" :class="`cseg-avatar-${s.key}`">{{ s.label.charAt(0) }}</div>
            <div>
              <div class="cseg-section-name">{{ s.label }}</div>
              <div class="cseg-section-sub">{{ s.full_name }}</div>
            </div>
            <div class="cseg-section-count">{{ filteredCustomers(s).length }}</div>
          </div>

          <div class="cseg-table-head">
            <span>Customer</span>
            <span>Group</span>
            <span>Territory</span>
            <span>License Type</span>
          </div>

          <div class="cseg-list">
            <div v-for="c in filteredCustomers(s)" :key="c.name" class="cseg-row">
              <span class="cseg-cname">{{ c.customer_name }}</span>
              <span class="cseg-dim">{{ c.customer_group || '—' }}</span>
              <span class="cseg-dim">{{ c.territory || '—' }}</span>
              <span class="cseg-dim">{{ c.license_type || '—' }}</span>
            </div>
            <div v-if="!filteredCustomers(s).length" class="cseg-empty">
              {{ search ? 'No customers match this search' : 'No customers in this section' }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'

const loading = ref(true)
const sections = ref([])
const total = ref(0)
const search = ref('')
const activeSection = ref('')

const visibleSections = computed(() =>
  activeSection.value
    ? sections.value.filter((s) => s.key === activeSection.value)
    : sections.value,
)

function filteredCustomers(section) {
  if (!search.value) return section.customers
  const q = search.value.toLowerCase()
  return section.customers.filter(
    (c) =>
      (c.customer_name || '').toLowerCase().includes(q) ||
      (c.territory || '').toLowerCase().includes(q) ||
      (c.customer_group || '').toLowerCase().includes(q),
  )
}

async function load() {
  loading.value = true
  try {
    const res = await call('crm.motley_terpz.customer_segmentation.get_customer_segmentation')
    sections.value = res?.sections || []
    total.value = res?.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.cseg-root {
  padding: 16px 20px 40px;
  overflow-y: auto;
  height: 100%;
}

.cseg-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}

.cseg-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-right: 10px;
}

.cseg-subtitle {
  font-size: 12px;
  color: #94a3b8;
}

.cseg-search {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  min-width: 240px;
  outline: none;
}

.cseg-search:focus {
  border-color: #a5b4fc;
}

.cseg-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.cseg-chip {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  user-select: none;
}

.cseg-chip-count {
  font-weight: 700;
  margin-left: 4px;
}

.cseg-chip-active {
  border-color: #7c3aed;
  background: #7c3aed;
  color: #fff;
}

.cseg-total {
  margin-left: auto;
  font-size: 12px;
  color: #94a3b8;
}

.cseg-sections {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.cseg-section {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.cseg-section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  background: #f8fafc;
}

.cseg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #fff;
  font-size: 15px;
}

.cseg-avatar-nikki       { background: #7c3aed; }
.cseg-avatar-douglas     { background: #0891b2; }
.cseg-avatar-dominic     { background: #059669; }
.cseg-avatar-unidentified { background: #94a3b8; }

.cseg-section-name {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.cseg-section-sub {
  font-size: 11px;
  color: #94a3b8;
}

.cseg-section-count {
  margin-left: auto;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 4px 12px;
}

.cseg-table-head,
.cseg-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.4fr;
  gap: 10px;
  padding: 8px 16px;
  align-items: center;
}

.cseg-table-head {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  border-bottom: 1px solid #f1f5f9;
}

.cseg-row {
  font-size: 13px;
  border-bottom: 1px solid #f8fafc;
}

.cseg-row:last-child {
  border-bottom: none;
}

.cseg-row:hover {
  background: #fafafa;
}

.cseg-cname {
  font-weight: 600;
  color: #334155;
}

.cseg-dim {
  color: #64748b;
  font-size: 12px;
}

.cseg-list {
  max-height: 420px;
  overflow-y: auto;
}

.cseg-empty {
  padding: 24px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}

.cseg-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.cseg-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #e2e8f0;
  border-top-color: #7c3aed;
  border-radius: 50%;
  animation: cseg-spin 0.8s linear infinite;
}

@keyframes cseg-spin {
  to { transform: rotate(360deg); }
}
</style>
