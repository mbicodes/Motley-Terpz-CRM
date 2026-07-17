<template>
  <div class="md-root">
    <div class="md-top">
      <div>
        <span class="md-title">My Day</span>
        <span class="md-sub">Tasks, meetings and momentum — all in one place</span>
      </div>
      <div v-if="reps.length" class="md-reps">
        <button
          v-for="r in reps"
          :key="r.name"
          class="md-rep-btn"
          :class="{ active: activeUser === r.name }"
          @click="switchTo(r.name)"
        >
          {{ r.full_name || r.name }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="md-loading"><div class="md-spin"></div></div>
    <template v-else>
      <div class="md-tiles">
        <div class="md-tile" :class="{ warn: d.overdue_count }">
          <span>Overdue</span><b>{{ d.overdue_count }}</b>
        </div>
        <div class="md-tile"><span>Due Today</span><b>{{ d.due_today_count }}</b></div>
        <div class="md-tile"><span>Open Tasks</span><b>{{ d.tasks.length }}</b></div>
        <div class="md-tile"><span>Meetings This Week</span><b>{{ d.meetings_count }}</b></div>
      </div>

      <div class="md-grid">
        <div class="md-card">
          <div class="md-card-head">My Tasks</div>
          <div v-if="!d.tasks.length" class="md-empty">Nothing open — you're clear.</div>
          <div
            v-for="t in d.tasks"
            :key="t.name"
            class="md-task"
            :class="{ overdue: t.is_overdue }"
            @click="go(t.route)"
          >
            <div class="md-task-main">
              <span class="md-task-title">{{ t.title }}</span>
              <span v-if="t.reference_title" class="md-task-ref">{{ t.reference_title }}</span>
            </div>
            <div class="md-task-side">
              <span v-if="t.priority" class="md-pill" :class="'p-' + t.priority.toLowerCase()">{{ t.priority }}</span>
              <span v-if="t.due_date" class="md-due" :class="{ overdue: t.is_overdue }">{{ fmtDate(t.due_date) }}</span>
            </div>
          </div>
        </div>

        <div class="md-col">
          <div class="md-card">
            <div class="md-card-head">This Week's Meetings</div>
            <div v-if="!d.meetings.length" class="md-empty">Nothing scheduled.</div>
            <div v-for="m in d.meetings" :key="m.name" class="md-meeting" @click="go(m.route)">
              <span class="md-meeting-title">{{ m.subject }}</span>
              <span class="md-meeting-time">{{ fmtDateTime(m.starts_on) }}</span>
              <span v-if="m.reference_title" class="md-task-ref">{{ m.reference_title }}</span>
            </div>
          </div>

          <div class="md-card">
            <div class="md-card-head">Recent Moves</div>
            <div v-if="!d.recent.length" class="md-empty">No recent activity.</div>
            <div v-for="(r, i) in d.recent" :key="i" class="md-recent" @click="go(r.route)">
              <span class="md-recent-icon">{{ recentIcon(r.type) }}</span>
              <div class="md-recent-body">
                <span class="md-recent-label">{{ r.label || r.type }}</span>
                <span v-if="r.reference_title" class="md-task-ref">{{ r.reference_title }}</span>
              </div>
              <span class="md-recent-time">{{ timeAgo(r.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'

const router = useRouter()
const d = ref({ tasks: [], meetings: [], recent: [], overdue_count: 0, due_today_count: 0, meetings_count: 0 })
const reps = ref([])
const activeUser = ref('')
const loading = ref(true)

function fmtDate(v) {
  if (!v) return ''
  return new Date(v).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function fmtDateTime(v) {
  if (!v) return ''
  return new Date(v).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function timeAgo(v) {
  if (!v) return ''
  const secs = (Date.now() - new Date(v).getTime()) / 1000
  if (secs < 60) return 'just now'
  if (secs < 3600) return Math.floor(secs / 60) + 'm ago'
  if (secs < 86400) return Math.floor(secs / 3600) + 'h ago'
  return Math.floor(secs / 86400) + 'd ago'
}
function recentIcon(type) {
  return { note: '📝', task: '✅', call: '📞' }[type] || '•'
}
function go(route) {
  if (route) router.push(route)
}

async function loadReps() {
  reps.value = await call('crm.motley_terpz.my_day.get_reps')
}

async function load() {
  loading.value = true
  try {
    d.value = await call('crm.motley_terpz.my_day.get_my_day', activeUser.value ? { user: activeUser.value } : {})
    activeUser.value = d.value.user
  } finally {
    loading.value = false
  }
}

function switchTo(user) {
  activeUser.value = user
  load()
}

onMounted(async () => {
  await loadReps()
  await load()
})
</script>

<style scoped>
.md-root{padding:16px;background:#f1f5f9;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;gap:14px;}
.md-top{display:flex;justify-content:space-between;align-items:center;background:#1e293b;border-radius:12px;padding:14px 20px;flex-wrap:wrap;gap:10px;}
.md-title{font-size:16px;font-weight:800;color:#fff;margin-right:10px;}
.md-sub{font-size:12px;color:#94a3b8;}
.md-reps{display:flex;gap:6px;flex-wrap:wrap;}
.md-rep-btn{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#fff;border-radius:999px;padding:5px 14px;font-size:12px;font-weight:600;cursor:pointer;}
.md-rep-btn.active{background:#6366f1;border-color:#6366f1;}

.md-tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
@media(max-width:680px){.md-tiles{grid-template-columns:1fr 1fr;}}
.md-tile{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;}
.md-tile.warn b{color:#dc2626;}
.md-tile span{font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;}
.md-tile b{font-size:22px;}

.md-grid{display:grid;grid-template-columns:1.3fr 1fr;gap:14px;align-items:start;}
@media(max-width:900px){.md-grid{grid-template-columns:1fr;}}
.md-col{display:flex;flex-direction:column;gap:14px;}

.md-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:4px 0 8px;}
.md-card-head{font-size:12px;font-weight:800;text-transform:uppercase;color:#64748b;padding:12px 16px 8px;}
.md-empty{padding:20px 16px;color:#94a3b8;font-size:13px;}

.md-task{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 16px;border-top:1px solid #f1f5f9;cursor:pointer;}
.md-task:hover{background:#f8fafc;}
.md-task.overdue{background:#fef2f2;}
.md-task-main{display:flex;flex-direction:column;gap:2px;min-width:0;}
.md-task-title{font-size:13px;font-weight:600;color:#1e293b;}
.md-task-ref{font-size:11px;color:#94a3b8;}
.md-task-side{display:flex;align-items:center;gap:8px;flex-shrink:0;}
.md-pill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;}
.md-pill.p-high{background:#fee2e2;color:#991b1b;}
.md-pill.p-medium{background:#fef3c7;color:#92400e;}
.md-pill.p-low{background:#e0e7ff;color:#3730a3;}
.md-due{font-size:11px;color:#64748b;}
.md-due.overdue{color:#dc2626;font-weight:700;}

.md-meeting{display:flex;flex-direction:column;gap:2px;padding:10px 16px;border-top:1px solid #f1f5f9;cursor:pointer;}
.md-meeting:hover{background:#f8fafc;}
.md-meeting-title{font-size:13px;font-weight:600;color:#1e293b;}
.md-meeting-time{font-size:11px;color:#6366f1;font-weight:600;}

.md-recent{display:flex;align-items:flex-start;gap:10px;padding:9px 16px;border-top:1px solid #f1f5f9;cursor:pointer;}
.md-recent:hover{background:#f8fafc;}
.md-recent-icon{font-size:14px;line-height:1.4;}
.md-recent-body{display:flex;flex-direction:column;gap:1px;flex:1;min-width:0;}
.md-recent-label{font-size:12.5px;color:#1e293b;font-weight:500;}
.md-recent-time{font-size:10.5px;color:#94a3b8;white-space:nowrap;}

.md-loading{display:flex;justify-content:center;padding:60px;}
.md-spin{width:30px;height:30px;border:3px solid #e2e8f0;border-top-color:#1e293b;border-radius:50%;animation:mds .8s linear infinite;}
@keyframes mds{to{transform:rotate(360deg);}}
</style>
