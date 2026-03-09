<template>
  <div class="dashboard-view">
    <SentimentDashboard :simulationId="simulationId" />
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import SentimentDashboard from '../components/SentimentDashboard.vue'

const props = defineProps({
  simulationId: { type: String, required: true }
})
</script>

<style scoped>
.dashboard-view {
  height: 100vh;
  background: #0a0a0f;
  overflow-y: auto;
}
</style>
