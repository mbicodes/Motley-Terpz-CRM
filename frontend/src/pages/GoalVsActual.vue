<template>
  <div class="gva-root">
    <div class="gva-top">
      <span class="gva-title">Goal vs Actual — Sales Targets</span>
    </div>
    <div v-if="!ready" class="gva-loading">Loading dashboard…</div>
    <iframe
      ref="frame"
      v-show="ready"
      class="gva-frame"
      :src="DASHBOARD_ROUTE"
      title="Sales Target Dashboard"
      @load="onFrameLoad"
    ></iframe>
  </div>
</template>

<script setup>
// Embeds only the Sales Target Dashboard desk page (Target Detail data).
// Desk chrome (navbar, workspace sidebar, page actions) is stripped inside the
// same-origin iframe so nothing but the dashboard is visible or navigable.
import { ref } from 'vue'

const DASHBOARD_ROUTE = '/app/sales-target-dashboa'
const frame = ref(null)
const ready = ref(false)

function onFrameLoad() {
  try {
    const doc = frame.value?.contentDocument
    if (doc) {
      const style = doc.createElement('style')
      style.textContent = `
        /* Promote the dashboard page container to a fullscreen overlay so it
           covers every piece of desk/theme chrome (navbar, app rail, sidebars),
           regardless of which theme is installed. */
        #page-sales-target-dashboa {
          position: fixed !important;
          inset: 0 !important;
          z-index: 2147483000 !important;
          background: #fff !important;
          overflow: auto !important;
          margin: 0 !important;
          max-width: none !important;
          display: block !important;
        }
        #page-sales-target-dashboa .page-head,
        #page-sales-target-dashboa .page-actions { display: none !important; }
        #page-sales-target-dashboa .layout-main-section-wrapper,
        #page-sales-target-dashboa .layout-main-section {
          margin: 0 !important;
          max-width: 100% !important;
        }
        body { overflow: hidden !important; }
      `
      doc.head.appendChild(style)
    }
  } catch (e) {
    // same-origin, so this should never throw; fail open and just show the frame
  }
  ready.value = true
}
</script>

<style scoped>
.gva-root{display:flex;flex-direction:column;height:100%;background:#f1f5f9;}
.gva-top{display:flex;justify-content:space-between;align-items:center;background:#1e293b;padding:12px 20px;}
.gva-title{font-size:16px;font-weight:800;color:#fff;}
.gva-loading{flex:1;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:14px;}
.gva-frame{flex:1;width:100%;border:none;background:#fff;}
</style>
