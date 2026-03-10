<template>
  <div class="setup-container">
    <div class="setup-card">
      <div class="setup-header">
        <span class="brand">SOCIALSWARM</span>
        <span class="header-label">SETUP WIZARD</span>
      </div>

      <!-- Progress indicator -->
      <div class="progress-bar">
        <div
          v-for="s in 4"
          :key="s"
          class="progress-step"
          :class="{ active: s === step, completed: s < step }"
        >
          <span class="step-dot">{{ s < step ? '\u2713' : s }}</span>
          <span class="step-label">{{ stepLabels[s - 1] }}</span>
        </div>
      </div>

      <!-- Step 1: LLM Configuration -->
      <div v-if="step === 1" class="step-content">
        <h2 class="step-title">LLM Configuration</h2>
        <p class="step-desc">
          Configure your LLM provider. SocialSwarm works with any OpenAI SDK-compatible API.
        </p>

        <div class="field-group">
          <label class="field-label">API Key <span class="required">*</span></label>
          <div class="password-wrapper">
            <input
              :type="showLlmKey ? 'text' : 'password'"
              v-model="llm.apiKey"
              placeholder="sk-..."
              class="field-input"
            />
            <button type="button" class="toggle-btn" @click="showLlmKey = !showLlmKey">
              {{ showLlmKey ? 'HIDE' : 'SHOW' }}
            </button>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">Base URL</label>
          <input
            type="text"
            v-model="llm.baseUrl"
            placeholder="e.g., https://api.groq.com/openai/v1"
            class="field-input"
          />
        </div>

        <div class="field-group">
          <label class="field-label">Model Name</label>
          <input
            type="text"
            v-model="llm.modelName"
            placeholder="gpt-4o-mini"
            class="field-input"
          />
        </div>

        <div class="test-row">
          <button class="test-btn" @click="testLlm" :disabled="testingLlm || !llm.apiKey">
            {{ testingLlm ? 'Testing...' : 'Test Connection' }}
          </button>
          <span v-if="llmTestResult === 'success'" class="test-success">\u2713 Connected</span>
          <span v-if="llmTestResult === 'error'" class="test-error">{{ llmTestError }}</span>
        </div>

        <div class="nav-row">
          <div></div>
          <button class="next-btn" @click="step = 2" :disabled="!llm.apiKey">Next &rarr;</button>
        </div>
      </div>

      <!-- Step 2: Zep Configuration -->
      <div v-if="step === 2" class="step-content">
        <h2 class="step-title">Zep Configuration</h2>
        <p class="step-desc">
          Configure Zep Cloud for knowledge graph storage. Get a free API key at
          <a href="https://app.getzep.com" target="_blank" class="link">app.getzep.com</a>
        </p>

        <div class="field-group">
          <label class="field-label">API Key <span class="required">*</span></label>
          <div class="password-wrapper">
            <input
              :type="showZepKey ? 'text' : 'password'"
              v-model="zep.apiKey"
              placeholder="z_..."
              class="field-input"
            />
            <button type="button" class="toggle-btn" @click="showZepKey = !showZepKey">
              {{ showZepKey ? 'HIDE' : 'SHOW' }}
            </button>
          </div>
        </div>

        <div class="test-row">
          <button class="test-btn" @click="testZep" :disabled="testingZep || !zep.apiKey">
            {{ testingZep ? 'Testing...' : 'Test Connection' }}
          </button>
          <span v-if="zepTestResult === 'success'" class="test-success">\u2713 Connected</span>
          <span v-if="zepTestResult === 'error'" class="test-error">{{ zepTestError }}</span>
        </div>

        <div class="nav-row">
          <button class="back-btn" @click="step = 1">&larr; Back</button>
          <button class="next-btn" @click="step = 3" :disabled="!zep.apiKey">Next &rarr;</button>
        </div>
      </div>

      <!-- Step 3: Optional Settings -->
      <div v-if="step === 3" class="step-content">
        <h2 class="step-title">Optional Settings</h2>
        <p class="step-desc">
          Configure optional settings (you can change these later in Settings)
        </p>

        <div class="section-label">Boost LLM</div>

        <div class="field-group">
          <label class="field-label">API Key</label>
          <div class="password-wrapper">
            <input
              :type="showBoostKey ? 'text' : 'password'"
              v-model="boost.apiKey"
              placeholder="Optional"
              class="field-input"
            />
            <button type="button" class="toggle-btn" @click="showBoostKey = !showBoostKey">
              {{ showBoostKey ? 'HIDE' : 'SHOW' }}
            </button>
          </div>
        </div>

        <div class="field-group">
          <label class="field-label">Base URL</label>
          <input
            type="text"
            v-model="boost.baseUrl"
            placeholder="Optional"
            class="field-input"
          />
        </div>

        <div class="field-group">
          <label class="field-label">Model Name</label>
          <input
            type="text"
            v-model="boost.modelName"
            placeholder="Optional"
            class="field-input"
          />
        </div>

        <div class="section-label">Simulation Defaults</div>

        <div class="field-group">
          <label class="field-label">Max Rounds</label>
          <input
            type="number"
            v-model.number="defaults.maxRounds"
            min="1"
            max="100"
            class="field-input field-narrow"
          />
        </div>

        <div class="section-label">Report Agent</div>

        <div class="field-group">
          <label class="field-label">Temperature</label>
          <div class="range-row">
            <input
              type="range"
              v-model.number="defaults.temperature"
              min="0"
              max="1"
              step="0.1"
              class="range-input"
            />
            <span class="range-value">{{ defaults.temperature.toFixed(1) }}</span>
          </div>
        </div>

        <div class="nav-row">
          <button class="back-btn" @click="step = 2">&larr; Back</button>
          <div class="nav-right-group">
            <button class="skip-link" @click="step = 4">Skip</button>
            <button class="next-btn" @click="step = 4">Next &rarr;</button>
          </div>
        </div>
      </div>

      <!-- Step 4: Confirmation -->
      <div v-if="step === 4" class="step-content">
        <h2 class="step-title">Confirmation</h2>
        <p class="step-desc">Review your configuration before completing setup.</p>

        <div class="summary-section">
          <div class="summary-label">LLM Provider</div>
          <div class="summary-row">
            <span class="summary-key">API Key</span>
            <span class="summary-val">{{ maskKey(llm.apiKey) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-key">Base URL</span>
            <span class="summary-val">{{ llm.baseUrl }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-key">Model</span>
            <span class="summary-val">{{ llm.modelName }}</span>
          </div>
        </div>

        <div class="summary-section">
          <div class="summary-label">Zep Cloud</div>
          <div class="summary-row">
            <span class="summary-key">API Key</span>
            <span class="summary-val">{{ maskKey(zep.apiKey) }}</span>
          </div>
        </div>

        <div v-if="boost.apiKey || boost.baseUrl || boost.modelName" class="summary-section">
          <div class="summary-label">Boost LLM</div>
          <div v-if="boost.apiKey" class="summary-row">
            <span class="summary-key">API Key</span>
            <span class="summary-val">{{ maskKey(boost.apiKey) }}</span>
          </div>
          <div v-if="boost.baseUrl" class="summary-row">
            <span class="summary-key">Base URL</span>
            <span class="summary-val">{{ boost.baseUrl }}</span>
          </div>
          <div v-if="boost.modelName" class="summary-row">
            <span class="summary-key">Model</span>
            <span class="summary-val">{{ boost.modelName }}</span>
          </div>
        </div>

        <div class="summary-section">
          <div class="summary-label">Defaults</div>
          <div class="summary-row">
            <span class="summary-key">Max Rounds</span>
            <span class="summary-val">{{ defaults.maxRounds }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-key">Temperature</span>
            <span class="summary-val">{{ defaults.temperature.toFixed(1) }}</span>
          </div>
        </div>

        <div v-if="saveError" class="save-error">{{ saveError }}</div>

        <div class="nav-row">
          <button class="back-btn" @click="step = 3">&larr; Back</button>
          <button class="complete-btn" @click="completeSetup" :disabled="saving">
            {{ saving ? 'Saving...' : 'Complete Setup' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { validateSettings, saveSettings } from '../api/settings'
import { setConfigured } from '../store/configStatus'

const router = useRouter()

const step = ref(1)
const stepLabels = ['LLM', 'Zep', 'Optional', 'Confirm']

// --- Step 1: LLM ---
const llm = reactive({
  apiKey: '',
  baseUrl: 'https://api.openai.com/v1',
  modelName: 'gpt-4o-mini',
})
const showLlmKey = ref(false)
const testingLlm = ref(false)
const llmTestResult = ref('')
const llmTestError = ref('')

async function testLlm() {
  testingLlm.value = true
  llmTestResult.value = ''
  llmTestError.value = ''
  try {
    const res = await validateSettings('llm', {
      apiKey: llm.apiKey,
      baseUrl: llm.baseUrl,
      modelName: llm.modelName,
    })
    if (res.data?.success || res.success) {
      llmTestResult.value = 'success'
    } else {
      llmTestResult.value = 'error'
      llmTestError.value = res.data?.message || res.message || 'Connection failed'
    }
  } catch (e) {
    llmTestResult.value = 'error'
    llmTestError.value = e.response?.data?.message || e.message || 'Connection failed'
  } finally {
    testingLlm.value = false
  }
}

// --- Step 2: Zep ---
const zep = reactive({ apiKey: '' })
const showZepKey = ref(false)
const testingZep = ref(false)
const zepTestResult = ref('')
const zepTestError = ref('')

async function testZep() {
  testingZep.value = true
  zepTestResult.value = ''
  zepTestError.value = ''
  try {
    const res = await validateSettings('zep', { apiKey: zep.apiKey })
    if (res.data?.success || res.success) {
      zepTestResult.value = 'success'
    } else {
      zepTestResult.value = 'error'
      zepTestError.value = res.data?.message || res.message || 'Connection failed'
    }
  } catch (e) {
    zepTestResult.value = 'error'
    zepTestError.value = e.response?.data?.message || e.message || 'Connection failed'
  } finally {
    testingZep.value = false
  }
}

// --- Step 3: Optional ---
const boost = reactive({ apiKey: '', baseUrl: '', modelName: '' })
const showBoostKey = ref(false)
const defaults = reactive({ maxRounds: 10, temperature: 0.5 })

// --- Step 4: Confirmation ---
const saving = ref(false)
const saveError = ref('')

function maskKey(key) {
  if (!key) return '\u2014'
  if (key.length <= 8) return '\u2022'.repeat(key.length)
  return key.slice(0, 4) + '\u2022'.repeat(key.length - 8) + key.slice(-4)
}

async function completeSetup() {
  saving.value = true
  saveError.value = ''
  try {
    const payload = {
      llm: {
        apiKey: llm.apiKey,
        baseUrl: llm.baseUrl,
        modelName: llm.modelName,
      },
      zep: {
        apiKey: zep.apiKey,
      },
      boost: {
        apiKey: boost.apiKey || undefined,
        baseUrl: boost.baseUrl || undefined,
        modelName: boost.modelName || undefined,
      },
      defaults: {
        maxRounds: defaults.maxRounds,
        temperature: defaults.temperature,
      },
    }
    const res = await saveSettings(payload)
    if (res.data?.success !== false && res.success !== false) {
      setConfigured(true)
      router.push('/')
    } else {
      saveError.value = res.data?.message || res.message || 'Failed to save settings'
    }
  } catch (e) {
    saveError.value = e.response?.data?.message || e.message || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.setup-container {
  min-height: 100vh;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  font-family: 'JetBrains Mono', monospace;
  color: #000;
}

.setup-card {
  width: 100%;
  max-width: 640px;
  border: 1px solid #e5e5e5;
  background: #fff;
}

.setup-header {
  background: #000;
  color: #fff;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.header-label {
  color: #999;
  font-weight: 500;
}

/* Progress bar */
.progress-bar {
  display: flex;
  border-bottom: 1px solid #e5e5e5;
}

.progress-step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 0.75rem;
  color: #999;
  border-right: 1px solid #e5e5e5;
  transition: all 0.2s;
}

.progress-step:last-child {
  border-right: none;
}

.progress-step.active {
  background: #fafafa;
  color: #000;
  font-weight: 700;
}

.progress-step.completed {
  color: #22c55e;
}

.step-dot {
  width: 22px;
  height: 22px;
  border: 1px solid currentColor;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.progress-step.active .step-dot {
  background: #000;
  color: #fff;
  border-color: #000;
}

.progress-step.completed .step-dot {
  background: #22c55e;
  color: #fff;
  border-color: #22c55e;
}

.step-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Step content */
.step-content {
  padding: 32px 28px;
}

.step-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.step-desc {
  font-size: 0.82rem;
  color: #666;
  line-height: 1.6;
  margin: 0 0 28px;
}

.link {
  color: #FF5722;
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  text-decoration: underline;
}

/* Fields */
.field-group {
  margin-bottom: 18px;
}

.field-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
  color: #333;
}

.required {
  color: #FF5722;
}

.field-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  background: #fafafa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #000;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: #000;
  background: #fff;
}

.field-input::placeholder {
  color: #bbb;
}

.field-narrow {
  max-width: 160px;
}

.password-wrapper {
  position: relative;
  display: flex;
}

.password-wrapper .field-input {
  flex: 1;
  padding-right: 64px;
}

.toggle-btn {
  position: absolute;
  right: 1px;
  top: 1px;
  bottom: 1px;
  background: #f0f0f0;
  border: none;
  border-left: 1px solid #ddd;
  padding: 0 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #666;
  cursor: pointer;
  transition: background 0.2s;
}

.toggle-btn:hover {
  background: #e5e5e5;
}

/* Section labels for step 3 */
.section-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
  margin: 24px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #eee;
}

.section-label:first-of-type {
  margin-top: 0;
}

/* Range */
.range-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.range-input {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: #ddd;
  outline: none;
  cursor: pointer;
}

.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: #000;
  cursor: pointer;
}

.range-input::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #000;
  border: none;
  cursor: pointer;
}

.range-value {
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 28px;
  text-align: right;
}

/* Test connection */
.test-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.test-btn {
  background: #fff;
  border: 1px solid #000;
  padding: 8px 18px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.test-btn:hover:not(:disabled) {
  background: #000;
  color: #fff;
}

.test-btn:disabled {
  border-color: #ddd;
  color: #bbb;
  cursor: not-allowed;
}

.test-success {
  color: #22c55e;
  font-size: 0.8rem;
  font-weight: 600;
}

.test-error {
  color: #ef4444;
  font-size: 0.8rem;
  font-weight: 600;
}

/* Navigation */
.nav-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.nav-right-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 10px 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: #000;
  color: #000;
}

.next-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 10px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

.next-btn:hover:not(:disabled) {
  background: #FF5722;
}

.next-btn:disabled {
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
}

.skip-link {
  background: none;
  border: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #999;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  padding: 0;
}

.skip-link:hover {
  color: #666;
}

.complete-btn {
  background: #000;
  color: #fff;
  border: none;
  padding: 12px 28px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

.complete-btn:hover:not(:disabled) {
  background: #22c55e;
}

.complete-btn:disabled {
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
}

/* Summary */
.summary-section {
  margin-bottom: 20px;
  border: 1px solid #eee;
  padding: 16px;
}

.summary-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #999;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 0.8rem;
}

.summary-key {
  color: #666;
}

.summary-val {
  font-weight: 600;
  color: #000;
  word-break: break-all;
  text-align: right;
  max-width: 60%;
}

.save-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #ef4444;
  padding: 10px 14px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 16px;
}
</style>
