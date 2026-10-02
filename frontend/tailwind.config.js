import frappeUIPreset from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  // Explicit list instead of a bare `/!(text|bg)-/` regex: that pattern matched
  // every text-*/bg-* utility in the whole theme (colors, gradients, background
  // properties, sizes, etc.) crossed with hover/active variants, ballooning the
  // generated CSS to 38k+ rules for a handful of actually-used classes.
  safelist: [
    '!text-sm',
    '!text-ink-gray-2',
    '!text-ink-gray-4',
    '!text-ink-gray-5',
    '!text-ink-gray-7',
    '!text-ink-gray-9',
    'hover:!text-ink-gray-9',
    '!bg-surface-gray-1',
    '!bg-surface-gray-2',
    '!bg-surface-gray-3',
    '!bg-surface-gray-4',
    '!bg-surface-gray-5',
    '!bg-surface-modal',
    '!bg-surface-cards',
    'hover:!bg-surface-gray-1',
    'hover:!bg-surface-gray-2',
    'hover:!bg-surface-gray-3',
    'group-hover:!bg-surface-gray-3',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
