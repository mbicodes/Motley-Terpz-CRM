import { ref } from 'vue'

// Set by a bulk "Add to Email Campaign" action on a list view; read once and
// cleared by the Campaigns page so a bulk selection doesn't have to be
// re-searched one name at a time in the audience builder.
export const pendingCampaignAudience = ref(null)

export function queueCampaignAudience(doctype, names) {
  pendingCampaignAudience.value = { doctype, names }
}
