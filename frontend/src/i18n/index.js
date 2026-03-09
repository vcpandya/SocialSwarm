import { createI18n } from 'vue-i18n'
import en from './en.json'
import zh from './zh.json'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'en',
  fallbackLocale: 'en',
  messages: { en, zh }
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en'
}

export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
