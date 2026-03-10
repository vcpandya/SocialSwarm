import { createRouter, createWebHistory } from 'vue-router'
import { fetchConfigStatus, getConfigStatus } from '../store/configStatus'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: () => import('../views/MainView.vue'),
    props: true
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: () => import('../views/SimulationView.vue'),
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: () => import('../views/SimulationRunView.vue'),
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: () => import('../views/ReportView.vue'),
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: () => import('../views/InteractionView.vue'),
    props: true
  },
  {
    path: '/dashboard/:simulationId',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    props: true
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupWizard.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsPage.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  // Don't guard the setup page itself
  if (to.name === 'Setup') {
    next()
    return
  }

  const status = getConfigStatus()
  if (!status.isLoaded) {
    await fetchConfigStatus()
  }

  if (status.configured === false) {
    next({ name: 'Setup' })
  } else {
    next()
  }
})

export default router
