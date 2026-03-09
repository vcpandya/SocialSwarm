import api from './index'

export const getSentimentAnalysis = (simulationId) => {
  return api.get(`/api/simulation/${simulationId}/sentiment`)
}

export const getSentimentTimeline = (simulationId) => {
  return api.get(`/api/simulation/${simulationId}/sentiment/timeline`)
}
