import service from './index'

export const getSettingsStatus = () => {
  return service.get('/api/settings/status')
}

export const getSettings = () => {
  return service.get('/api/settings')
}

export const saveSettings = (data) => {
  return service.post('/api/settings', data)
}

export const validateSettings = (group, values) => {
  return service.post('/api/settings/validate', { group, values })
}
