<template>
  <div class="calc-root">
    <div class="calc-top"><span class="calc-title">Tolling / Processing Cost Calculator</span></div>

    <div class="calc-grid">
      <div class="calc-card">
        <h3>Batch inputs</h3>
        <label>Input material (lbs)</label>
        <input type="number" v-model.number="f.input_lbs" min="0" />

        <label>Expected yield %<span v-if="avgYield" class="calc-hint"> · historical avg {{ avgYield }}%</span></label>
        <input type="number" v-model.number="f.yield_pct" min="0" max="100" />

        <label>Tolling rate ($/lb)</label>
        <input type="number" v-model.number="f.rate_per_lb" min="0" />

        <label>Rate is charged per</label>
        <select v-model="f.rate_basis">
          <option value="input">Input lb (material in)</option>
          <option value="output">Output lb (product out)</option>
        </select>

        <div class="calc-row3">
          <div><label>Labor hrs</label><input type="number" v-model.number="f.labor_hours" /></div>
          <div><label>Labor $/hr</label><input type="number" v-model.number="f.labor_rate_per_hour" /></div>
          <div><label>Overhead %</label><input type="number" v-model.number="f.overhead_pct" /></div>
        </div>
        <label>Target margin % (optional)</label>
        <input type="number" v-model.number="f.margin_pct" />

        <button class="calc-go" :disabled="busy" @click="run">{{ busy ? 'Calculating…' : 'Calculate' }}</button>
      </div>

      <div class="calc-card">
        <h3>Result</h3>
        <div v-if="!r" class="calc-empty">Enter the batch details and press Calculate.</div>
        <div v-else class="calc-result">
          <div class="calc-tiles">
            <div class="calc-tile"><span>Output weight</span><b>{{ num(r.output_lbs) }} lb</b></div>
            <div class="calc-tile"><span>Total tolling cost</span><b>{{ money(r.total_cost) }}</b></div>
            <div class="calc-tile"><span>Cost / output lb</span><b>{{ money(r.cost_per_output_lb) }}</b></div>
            <div class="calc-tile hl"><span>Suggested $/output lb</span><b>{{ money(r.suggested_price_per_output_lb) }}</b></div>
          </div>
          <table class="calc-bd">
            <tr><td>Tolling fee ({{ r.breakdown.rate_basis }} basis)</td><td>{{ money(r.breakdown.tolling_fee) }}</td></tr>
            <tr><td>Labor</td><td>{{ money(r.breakdown.labor_cost) }}</td></tr>
            <tr><td>Overhead</td><td>{{ money(r.breakdown.overhead_cost) }}</td></tr>
            <tr class="calc-bd-tot"><td>Total per batch</td><td>{{ money(r.total_cost) }}</td></tr>
          </table>
          <div v-if="f.margin_pct" class="calc-note">Suggested quote for the batch: <b>{{ money(r.suggested_quote_total) }}</b></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const f = reactive({
  input_lbs: 0, yield_pct: 0, rate_per_lb: 0, rate_basis: 'input',
  labor_hours: 0, labor_rate_per_hour: 25, overhead_pct: 0, margin_pct: null,
})
const r = ref(null)
const busy = ref(false)
const avgYield = ref(null)

function money(v) { return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function num(v) { return parseFloat(v || 0).toLocaleString('en-US', { maximumFractionDigits: 3 }) }

async function run() {
  busy.value = true
  try {
    r.value = await call('cannabis_management.api.tolling_calculator.calculate', { payload: JSON.stringify(f) })
  } finally { busy.value = false }
}

onMounted(async () => {
  try {
    const y = await call('cannabis_management.api.tolling_calculator.get_avg_yield')
    if (y) { avgYield.value = y; if (!f.yield_pct) f.yield_pct = y }
  } catch (e) { /* optional */ }
})
</script>

<style scoped>
.calc-root { padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; display:flex; flex-direction:column; gap:14px; }
.calc-top { background:#134e4a; border-radius:12px; padding:14px 20px; }
.calc-title { font-size:16px; font-weight:800; color:#fff; }
.calc-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
@media (max-width:780px){ .calc-grid{ grid-template-columns:1fr; } }
.calc-card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px 20px; display:flex; flex-direction:column; gap:8px; }
.calc-card h3 { margin:0 0 6px; font-size:14px; font-weight:750; }
.calc-card label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#64748b; margin-top:4px; }
.calc-hint { color:#0d9488; text-transform:none; letter-spacing:0; font-weight:600; }
.calc-card input, .calc-card select { border:1px solid #cbd5e1; border-radius:7px; padding:7px 9px; font-size:14px; }
.calc-row3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
.calc-go { margin-top:14px; background:#0d9488; color:#fff; border:none; border-radius:8px; padding:10px; font-weight:800; cursor:pointer; }
.calc-go:disabled { opacity:.5; }
.calc-empty { color:#94a3b8; font-size:13px; padding:24px 0; }
.calc-tiles { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }
.calc-tile { background:#f8fafc; border:1px solid #e2e8f0; border-radius:9px; padding:10px 12px; display:flex; flex-direction:column; gap:2px; }
.calc-tile span { font-size:10px; font-weight:700; text-transform:uppercase; color:#64748b; }
.calc-tile b { font-size:17px; }
.calc-tile.hl { background:#ccfbf1; border-color:#99f6e4; } .calc-tile.hl b { color:#0f766e; }
.calc-bd { width:100%; border-collapse:collapse; font-size:13px; }
.calc-bd td { padding:6px 4px; border-bottom:1px solid #f1f5f9; }
.calc-bd td:last-child { text-align:right; font-weight:600; }
.calc-bd-tot td { font-weight:800; border-top:2px solid #e2e8f0; }
.calc-note { margin-top:10px; font-size:13px; color:#334155; }
</style>
