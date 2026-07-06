<template>
  <div class="calc-root">
    <div class="calc-top"><span class="calc-title">Co-Pack Cost &amp; Quote Calculator</span></div>

    <div class="calc-grid">
      <!-- Inputs -->
      <div class="calc-card">
        <h3>Job inputs</h3>
        <label>Client raw material cost ($)</label>
        <input type="number" v-model.number="f.raw_material_cost" min="0" />

        <label>Run quantity (units)</label>
        <input type="number" v-model.number="f.run_qty" min="1" />

        <label>Labor hours</label>
        <input type="number" v-model.number="f.labor_hours" min="0" />

        <div class="calc-row3">
          <div><label>Labor $/hr</label><input type="number" v-model.number="f.labor_rate_per_hour" /></div>
          <div><label>Overhead %</label><input type="number" v-model.number="f.overhead_pct" /></div>
          <div><label>Margin %</label><input type="number" v-model.number="f.margin_pct" /></div>
        </div>

        <div class="calc-pkg-head">
          <span>Packaging components</span>
          <button class="calc-mini" @click="addPkg">+ Add</button>
        </div>
        <div v-for="(p, i) in f.packaging" :key="i" class="calc-pkg-row">
          <input class="calc-pkg-item" placeholder="Item code" v-model="p.item_code" />
          <input class="calc-pkg-qty" type="number" placeholder="Qty / unit" v-model.number="p.qty_per_unit" />
          <button class="calc-mini calc-del" @click="f.packaging.splice(i,1)">&times;</button>
        </div>

        <button class="calc-go" :disabled="busy" @click="run">{{ busy ? 'Calculating…' : 'Calculate' }}</button>
      </div>

      <!-- Results -->
      <div class="calc-card">
        <h3>Result</h3>
        <div v-if="!r" class="calc-empty">Enter the job details and press Calculate.</div>
        <div v-else class="calc-result">
          <div class="calc-tiles">
            <div class="calc-tile"><span>Total cost</span><b>{{ money(r.total_cost) }}</b></div>
            <div class="calc-tile"><span>Cost / unit</span><b>{{ money(r.cost_per_unit) }}</b></div>
            <div class="calc-tile hl"><span>Suggested quote / unit</span><b>{{ money(r.suggested_price_per_unit) }}</b></div>
            <div class="calc-tile hl"><span>Suggested quote total</span><b>{{ money(r.suggested_quote_total) }}</b></div>
          </div>
          <table class="calc-bd">
            <tr><td>Raw material</td><td>{{ money(r.breakdown.raw_material_cost) }}</td></tr>
            <tr><td>Labor</td><td>{{ money(r.breakdown.labor_cost) }}</td></tr>
            <tr><td>Packaging</td><td>{{ money(r.breakdown.packaging_total) }}</td></tr>
            <tr><td>Overhead</td><td>{{ money(r.breakdown.overhead_cost) }}</td></tr>
            <tr class="calc-bd-tot"><td>Total</td><td>{{ money(r.total_cost) }}</td></tr>
          </table>
          <div v-if="r.breakdown.packaging_lines.length" class="calc-pkg-detail">
            <div class="calc-sub">Packaging detail</div>
            <table class="calc-bd">
              <tr v-for="(l,i) in r.breakdown.packaging_lines" :key="i">
                <td>{{ l.item_name || l.item_code || '—' }}</td>
                <td>{{ money(l.unit_cost) }} × {{ l.qty_per_unit }} × {{ f.run_qty }}</td>
                <td>{{ money(l.line_total) }}</td>
              </tr>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { call } from 'frappe-ui'

const f = reactive({
  raw_material_cost: 0, run_qty: 100, labor_hours: 0,
  labor_rate_per_hour: null, overhead_pct: null, margin_pct: null,
  packaging: [{ item_code: '', qty_per_unit: 1 }],
})
const r = ref(null)
const busy = ref(false)

function addPkg() { f.packaging.push({ item_code: '', qty_per_unit: 1 }) }
function money(v) { return '$ ' + parseFloat(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

async function run() {
  busy.value = true
  try {
    r.value = await call('cannabis_management.api.copack_calculator.calculate', {
      payload: JSON.stringify({
        raw_material_cost: f.raw_material_cost, run_qty: f.run_qty, labor_hours: f.labor_hours,
        labor_rate_per_hour: f.labor_rate_per_hour, overhead_pct: f.overhead_pct, margin_pct: f.margin_pct,
        packaging: f.packaging.filter(p => p.item_code),
      }),
    })
  } finally { busy.value = false }
}

onMounted(async () => {
  try {
    const s = await call('cannabis_management.api.copack_calculator.get_settings')
    f.labor_rate_per_hour = s.labor_rate_per_hour
    f.overhead_pct = s.overhead_pct
    f.margin_pct = s.default_margin_pct
  } catch (e) { /* defaults stay null; backend fills them */ }
})
</script>

<style scoped>
.calc-root { padding:16px; background:#f1f5f9; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; display:flex; flex-direction:column; gap:14px; }
.calc-top { background:#14532d; border-radius:12px; padding:14px 20px; }
.calc-title { font-size:16px; font-weight:800; color:#fff; }
.calc-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
@media (max-width:780px){ .calc-grid{ grid-template-columns:1fr; } }
.calc-card { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px 20px; display:flex; flex-direction:column; gap:8px; }
.calc-card h3 { margin:0 0 6px; font-size:14px; font-weight:750; }
.calc-card label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#64748b; margin-top:4px; }
.calc-card input { border:1px solid #cbd5e1; border-radius:7px; padding:7px 9px; font-size:14px; }
.calc-row3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
.calc-pkg-head { display:flex; justify-content:space-between; align-items:center; margin-top:10px; font-size:11px; font-weight:700; text-transform:uppercase; color:#64748b; }
.calc-pkg-row { display:flex; gap:6px; }
.calc-pkg-item { flex:2; } .calc-pkg-qty { flex:1; }
.calc-mini { border:1px solid #cbd5e1; background:#f8fafc; border-radius:6px; padding:4px 9px; cursor:pointer; font-size:12px; font-weight:700; }
.calc-del { color:#dc2626; }
.calc-go { margin-top:14px; background:#16a34a; color:#fff; border:none; border-radius:8px; padding:10px; font-weight:800; cursor:pointer; }
.calc-go:disabled { opacity:.5; }
.calc-empty { color:#94a3b8; font-size:13px; padding:24px 0; }
.calc-tiles { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }
.calc-tile { background:#f8fafc; border:1px solid #e2e8f0; border-radius:9px; padding:10px 12px; display:flex; flex-direction:column; gap:2px; }
.calc-tile span { font-size:10px; font-weight:700; text-transform:uppercase; color:#64748b; }
.calc-tile b { font-size:17px; }
.calc-tile.hl { background:#dcfce7; border-color:#bbf7d0; } .calc-tile.hl b { color:#15803d; }
.calc-bd { width:100%; border-collapse:collapse; font-size:13px; }
.calc-bd td { padding:6px 4px; border-bottom:1px solid #f1f5f9; }
.calc-bd td:last-child { text-align:right; font-weight:600; }
.calc-bd-tot td { font-weight:800; border-top:2px solid #e2e8f0; }
.calc-sub { font-size:11px; font-weight:700; text-transform:uppercase; color:#64748b; margin:12px 0 4px; }
</style>
