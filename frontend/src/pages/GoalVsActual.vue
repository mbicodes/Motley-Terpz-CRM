<template>
  <div class="gva-root">
    <div class="gva-top">
      <span class="gva-title">Goal vs Actual — Sales Targets</span>
      <a href="/app/sales-target-dashboa" target="_blank" class="gva-link">Open full dashboard ↗</a>
    </div>
    <iframe class="gva-frame" src="/app/sales-target-dashboa" title="Sales Target Dashboard"></iframe>
  </div>
</template>

<script setup>
// Reuses the existing (already dynamic) Sales Target dashboard, which reads
// live targets from ERPNext Target Detail records.
</script>

<style scoped>
.gva-root{display:flex;flex-direction:column;height:100%;background:#f1f5f9;}
.gva-top{display:flex;justify-content:space-between;align-items:center;background:#1e293b;padding:12px 20px;}
.gva-title{font-size:16px;font-weight:800;color:#fff;}
.gva-link{color:#93c5fd;font-size:13px;text-decoration:none;font-weight:600;}
.gva-link:hover{text-decoration:underline;}
.gva-frame{flex:1;width:100%;border:none;background:#fff;}
</style>
