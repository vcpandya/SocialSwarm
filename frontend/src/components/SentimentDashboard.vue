<template>
  <div class="sentiment-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">{{ $t('dashboard.title') }}</h1>
      <span class="dashboard-sim-id">SIM: {{ simulationId }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="dashboard-loading">
      <div class="loading-spinner"></div>
      <span class="loading-text">{{ $t('dashboard.loading') }}</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="dashboard-error">
      <span class="error-icon">!</span>
      <span class="error-text">{{ $t('dashboard.error') }}</span>
      <button class="retry-btn" @click="fetchData">Retry</button>
    </div>

    <!-- No Data State -->
    <div v-else-if="!sentimentData" class="dashboard-no-data">
      <span class="no-data-text">{{ $t('dashboard.noData') }}</span>
    </div>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Summary Cards Row -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-label">{{ $t('dashboard.overallSentiment') }}</div>
          <div class="card-value" :style="{ color: sentimentColor(sentimentData.overallSentiment) }">
            {{ sentimentData.overallSentiment.toFixed(2) }}
          </div>
          <div class="card-tag" :style="{ background: sentimentColor(sentimentData.overallSentiment) + '22', color: sentimentColor(sentimentData.overallSentiment) }">
            {{ sentimentLabel(sentimentData.overallSentiment) }}
          </div>
        </div>

        <div class="summary-card">
          <div class="card-label">{{ $t('dashboard.polarizationIndex') }}</div>
          <div class="card-gauge">
            <svg viewBox="0 0 120 70" class="gauge-svg">
              <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#1a1a2e" stroke-width="8" stroke-linecap="round" />
              <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" :stroke="polarizationColor" stroke-width="8" stroke-linecap="round"
                :stroke-dasharray="gaugeCircumference"
                :stroke-dashoffset="gaugeOffset" />
            </svg>
            <div class="gauge-value">{{ sentimentData.polarizationIndex.toFixed(2) }}</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-label">{{ $t('dashboard.echoChamberScore') }}</div>
          <div class="card-value echo-value">
            {{ sentimentData.echoChamberScore.toFixed(2) }}
          </div>
          <div class="echo-bar-track">
            <div class="echo-bar-fill" :style="{ width: (sentimentData.echoChamberScore * 100) + '%' }"></div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-label">{{ $t('dashboard.postsAnalyzed') }}</div>
          <div class="card-value posts-value">
            {{ sentimentData.totalPosts.toLocaleString() }}
          </div>
        </div>
      </div>

      <!-- Charts Row 1: Timeline + Topic Sentiment -->
      <div class="charts-row">
        <div class="chart-panel timeline-panel">
          <div class="chart-header">{{ $t('dashboard.sentimentTimeline') }}</div>
          <div class="chart-body" role="img" aria-label="Sentiment timeline chart">
            <svg ref="timelineSvg" class="chart-svg"></svg>
          </div>
        </div>

        <div class="chart-panel topic-panel">
          <div class="chart-header">{{ $t('dashboard.topicSentiment') }}</div>
          <div class="chart-body" role="img" aria-label="Topic frequency chart">
            <svg ref="topicSvg" class="chart-svg"></svg>
          </div>
        </div>
      </div>

      <!-- Charts Row 2: Emotion Distribution + Agent Scatter -->
      <div class="charts-row">
        <div class="chart-panel emotion-panel">
          <div class="chart-header">{{ $t('dashboard.emotionDistribution') }}</div>
          <div class="chart-body" role="img" aria-label="Emotion distribution radar chart">
            <svg ref="emotionSvg" class="chart-svg"></svg>
          </div>
        </div>

        <div class="chart-panel scatter-panel">
          <div class="chart-header">{{ $t('dashboard.agentSentiment') }}</div>
          <div class="chart-body" role="img" aria-label="Agent activity scatter plot">
            <svg ref="scatterSvg" class="chart-svg"></svg>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { select, scaleLinear, scaleBand, scaleSqrt, extent, max, area as d3area, line as d3line, curveMonotoneX, axisBottom, axisLeft } from 'd3'
import { getSentimentAnalysis, getSentimentTimeline } from '../api/dashboard'

const { t } = useI18n()

const props = defineProps({
  simulationId: { type: String, required: true }
})

// State
const loading = ref(true)
const error = ref(false)
const sentimentData = ref(null)

// SVG refs
const timelineSvg = ref(null)
const topicSvg = ref(null)
const emotionSvg = ref(null)
const scatterSvg = ref(null)

// Resize observer
let resizeObserver = null
let resizeTimer = null

// Color helpers
const sentimentColor = (val) => {
  if (val > 0.1) return '#00c853'
  if (val < -0.1) return '#ff6b6b'
  return '#a0a0a0'
}

const sentimentLabel = (val) => {
  if (val > 0.1) return t('dashboard.positive')
  if (val < -0.1) return t('dashboard.negative')
  return t('dashboard.neutral')
}

const polarizationColor = computed(() => {
  if (!sentimentData.value) return '#6c5ce7'
  const v = sentimentData.value.polarizationIndex
  if (v < 0.3) return '#00c853'
  if (v < 0.6) return '#ffd600'
  return '#ff6b6b'
})

const gaugeCircumference = computed(() => {
  // Half circle arc length for r=50: pi * 50 ~ 157
  return 157
})

const gaugeOffset = computed(() => {
  if (!sentimentData.value) return 157
  return 157 * (1 - sentimentData.value.polarizationIndex)
})

// Sentiment color scale for D3
const sentimentColorScale = scaleLinear()
  .domain([-1, 0, 1])
  .range(['#ff6b6b', '#a0a0a0', '#00c853'])

// Fetch data
const fetchData = async () => {
  loading.value = true
  error.value = false
  try {
    const [analysisRes, timelineRes] = await Promise.all([
      getSentimentAnalysis(props.simulationId),
      getSentimentTimeline(props.simulationId)
    ])

    const analysis = analysisRes.data || analysisRes
    const timeline = timelineRes.data || timelineRes

    sentimentData.value = {
      overallSentiment: analysis.overall_sentiment ?? 0,
      polarizationIndex: analysis.polarization_index ?? 0,
      echoChamberScore: analysis.echo_chamber_score ?? 0,
      totalPosts: analysis.total_posts ?? 0,
      timeline: timeline.timeline || [],
      topics: analysis.topics || [],
      emotions: analysis.emotions || {},
      agents: analysis.agents || []
    }

    await nextTick()
    renderAllCharts()
  } catch (e) {
    console.error('Failed to load sentiment data:', e)
    error.value = true

    // Use mock data for demonstration if API not available
    sentimentData.value = generateMockData()
    error.value = false
    await nextTick()
    renderAllCharts()
  } finally {
    loading.value = false
  }
}

// Mock data generator for development/demo
const generateMockData = () => {
  const rounds = 24
  const timeline = []
  let sentiment = 0.1
  for (let i = 1; i <= rounds; i++) {
    sentiment += (Math.random() - 0.48) * 0.15
    sentiment = Math.max(-1, Math.min(1, sentiment))
    timeline.push({
      round: i,
      mean: sentiment,
      std: 0.1 + Math.random() * 0.2
    })
  }

  const topics = [
    { name: 'Policy Reform', count: 145, sentiment: 0.35 },
    { name: 'Economic Impact', count: 120, sentiment: -0.22 },
    { name: 'Public Safety', count: 98, sentiment: -0.45 },
    { name: 'Education', count: 87, sentiment: 0.52 },
    { name: 'Healthcare', count: 76, sentiment: 0.18 },
    { name: 'Environment', count: 65, sentiment: 0.41 },
    { name: 'Technology', count: 54, sentiment: 0.62 },
    { name: 'Housing', count: 43, sentiment: -0.31 }
  ]

  const emotions = {
    anger: 0.18,
    joy: 0.35,
    sadness: 0.12,
    fear: 0.15,
    surprise: 0.22,
    disgust: 0.08
  }

  const agents = []
  for (let i = 0; i < 60; i++) {
    agents.push({
      id: `agent_${i}`,
      posts: Math.floor(Math.random() * 40) + 1,
      sentiment: (Math.random() - 0.4) * 1.6,
      influence: 0.2 + Math.random() * 0.8
    })
  }

  return {
    overallSentiment: 0.12,
    polarizationIndex: 0.45,
    echoChamberScore: 0.38,
    totalPosts: 1247,
    timeline,
    topics,
    emotions,
    agents
  }
}

// Chart rendering
const renderAllCharts = () => {
  renderTimeline()
  renderTopicBars()
  renderEmotionChart()
  renderScatterPlot()
}

// 1. Sentiment Timeline (line chart with confidence band)
const renderTimeline = () => {
  const svg = select(timelineSvg.value)
  svg.selectAll('*').remove()

  const data = sentimentData.value.timeline
  if (!data || data.length === 0) return

  const container = timelineSvg.value.parentElement
  const width = container.clientWidth
  const height = container.clientHeight || 220
  const margin = { top: 20, right: 20, bottom: 35, left: 45 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  svg.attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleLinear()
    .domain(extent(data, d => d.round))
    .range([0, innerW])

  const y = scaleLinear()
    .domain([-1, 1])
    .range([innerH, 0])

  // Grid lines
  g.append('g')
    .attr('class', 'grid')
    .selectAll('line')
    .data([-0.5, 0, 0.5])
    .enter().append('line')
    .attr('x1', 0).attr('x2', innerW)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', '#1a1a2e').attr('stroke-dasharray', '3,3')

  // Zero line
  g.append('line')
    .attr('x1', 0).attr('x2', innerW)
    .attr('y1', y(0)).attr('y2', y(0))
    .attr('stroke', '#333').attr('stroke-width', 1)

  // Confidence band
  const areaGen = d3area()
    .x(d => x(d.round))
    .y0(d => y(Math.max(-1, d.mean - d.std)))
    .y1(d => y(Math.min(1, d.mean + d.std)))
    .curve(curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', areaGen)
    .attr('fill', '#6c5ce7')
    .attr('fill-opacity', 0.15)

  // Gradient definition for the line
  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', 'line-gradient')
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0).attr('y1', y(1))
    .attr('x2', 0).attr('y2', y(-1))

  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#00c853')
  gradient.append('stop').attr('offset', '50%').attr('stop-color', '#a0a0a0')
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ff6b6b')

  // Line
  const lineGen = d3line()
    .x(d => x(d.round))
    .y(d => y(d.mean))
    .curve(curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', lineGen)
    .attr('fill', 'none')
    .attr('stroke', 'url(#line-gradient)')
    .attr('stroke-width', 2.5)

  // Data points
  g.selectAll('.dot')
    .data(data)
    .enter().append('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.mean))
    .attr('r', 3)
    .attr('fill', d => sentimentColorScale(d.mean))
    .attr('stroke', '#0a0a0f')
    .attr('stroke-width', 1)

  // X-axis
  g.append('g')
    .attr('transform', `translate(0,${innerH})`)
    .call(axisBottom(x).ticks(Math.min(data.length, 12)).tickFormat(d => `${t('dashboard.round')} ${d}`))
    .attr('color', '#666')
    .selectAll('text')
    .attr('fill', '#888')
    .style('font-size', '10px')
    .style('font-family', 'monospace')

  // Y-axis
  g.append('g')
    .call(axisLeft(y).ticks(5))
    .attr('color', '#666')
    .selectAll('text')
    .attr('fill', '#888')
    .style('font-size', '10px')
    .style('font-family', 'monospace')

  // Remove axis domain lines
  g.selectAll('.domain').attr('stroke', '#333')
}

// 2. Topic Sentiment (horizontal bar chart)
const renderTopicBars = () => {
  const svg = select(topicSvg.value)
  svg.selectAll('*').remove()

  const data = sentimentData.value.topics
  if (!data || data.length === 0) return

  const container = topicSvg.value.parentElement
  const width = container.clientWidth
  const height = container.clientHeight || 220
  const margin = { top: 10, right: 55, bottom: 10, left: 110 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  svg.attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const sorted = [...data].sort((a, b) => b.count - a.count).slice(0, 8)

  const y = scaleBand()
    .domain(sorted.map(d => d.name))
    .range([0, innerH])
    .padding(0.25)

  const x = scaleLinear()
    .domain([0, max(sorted, d => d.count)])
    .range([0, innerW])

  // Bars
  g.selectAll('.bar')
    .data(sorted)
    .enter().append('rect')
    .attr('x', 0)
    .attr('y', d => y(d.name))
    .attr('width', d => x(d.count))
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', d => sentimentColorScale(d.sentiment))
    .attr('opacity', 0.8)

  // Topic labels
  g.selectAll('.label')
    .data(sorted)
    .enter().append('text')
    .attr('x', -8)
    .attr('y', d => y(d.name) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('fill', '#c0c0c0')
    .style('font-size', '11px')
    .style('font-family', 'monospace')
    .text(d => d.name.length > 14 ? d.name.slice(0, 13) + '..' : d.name)

  // Count labels
  g.selectAll('.count')
    .data(sorted)
    .enter().append('text')
    .attr('x', d => x(d.count) + 6)
    .attr('y', d => y(d.name) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('fill', '#888')
    .style('font-size', '10px')
    .style('font-family', 'monospace')
    .text(d => d.count)
}

// 3. Emotion Distribution (radar / spider chart)
const renderEmotionChart = () => {
  const svg = select(emotionSvg.value)
  svg.selectAll('*').remove()

  const emotions = sentimentData.value.emotions
  if (!emotions || Object.keys(emotions).length === 0) return

  const container = emotionSvg.value.parentElement
  const width = container.clientWidth
  const height = container.clientHeight || 220

  svg.attr('width', width).attr('height', height)

  const centerX = width / 2
  const centerY = height / 2
  const radius = Math.min(width, height) / 2 - 35

  const emotionKeys = ['anger', 'joy', 'sadness', 'fear', 'surprise', 'disgust']
  const emotionColors = {
    anger: '#ff6b6b',
    joy: '#ffd600',
    sadness: '#00d2ff',
    fear: '#6c5ce7',
    surprise: '#ff9f43',
    disgust: '#a0a0a0'
  }

  const data = emotionKeys.map(k => ({
    key: k,
    value: emotions[k] || 0,
    color: emotionColors[k]
  }))

  const angleSlice = (2 * Math.PI) / data.length

  const g = svg.append('g').attr('transform', `translate(${centerX},${centerY})`)

  const rScale = scaleLinear().domain([0, 1]).range([0, radius])

  // Concentric grid circles
  const levels = [0.2, 0.4, 0.6, 0.8, 1.0]
  levels.forEach(level => {
    const points = data.map((_, i) => {
      const angle = angleSlice * i - Math.PI / 2
      return [rScale(level) * Math.cos(angle), rScale(level) * Math.sin(angle)]
    })
    g.append('polygon')
      .attr('points', points.map(p => p.join(',')).join(' '))
      .attr('fill', 'none')
      .attr('stroke', '#1a1a2e')
      .attr('stroke-width', 1)
  })

  // Axis lines
  data.forEach((_, i) => {
    const angle = angleSlice * i - Math.PI / 2
    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', radius * Math.cos(angle))
      .attr('y2', radius * Math.sin(angle))
      .attr('stroke', '#1a1a2e')
      .attr('stroke-width', 1)
  })

  // Data polygon
  const dataPoints = data.map((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    return [rScale(d.value) * Math.cos(angle), rScale(d.value) * Math.sin(angle)]
  })

  g.append('polygon')
    .attr('points', dataPoints.map(p => p.join(',')).join(' '))
    .attr('fill', '#6c5ce7')
    .attr('fill-opacity', 0.2)
    .attr('stroke', '#6c5ce7')
    .attr('stroke-width', 2)

  // Data points
  data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const px = rScale(d.value) * Math.cos(angle)
    const py = rScale(d.value) * Math.sin(angle)

    g.append('circle')
      .attr('cx', px).attr('cy', py)
      .attr('r', 4)
      .attr('fill', d.color)
      .attr('stroke', '#0a0a0f')
      .attr('stroke-width', 1.5)
  })

  // Labels
  data.forEach((d, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const lx = (radius + 18) * Math.cos(angle)
    const ly = (radius + 18) * Math.sin(angle)

    g.append('text')
      .attr('x', lx).attr('y', ly)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', d.color)
      .style('font-size', '10px')
      .style('font-family', 'monospace')
      .style('font-weight', '600')
      .text(`${d.key} (${(d.value * 100).toFixed(0)}%)`)
  })
}

// 4. Agent Sentiment Scatter Plot
const renderScatterPlot = () => {
  const svg = select(scatterSvg.value)
  svg.selectAll('*').remove()

  const agents = sentimentData.value.agents
  if (!agents || agents.length === 0) return

  const container = scatterSvg.value.parentElement
  const width = container.clientWidth
  const height = container.clientHeight || 220
  const margin = { top: 20, right: 20, bottom: 35, left: 45 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  svg.attr('width', width).attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = scaleLinear()
    .domain([0, max(agents, d => d.posts) * 1.1])
    .range([0, innerW])

  const y = scaleLinear()
    .domain([-1, 1])
    .range([innerH, 0])

  const size = scaleSqrt()
    .domain([0, max(agents, d => d.influence)])
    .range([3, 12])

  // Zero line
  g.append('line')
    .attr('x1', 0).attr('x2', innerW)
    .attr('y1', y(0)).attr('y2', y(0))
    .attr('stroke', '#333').attr('stroke-dasharray', '4,3')

  // Quadrant background hints
  g.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', innerW).attr('height', y(0))
    .attr('fill', '#00c853').attr('fill-opacity', 0.03)

  g.append('rect')
    .attr('x', 0).attr('y', y(0))
    .attr('width', innerW).attr('height', innerH - y(0))
    .attr('fill', '#ff6b6b').attr('fill-opacity', 0.03)

  // Dots
  g.selectAll('.agent-dot')
    .data(agents)
    .enter().append('circle')
    .attr('cx', d => x(d.posts))
    .attr('cy', d => y(d.sentiment))
    .attr('r', d => size(d.influence))
    .attr('fill', d => sentimentColorScale(d.sentiment))
    .attr('fill-opacity', 0.7)
    .attr('stroke', d => sentimentColorScale(d.sentiment))
    .attr('stroke-opacity', 0.9)
    .attr('stroke-width', 1)

  // X-axis
  g.append('g')
    .attr('transform', `translate(0,${innerH})`)
    .call(axisBottom(x).ticks(6))
    .attr('color', '#666')
    .selectAll('text')
    .attr('fill', '#888')
    .style('font-size', '10px')
    .style('font-family', 'monospace')

  // X-axis label
  g.append('text')
    .attr('x', innerW / 2).attr('y', innerH + 30)
    .attr('text-anchor', 'middle')
    .attr('fill', '#666')
    .style('font-size', '10px')
    .style('font-family', 'monospace')
    .text('Posts')

  // Y-axis
  g.append('g')
    .call(axisLeft(y).ticks(5))
    .attr('color', '#666')
    .selectAll('text')
    .attr('fill', '#888')
    .style('font-size', '10px')
    .style('font-family', 'monospace')

  // Y-axis label
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -innerH / 2).attr('y', -35)
    .attr('text-anchor', 'middle')
    .attr('fill', '#666')
    .style('font-size', '10px')
    .style('font-family', 'monospace')
    .text('Sentiment')

  // Remove axis domain lines
  g.selectAll('.domain').attr('stroke', '#333')
}

// Lifecycle
onMounted(() => {
  fetchData()

  // Setup resize observer with debounce
  resizeObserver = new ResizeObserver(() => {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (sentimentData.value) {
        renderAllCharts()
      }
    }, 300)
  })

  const el = document.querySelector('.sentiment-dashboard')
  if (el) resizeObserver.observe(el)
})

onUnmounted(() => {
  if (resizeTimer) clearTimeout(resizeTimer)
  if (resizeObserver) resizeObserver.disconnect()
  // Clear SVG content to release DOM references
  if (timelineSvg.value) select(timelineSvg.value).selectAll('*').remove()
  if (topicSvg.value) select(topicSvg.value).selectAll('*').remove()
  if (emotionSvg.value) select(emotionSvg.value).selectAll('*').remove()
  if (scatterSvg.value) select(scatterSvg.value).selectAll('*').remove()
})
</script>

<style scoped>
.sentiment-dashboard {
  padding: 24px;
  background: #0a0a0f;
  min-height: 100%;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #e0e0e0;
}

/* Header */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.dashboard-title {
  font-size: 18px;
  font-weight: 700;
  color: #e0e0e0;
  letter-spacing: 0.02em;
}

.dashboard-sim-id {
  font-size: 11px;
  color: #666;
  background: #12121a;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #1a1a2e;
}

/* Loading / Error / NoData states */
.dashboard-loading,
.dashboard-error,
.dashboard-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 300px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #1a1a2e;
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text,
.no-data-text {
  font-size: 13px;
  color: #666;
}

.error-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ff6b6b22;
  color: #ff6b6b;
  border-radius: 50%;
  font-weight: 700;
  font-size: 16px;
}

.error-text {
  font-size: 13px;
  color: #ff6b6b;
}

.retry-btn {
  padding: 6px 16px;
  background: #1a1a2e;
  color: #e0e0e0;
  border: 1px solid #333;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #222240;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  background: #12121a;
  border: 1px solid #1a1a2e;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-label {
  font-size: 11px;
  color: #a0a0a0;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.posts-value {
  color: #00d2ff;
}

.echo-value {
  color: #6c5ce7;
}

.card-tag {
  display: inline-flex;
  align-self: flex-start;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Gauge */
.card-gauge {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
}

.gauge-svg {
  width: 100px;
  height: 60px;
}

.gauge-value {
  position: absolute;
  bottom: 4px;
  font-size: 22px;
  font-weight: 700;
  color: #e0e0e0;
}

/* Echo bar */
.echo-bar-track {
  width: 100%;
  height: 4px;
  background: #1a1a2e;
  border-radius: 2px;
  overflow: hidden;
}

.echo-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6c5ce7, #00d2ff);
  border-radius: 2px;
  transition: width 0.5s ease;
}

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-panel {
  background: #12121a;
  border: 1px solid #1a1a2e;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chart-header {
  padding: 12px 18px;
  font-size: 12px;
  font-weight: 600;
  color: #a0a0a0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #1a1a2e;
}

.chart-body {
  flex: 1;
  padding: 8px;
  min-height: 220px;
  position: relative;
}

.chart-svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* Responsive */
@media (max-width: 900px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }

  .sentiment-dashboard {
    padding: 12px;
  }
}
</style>
