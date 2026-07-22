<template>
  <div class="cp-root">
    <div class="cp-top">
      <div>
        <span class="cp-title">Email Campaigns</span>
        <span class="cp-sub">Blast emails to a list of leads, deals, or contacts &mdash; sent from info@motleyterpz.io</span>
      </div>
      <button class="cp-btn cp-btn-primary" @click="startNew">+ New Campaign</button>
    </div>

    <!-- ═══ List of past campaigns ═══ -->
    <div v-if="!composing" class="cp-card">
      <div v-if="loadingList" class="cp-loading"><div class="cp-spin"></div></div>
      <table v-else-if="campaigns.length" class="cp-table">
        <thead>
          <tr>
            <th>Subject</th>
            <th>Type</th>
            <th>Status</th>
            <th class="r">Recipients</th>
            <th>Sent</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in campaigns" :key="c.name" class="cp-row-click" @click="openCampaign(c.name)">
            <td class="cp-strong">{{ c.subject }}</td>
            <td>{{ c.content_type }}</td>
            <td>
              <span class="cp-pill" :class="c.email_sent ? 'cp-pill-sent' : 'cp-pill-draft'">
                {{ c.email_sent ? 'Sent' : 'Draft' }}
              </span>
            </td>
            <td class="r">{{ c.total_recipients || '—' }}</td>
            <td>{{ c.email_sent_at ? fmtDate(c.email_sent_at) : '—' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="cp-empty">No campaigns yet — click "New Campaign" to send your first blast.</div>
    </div>

    <!-- ═══ Composer ═══ -->
    <div v-else class="cp-composer">
      <!-- Step 1: audience -->
      <div class="cp-card">
        <div class="cp-card-head">1. Audience</div>

        <div class="cp-audience-tabs">
          <button
            class="cp-tab"
            :class="{ active: audienceMode === 'build' }"
            @click="audienceMode = 'build'"
          >Build from CRM records</button>
          <button
            class="cp-tab"
            :class="{ active: audienceMode === 'existing' }"
            @click="audienceMode = 'existing'"
          >Use an existing list</button>
        </div>

        <template v-if="audienceMode === 'build'">
          <div class="cp-row">
            <select v-model="searchDoctype" class="cp-select">
              <option value="CRM Lead">Leads</option>
              <option value="CRM Deal">Deals</option>
              <option value="Contact">Contacts</option>
            </select>
            <input
              v-model="searchText"
              class="cp-input"
              placeholder="Search by name or email…"
              @input="debouncedSearch"
            />
          </div>
          <div v-if="searchResults.length" class="cp-results">
            <div v-for="r in searchResults" :key="r.name" class="cp-result-row" @click="addRecipient(r)">
              <span class="cp-strong">{{ r.title }}</span>
              <span class="cp-dim">{{ r.email }}</span>
              <span class="cp-add">+ Add</span>
            </div>
          </div>
          <div class="cp-chips">
            <span v-for="r in picked" :key="r.email" class="cp-chip">
              {{ r.title }} &lt;{{ r.email }}&gt;
              <span class="cp-chip-x" @click="removeRecipient(r)">×</span>
            </span>
          </div>
          <div class="cp-row">
            <input v-model="audienceTitle" class="cp-input" placeholder="Name this audience (e.g. 'Q3 Rosin Buyers')" />
            <button class="cp-btn" :disabled="!picked.length || !audienceTitle || buildingAudience" @click="buildAudience">
              {{ buildingAudience ? 'Saving…' : `Save Audience (${picked.length})` }}
            </button>
          </div>
        </template>

        <template v-else>
          <select v-model="selectedExistingGroup" class="cp-select cp-select-wide">
            <option value="">Select a saved audience…</option>
            <option v-for="g in existingGroups" :key="g.name" :value="g.name">
              {{ g.title }} ({{ g.total_subscribers }})
            </option>
          </select>
        </template>

        <div v-if="selectedGroupInfo" class="cp-audience-confirmed">
          ✓ Audience ready: <b>{{ selectedGroupInfo.total_subscribers }}</b> recipient(s)
        </div>
        <div v-if="audienceError" class="cp-audience-error">✗ {{ audienceError }}</div>
      </div>

      <!-- Step 2: compose -->
      <div class="cp-card">
        <div class="cp-card-head">2. Compose</div>
        <input v-model="subject" class="cp-input cp-input-wide" placeholder="Subject line" />

        <div class="cp-row" style="justify-content: space-between;">
          <div class="cp-audience-tabs">
            <button class="cp-tab" :class="{ active: contentType === 'Rich Text' }" @click="contentType = 'Rich Text'">Rich Text</button>
            <button class="cp-tab" :class="{ active: contentType === 'HTML' }" @click="contentType = 'HTML'">HTML Source</button>
          </div>
          <button class="cp-btn" :disabled="!hasContent" @click="showPreview = true">Preview</button>
        </div>

        <TextEditor
          v-if="contentType === 'Rich Text'"
          ref="textEditorRef"
          editor-class="cp-editor prose-sm max-w-none"
          :content="richContent"
          placeholder="Write your campaign…"
          :editable="true"
          @change="richContent = $event"
        />
        <textarea
          v-else
          v-model="htmlContent"
          class="cp-html-source"
          placeholder="Paste your custom HTML email here…"
        />
      </div>

      <!-- Step 3: test + send -->
      <div class="cp-card">
        <div class="cp-card-head">3. Test &amp; Send</div>
        <div class="cp-row">
          <input v-model="testEmail" class="cp-input" placeholder="your@email.com" />
          <button class="cp-btn" :disabled="!canDraft || sendingTest" @click="doSendTest">
            {{ sendingTest ? 'Sending…' : 'Send Test' }}
          </button>
        </div>
        <div v-if="testSentMsg" class="cp-audience-confirmed">{{ testSentMsg }}</div>

        <div class="cp-row cp-row-end">
          <button class="cp-btn" @click="composing = false">Cancel</button>
          <button class="cp-btn cp-btn-danger" :disabled="!canSend || sending" @click="doSend">
            {{ sending ? 'Sending…' : `Send to ${selectedGroupInfo?.total_subscribers || 0} recipients` }}
          </button>
        </div>
        <div v-if="!canSend && !sending" class="cp-audience-hint">
          {{ !subject ? 'Add a subject line.' : !hasContent ? 'Add campaign content.' : 'Build or select an audience above first.' }}
        </div>
        <div v-if="sendError" class="cp-audience-error">✗ {{ sendError }}</div>
      </div>
    </div>

    <div v-if="showPreview" class="cp-preview-overlay" @click.self="showPreview = false">
      <div class="cp-preview-panel">
        <div class="cp-preview-head">
          <span>{{ subject || '(no subject)' }}</span>
          <button class="cp-btn" @click="showPreview = false">Close</button>
        </div>
        <iframe class="cp-preview-frame" :srcdoc="previewHtml" sandbox=""></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call, TextEditor } from 'frappe-ui'
import { pendingCampaignAudience } from '@/composables/campaignPrefill'

const composing = ref(false)
const loadingList = ref(true)
const campaigns = ref([])

const audienceMode = ref('build')
const searchDoctype = ref('CRM Lead')
const searchText = ref('')
const searchResults = ref([])
const picked = ref([])
const audienceTitle = ref('')
const buildingAudience = ref(false)
const audience = ref(null)
const audienceError = ref('')
const sendError = ref('')

const existingGroups = ref([])
const selectedExistingGroup = ref('')

const subject = ref('')
const contentType = ref('Rich Text')
const richContent = ref('')
const htmlContent = ref('')

const testEmail = ref('')
const sendingTest = ref(false)
const testSentMsg = ref('')
const sending = ref(false)
const showPreview = ref(false)

const previewHtml = computed(() =>
  contentType.value === 'HTML' ? htmlContent.value : richContent.value,
)

let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(runSearch, 300)
}
async function runSearch() {
  searchResults.value = await call('crm.motley_terpz.campaigns.search_recipients', {
    doctype: searchDoctype.value,
    txt: searchText.value,
  })
}

function addRecipient(r) {
  if (!picked.value.find((p) => p.email === r.email)) {
    picked.value.push({ ...r, doctype: searchDoctype.value })
  }
}
function removeRecipient(r) {
  picked.value = picked.value.filter((p) => p.email !== r.email)
}

async function buildAudience() {
  buildingAudience.value = true
  audienceError.value = ''
  try {
    audience.value = await call('crm.motley_terpz.campaigns.build_audience', {
      title: audienceTitle.value,
      recipients: picked.value.map((p) => ({ name: p.name, doctype: p.doctype, email: p.email })),
    })
  } catch (e) {
    audience.value = null
    audienceError.value = e.messages?.[0] || e.message || 'Failed to save audience'
  } finally {
    buildingAudience.value = false
  }
}

async function loadExistingGroups() {
  existingGroups.value = await call('crm.motley_terpz.campaigns.get_audiences')
}

const resolvedAudienceName = computed(() =>
  audienceMode.value === 'build' ? audience.value?.name : selectedExistingGroup.value,
)

const hasAudience = computed(() =>
  audienceMode.value === 'build' ? !!audience.value : !!selectedExistingGroup.value,
)
const selectedGroupInfo = computed(() => {
  if (audienceMode.value === 'build') return audience.value
  return existingGroups.value.find((g) => g.name === selectedExistingGroup.value) || null
})
const hasContent = computed(() =>
  contentType.value === 'HTML' ? !!htmlContent.value : !!richContent.value,
)
const canDraft = computed(() => hasAudience.value && !!subject.value && hasContent.value)
const canSend = computed(() => canDraft.value)

const draftName = ref(null)
async function ensureDraft() {
  const content = contentType.value === 'HTML' ? htmlContent.value : richContent.value
  const r = await call('crm.motley_terpz.campaigns.create_campaign', {
    subject: subject.value,
    content,
    content_type: contentType.value,
    email_group: resolvedAudienceName.value,
    newsletter: draftName.value,
  })
  draftName.value = r.name
  return r.name
}

async function openCampaign(name) {
  const [c] = await Promise.all([
    call('crm.motley_terpz.campaigns.get_campaign', { newsletter: name }),
    loadExistingGroups(),
  ])
  draftName.value = c.name
  subject.value = c.subject
  contentType.value = c.content_type === 'Markdown' ? 'Rich Text' : c.content_type
  if (c.content_type === 'HTML') {
    htmlContent.value = c.content
  } else {
    richContent.value = c.content
  }
  audienceMode.value = 'existing'
  selectedExistingGroup.value = c.email_group
  audienceError.value = ''
  sendError.value = ''
  composing.value = true
}

async function doSendTest() {
  sendingTest.value = true
  testSentMsg.value = ''
  try {
    const name = await ensureDraft()
    await call('crm.motley_terpz.campaigns.send_test', { newsletter: name, email: testEmail.value })
    testSentMsg.value = `✓ Test sent to ${testEmail.value}`
  } catch (e) {
    testSentMsg.value = `✗ ${e.messages?.[0] || 'Failed to send test'}`
  } finally {
    sendingTest.value = false
  }
}

async function doSend() {
  if (!confirm(`Send this campaign to ${selectedGroupInfo.value?.total_subscribers || 'all'} recipients? This can't be undone.`)) {
    return
  }
  sending.value = true
  sendError.value = ''
  try {
    const name = await ensureDraft()
    await call('crm.motley_terpz.campaigns.send_campaign', { newsletter: name })
    composing.value = false
    await loadCampaigns()
  } catch (e) {
    sendError.value = e.messages?.[0] || e.message || 'Failed to send campaign'
  } finally {
    sending.value = false
  }
}

function startNew() {
  composing.value = true
  audienceMode.value = 'build'
  picked.value = []
  audience.value = null
  audienceTitle.value = ''
  subject.value = ''
  richContent.value = ''
  htmlContent.value = ''
  testEmail.value = ''
  testSentMsg.value = ''
  draftName.value = null
  loadExistingGroups()
}

async function loadCampaigns() {
  loadingList.value = true
  try {
    campaigns.value = await call('crm.motley_terpz.campaigns.list_campaigns')
  } finally {
    loadingList.value = false
  }
}

function fmtDate(v) {
  return new Date(v).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

async function consumePendingAudience() {
  const pending = pendingCampaignAudience.value
  if (!pending) return
  pendingCampaignAudience.value = null

  startNew()
  searchDoctype.value = pending.doctype
  const rows = await call('crm.motley_terpz.campaigns.get_recipients_by_names', {
    doctype: pending.doctype,
    names: pending.names,
  })
  picked.value = rows.map((r) => ({ ...r, doctype: pending.doctype }))
  if (rows.length < pending.names.length) {
    audienceError.value = `${pending.names.length - rows.length} of ${pending.names.length} selected record(s) had no email address and were skipped.`
  }
}

onMounted(async () => {
  await loadCampaigns()
  await consumePendingAudience()
})
</script>

<style scoped>
.cp-root{padding:16px;background:#f1f5f9;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;gap:14px;}
.cp-top{display:flex;justify-content:space-between;align-items:center;background:#1e293b;border-radius:12px;padding:14px 20px;flex-wrap:wrap;gap:10px;}
.cp-title{font-size:16px;font-weight:800;color:#fff;margin-right:10px;}
.cp-sub{font-size:12px;color:#94a3b8;}
.cp-btn{background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:7px 14px;font-weight:600;font-size:13px;cursor:pointer;color:#1e293b;}
.cp-btn:disabled{opacity:.5;cursor:not-allowed;}
.cp-btn-primary{background:#6366f1;color:#fff;border:none;}
.cp-btn-danger{background:#dc2626;color:#fff;border:none;}

.cp-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:10px;}
.cp-card-head{font-size:13px;font-weight:800;color:#334155;}

.cp-table{width:100%;border-collapse:collapse;font-size:13px;}
.cp-table th{text-align:left;padding:10px 12px;font-size:10px;text-transform:uppercase;color:#64748b;font-weight:700;background:#f8fafc;}
.cp-table th.r,.cp-table td.r{text-align:right;}
.cp-table td{padding:10px 12px;border-bottom:1px solid #f1f5f9;}
.cp-row-click{cursor:pointer;}
.cp-row-click:hover{background:#f8fafc;}
.cp-strong{font-weight:700;}
.cp-dim{color:#94a3b8;font-size:12px;}
.cp-empty{padding:30px;text-align:center;color:#94a3b8;}
.cp-loading{display:flex;justify-content:center;padding:40px;}
.cp-spin{width:26px;height:26px;border:3px solid #e2e8f0;border-top-color:#1e293b;border-radius:50%;animation:cps .8s linear infinite;}
@keyframes cps{to{transform:rotate(360deg);}}

.cp-pill{font-size:11px;font-weight:700;padding:2px 10px;border-radius:999px;}
.cp-pill-sent{background:#dcfce7;color:#166534;}
.cp-pill-draft{background:#f1f5f9;color:#64748b;}

.cp-composer{display:flex;flex-direction:column;gap:14px;}
.cp-audience-tabs{display:flex;gap:6px;}
.cp-tab{border:1px solid #e2e8f0;background:#fff;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;color:#64748b;}
.cp-tab.active{background:#1e293b;color:#fff;border-color:#1e293b;}

.cp-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.cp-row-end{justify-content:flex-end;}
.cp-select,.cp-input{border:1px solid #e2e8f0;border-radius:6px;padding:7px 10px;font-size:13px;}
.cp-select-wide,.cp-input-wide{width:100%;}
.cp-input{flex:1;min-width:180px;}

.cp-results{border:1px solid #e2e8f0;border-radius:8px;max-height:200px;overflow-y:auto;}
.cp-result-row{display:flex;gap:10px;align-items:center;padding:8px 12px;cursor:pointer;border-bottom:1px solid #f1f5f9;}
.cp-result-row:hover{background:#f8fafc;}
.cp-result-row:last-child{border-bottom:none;}
.cp-add{margin-left:auto;color:#6366f1;font-size:12px;font-weight:700;}

.cp-chips{display:flex;flex-wrap:wrap;gap:6px;}
.cp-chip{background:#eef2ff;color:#3730a3;border-radius:999px;padding:4px 10px;font-size:12px;display:flex;align-items:center;gap:6px;}
.cp-chip-x{cursor:pointer;font-weight:700;}

.cp-audience-confirmed{background:#f0fdf4;color:#166534;border-radius:6px;padding:8px 12px;font-size:12.5px;font-weight:600;}
.cp-audience-error{background:#fef2f2;color:#991b1b;border-radius:6px;padding:8px 12px;font-size:12.5px;font-weight:600;margin-top:8px;}
.cp-audience-hint{color:#6b7280;font-size:12px;margin-top:6px;text-align:right;}

.cp-preview-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);display:flex;align-items:center;justify-content:center;z-index:1000;}
.cp-preview-panel{background:#fff;border-radius:10px;width:min(720px,92vw);height:min(80vh,860px);display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 50px -20px rgba(0,0,0,.4);}
.cp-preview-head{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px solid #e5e7eb;font-weight:600;font-size:13px;}
.cp-preview-frame{flex:1;border:0;width:100%;background:#fff;}

.cp-editor{border:1px solid #e2e8f0;border-radius:8px;padding:12px;min-height:220px;}
.cp-html-source{border:1px solid #e2e8f0;border-radius:8px;padding:12px;min-height:220px;font-family:monospace;font-size:12.5px;width:100%;resize:vertical;}
</style>
