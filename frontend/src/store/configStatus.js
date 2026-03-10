/**
 * Tracks whether the app has required configuration (API keys).
 * Used by the router navigation guard to redirect to /setup when needed.
 */
import { reactive } from 'vue'

const state = reactive({
  configured: null,  // null = not yet checked, true/false after check
  missing: [],
  isLoaded: false,
})

export async function fetchConfigStatus() {
  try {
    const res = await fetch(
      (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001') + '/api/settings/status'
    )
    const json = await res.json()
    if (json.success) {
      state.configured = json.data.configured
      state.missing = json.data.missing
    } else {
      // Backend error — assume configured to not block the app
      state.configured = true
      state.missing = []
    }
  } catch (e) {
    // Backend unreachable — assume configured to not block
    console.warn('Could not reach backend to check config status:', e)
    state.configured = true
    state.missing = []
  }
  state.isLoaded = true
}

export function getConfigStatus() {
  return state
}

export function setConfigured(value) {
  state.configured = value
  state.missing = value ? [] : state.missing
}

export default state
