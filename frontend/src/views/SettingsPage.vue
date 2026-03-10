<template>
  <div class="settings-page">
    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header">
        <router-link to="/" class="back-link">&larr; Back to Home</router-link>
        <h1 class="settings-title">Settings</h1>
        <p class="settings-subtitle">View and modify application configuration</p>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="loading-state">Loading settings...</div>

      <!-- Toast message -->
      <Transition name="toast">
        <div v-if="toast.visible" class="toast" :class="toast.type">
          {{ toast.message }}
        </div>
      </Transition>

      <div v-if="!loading" class="sections">
        <!-- Section 1: LLM Configuration -->
        <div class="section" :class="{ expanded: sections.llm }">
          <div class="section-header" @click="toggleSection('llm')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.llm ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">LLM Configuration</span>
            </div>
            <span class="section-badge">Required</span>
          </div>
          <div v-show="sections.llm" class="section-body">
            <div class="field-group">
              <label class="field-label">API Key</label>
              <div class="password-field">
                <input
                  :type="showKeys.llm ? 'text' : 'password'"
                  v-model="form.llm_api_key"
                  class="field-input"
                  placeholder="Enter LLM API key"
                  @input="markChanged('llm_api_key')"
                />
                <button class="toggle-vis" @click="showKeys.llm = !showKeys.llm" type="button">
                  {{ showKeys.llm ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
            <div class="field-group">
              <label class="field-label">Base URL</label>
              <input
                type="text"
                v-model="form.llm_base_url"
                class="field-input"
                placeholder="https://api.openai.com/v1"
              />
            </div>
            <div class="field-group">
              <label class="field-label">Model Name</label>
              <input
                type="text"
                v-model="form.llm_model_name"
                class="field-input"
                placeholder="gpt-4"
              />
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="testAndSave('llm')" :disabled="saving.llm">
                {{ saving.llm ? 'Testing...' : 'Test & Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Section 2: Zep Configuration -->
        <div class="section" :class="{ expanded: sections.zep }">
          <div class="section-header" @click="toggleSection('zep')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.zep ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">Zep Configuration</span>
            </div>
            <span class="section-badge">Required</span>
          </div>
          <div v-show="sections.zep" class="section-body">
            <div class="field-group">
              <label class="field-label">API Key</label>
              <div class="password-field">
                <input
                  :type="showKeys.zep ? 'text' : 'password'"
                  v-model="form.zep_api_key"
                  class="field-input"
                  placeholder="Enter Zep API key"
                  @input="markChanged('zep_api_key')"
                />
                <button class="toggle-vis" @click="showKeys.zep = !showKeys.zep" type="button">
                  {{ showKeys.zep ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="testAndSave('zep')" :disabled="saving.zep">
                {{ saving.zep ? 'Testing...' : 'Test & Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Section 3: Boost LLM (Optional) -->
        <div class="section" :class="{ expanded: sections.boost }">
          <div class="section-header" @click="toggleSection('boost')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.boost ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">Boost LLM</span>
            </div>
            <span class="section-badge optional">Optional</span>
          </div>
          <div v-show="sections.boost" class="section-body">
            <div class="field-group">
              <label class="field-label">API Key</label>
              <div class="password-field">
                <input
                  :type="showKeys.boost ? 'text' : 'password'"
                  v-model="form.boost_api_key"
                  class="field-input"
                  placeholder="Enter Boost LLM API key (optional)"
                  @input="markChanged('boost_api_key')"
                />
                <button class="toggle-vis" @click="showKeys.boost = !showKeys.boost" type="button">
                  {{ showKeys.boost ? 'Hide' : 'Show' }}
                </button>
              </div>
            </div>
            <div class="field-group">
              <label class="field-label">Base URL</label>
              <input
                type="text"
                v-model="form.boost_base_url"
                class="field-input"
                placeholder="https://api.openai.com/v1"
              />
            </div>
            <div class="field-group">
              <label class="field-label">Model Name</label>
              <input
                type="text"
                v-model="form.boost_model_name"
                class="field-input"
                placeholder="gpt-4"
              />
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="saveSection('boost')" :disabled="saving.boost">
                {{ saving.boost ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Section 4: Simulation Defaults -->
        <div class="section" :class="{ expanded: sections.simulation }">
          <div class="section-header" @click="toggleSection('simulation')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.simulation ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">Simulation Defaults</span>
            </div>
          </div>
          <div v-show="sections.simulation" class="section-body">
            <div class="field-group">
              <label class="field-label">Max Rounds</label>
              <input
                type="number"
                v-model.number="form.max_rounds"
                class="field-input"
                min="1"
                max="100"
              />
            </div>
            <div class="field-group">
              <label class="field-label">Chunk Size</label>
              <input
                type="number"
                v-model.number="form.chunk_size"
                class="field-input"
                min="100"
                max="2000"
              />
            </div>
            <div class="field-group">
              <label class="field-label">Chunk Overlap</label>
              <input
                type="number"
                v-model.number="form.chunk_overlap"
                class="field-input"
                min="0"
                max="500"
              />
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="saveSection('simulation')" :disabled="saving.simulation">
                {{ saving.simulation ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Section 5: Report Agent -->
        <div class="section" :class="{ expanded: sections.report }">
          <div class="section-header" @click="toggleSection('report')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.report ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">Report Agent</span>
            </div>
          </div>
          <div v-show="sections.report" class="section-body">
            <div class="field-group">
              <label class="field-label">Max Tool Calls</label>
              <input
                type="number"
                v-model.number="form.max_tool_calls"
                class="field-input"
                min="1"
                max="20"
              />
            </div>
            <div class="field-group">
              <label class="field-label">Max Reflection Rounds</label>
              <input
                type="number"
                v-model.number="form.max_reflection_rounds"
                class="field-input"
                min="1"
                max="10"
              />
            </div>
            <div class="field-group">
              <label class="field-label">
                Temperature
                <span class="field-value-display">{{ form.temperature }}</span>
              </label>
              <input
                type="range"
                v-model.number="form.temperature"
                class="field-range"
                min="0"
                max="1"
                step="0.1"
              />
              <div class="range-labels">
                <span>0</span>
                <span>0.5</span>
                <span>1</span>
              </div>
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="saveSection('report')" :disabled="saving.report">
                {{ saving.report ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Section 6: Application -->
        <div class="section" :class="{ expanded: sections.app }">
          <div class="section-header" @click="toggleSection('app')">
            <div class="section-header-left">
              <span class="chevron">{{ sections.app ? '&#9660;' : '&#9654;' }}</span>
              <span class="section-title-text">Application</span>
            </div>
          </div>
          <div v-show="sections.app" class="section-body">
            <div class="field-group">
              <label class="field-label">Language</label>
              <select v-model="form.language" class="field-input field-select">
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </div>
            <div class="section-actions">
              <button class="btn btn-primary" @click="saveAppSection" :disabled="saving.app">
                {{ saving.app ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getSettings, saveSettings, validateSettings } from '../api/settings'
import { setLocale, getLocale } from '../i18n'

// Loading state
const loading = ref(true)

// Section expand/collapse state
const sections = reactive({
  llm: true,
  zep: false,
  boost: false,
  simulation: false,
  report: false,
  app: false
})

// Saving state per section
const saving = reactive({
  llm: false,
  zep: false,
  boost: false,
  simulation: false,
  report: false,
  app: false
})

// Show/hide password fields
const showKeys = reactive({
  llm: false,
  zep: false,
  boost: false
})

// Track which API key fields have been changed by the user
const changedKeys = reactive({
  llm_api_key: false,
  zep_api_key: false,
  boost_api_key: false
})

// Form data
const form = reactive({
  llm_api_key: '',
  llm_base_url: '',
  llm_model_name: '',
  zep_api_key: '',
  boost_api_key: '',
  boost_base_url: '',
  boost_model_name: '',
  max_rounds: 10,
  chunk_size: 500,
  chunk_overlap: 100,
  max_tool_calls: 5,
  max_reflection_rounds: 3,
  temperature: 0.7,
  language: 'en'
})

// Toast notification
const toast = reactive({
  visible: false,
  message: '',
  type: 'success',
  timer: null
})

function showToast(message, type = 'success') {
  if (toast.timer) clearTimeout(toast.timer)
  toast.message = message
  toast.type = type
  toast.visible = true
  toast.timer = setTimeout(() => {
    toast.visible = false
  }, 3000)
}

function toggleSection(key) {
  sections[key] = !sections[key]
}

function markChanged(field) {
  changedKeys[field] = true
}

// Build payload for a section, omitting unchanged masked API keys
function buildPayload(group) {
  const payloads = {
    llm: () => {
      const data = {
        llm_base_url: form.llm_base_url,
        llm_model_name: form.llm_model_name
      }
      if (changedKeys.llm_api_key) {
        data.llm_api_key = form.llm_api_key
      }
      return data
    },
    zep: () => {
      const data = {}
      if (changedKeys.zep_api_key) {
        data.zep_api_key = form.zep_api_key
      }
      return data
    },
    boost: () => {
      const data = {
        boost_base_url: form.boost_base_url,
        boost_model_name: form.boost_model_name
      }
      if (changedKeys.boost_api_key) {
        data.boost_api_key = form.boost_api_key
      }
      return data
    },
    simulation: () => ({
      max_rounds: form.max_rounds,
      chunk_size: form.chunk_size,
      chunk_overlap: form.chunk_overlap
    }),
    report: () => ({
      max_tool_calls: form.max_tool_calls,
      max_reflection_rounds: form.max_reflection_rounds,
      temperature: form.temperature
    }),
    app: () => ({
      language: form.language
    })
  }
  return payloads[group]()
}

async function testAndSave(group) {
  saving[group] = true
  try {
    const payload = buildPayload(group)
    // Validate first
    const validateRes = await validateSettings(group, payload)
    if (validateRes.data && validateRes.data.valid === false) {
      showToast(validateRes.data.message || 'Validation failed', 'error')
      return
    }
    // Then save
    await saveSettings({ group, ...payload })
    showToast(`${group.toUpperCase()} configuration saved successfully`)
  } catch (err) {
    const msg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Save failed'
    showToast(msg, 'error')
  } finally {
    saving[group] = false
  }
}

async function saveSection(group) {
  saving[group] = true
  try {
    const payload = buildPayload(group)
    await saveSettings({ group, ...payload })
    showToast(`${group.charAt(0).toUpperCase() + group.slice(1)} settings saved successfully`)
  } catch (err) {
    const msg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Save failed'
    showToast(msg, 'error')
  } finally {
    saving[group] = false
  }
}

async function saveAppSection() {
  saving.app = true
  try {
    setLocale(form.language)
    const payload = buildPayload('app')
    await saveSettings({ group: 'app', ...payload })
    showToast('Application settings saved successfully')
  } catch (err) {
    const msg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Save failed'
    showToast(msg, 'error')
  } finally {
    saving.app = false
  }
}

onMounted(async () => {
  try {
    const res = await getSettings()
    const data = res.data || {}
    // Populate form with loaded values, keeping defaults for missing fields
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        form[key] = data[key]
      }
    })
    // Set language from current locale if not provided by backend
    if (!data.language) {
      form.language = getLocale()
    }
  } catch (err) {
    showToast('Failed to load settings', 'error')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #FFFFFF;
  font-family: 'JetBrains Mono', monospace;
  color: #000000;
  padding: 40px 20px;
}

.settings-container {
  max-width: 720px;
  margin: 0 auto;
}

/* Header */
.settings-header {
  margin-bottom: 40px;
}

.back-link {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #666666;
  text-decoration: none;
  display: inline-block;
  margin-bottom: 20px;
  transition: color 0.2s;
}

.back-link:hover {
  color: #FF4500;
}

.settings-title {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  letter-spacing: -1px;
}

.settings-subtitle {
  font-size: 0.85rem;
  color: #666666;
  margin: 0;
}

/* Loading */
.loading-state {
  text-align: center;
  padding: 60px 0;
  font-size: 0.9rem;
  color: #999999;
}

/* Toast */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  z-index: 1000;
  border: 1px solid;
  max-width: 400px;
}

.toast.success {
  background: #f0fff0;
  border-color: #2e7d32;
  color: #2e7d32;
}

.toast.error {
  background: #fff0f0;
  border-color: #c62828;
  color: #c62828;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Sections */
.sections {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section {
  border: 1px solid #E5E5E5;
  background: #FFFFFF;
}

.section.expanded {
  border-color: #000000;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.section-header:hover {
  background: #FAFAFA;
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chevron {
  font-size: 0.7rem;
  color: #999999;
  width: 14px;
  display: inline-block;
  text-align: center;
}

.section-title-text {
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.section-badge {
  font-size: 0.65rem;
  padding: 2px 8px;
  background: #000000;
  color: #FFFFFF;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.section-badge.optional {
  background: transparent;
  color: #999999;
  border: 1px solid #E5E5E5;
}

/* Section body */
.section-body {
  padding: 0 20px 20px 20px;
  border-top: 1px solid #F0F0F0;
}

/* Field groups */
.field-group {
  margin-top: 16px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #666666;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-value-display {
  font-weight: 700;
  color: #FF4500;
  font-size: 0.85rem;
  text-transform: none;
}

.field-input {
  width: 100%;
  padding: 10px 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  border: 1px solid #E5E5E5;
  background: #FAFAFA;
  color: #000000;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: #000000;
  background: #FFFFFF;
}

.field-select {
  cursor: pointer;
  appearance: auto;
}

/* Password field with show/hide toggle */
.password-field {
  display: flex;
  gap: 0;
}

.password-field .field-input {
  flex: 1;
  border-right: none;
}

.toggle-vis {
  padding: 10px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  background: #FAFAFA;
  border: 1px solid #E5E5E5;
  color: #666666;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.toggle-vis:hover {
  background: #F0F0F0;
  color: #000000;
}

/* Range slider */
.field-range {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: #E5E5E5;
  outline: none;
  margin: 8px 0 4px 0;
  cursor: pointer;
}

.field-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #000000;
  cursor: pointer;
  border: 2px solid #FFFFFF;
  box-shadow: 0 0 0 1px #000000;
}

.field-range::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #000000;
  cursor: pointer;
  border: 2px solid #FFFFFF;
  box-shadow: 0 0 0 1px #000000;
  border-radius: 0;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #999999;
}

/* Section actions */
.section-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* Buttons */
.btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 10px 24px;
  border: 1px solid;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

.btn-primary {
  background: #000000;
  color: #FFFFFF;
  border-color: #000000;
}

.btn-primary:hover:not(:disabled) {
  background: #FF4500;
  border-color: #FF4500;
}

.btn-primary:disabled {
  background: #E5E5E5;
  border-color: #E5E5E5;
  color: #999999;
  cursor: not-allowed;
}
</style>
