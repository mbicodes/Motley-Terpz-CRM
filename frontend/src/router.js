import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'

const routes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/pages/MobileNotification.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    alias: '/leads',
    path: '/leads/view/:viewType?',
    name: 'Leads',
    component: () => import('@/pages/Leads.vue'),
  },
  {
    path: '/leads/:leadId',
    name: 'Lead',
    component: () => import(`@/pages/${handleMobileView('Lead')}.vue`),
    props: true,
  },
  {
    alias: '/deals',
    path: '/deals/view/:viewType?',
    name: 'Deals',
    component: () => import('@/pages/Deals.vue'),
  },
  {
    path: '/deals/:dealId',
    name: 'Deal',
    component: () => import(`@/pages/${handleMobileView('Deal')}.vue`),
    props: true,
  },
  {
    alias: '/notes',
    path: '/notes/view/:viewType?',
    name: 'Notes',
    component: () => import('@/pages/Notes.vue'),
  },
  {
    alias: '/tasks',
    path: '/tasks/view/:viewType?',
    name: 'Tasks',
    component: () => import('@/pages/Tasks.vue'),
  },
  // Motley Terpz — pipeline customer views (between Deals and Contacts)
  {
    path: '/customers/:pipeline',
    name: 'PipelineCustomers',
    component: () => import('@/pages/PipelineCustomers.vue'),
    props: true,
  },
  // Motley Terpz — pipeline health dashboard
  {
    path: '/pipeline-health',
    name: 'PipelineHealth',
    component: () => import('@/pages/PipelineHealthDashboard.vue'),
  },
  // Motley Terpz — deal pipeline kanban boards
  {
    path: '/pipeline/fresh-frozen',
    name: 'PipelineFreshFrozen',
    component: () => import('@/pages/PipelineKanban.vue'),
    props: { pipeline: 'fresh_frozen' },
  },
  {
    path: '/pipeline/rosin',
    name: 'PipelineRosin',
    component: () => import('@/pages/PipelineKanban.vue'),
    props: { pipeline: 'rosin' },
  },
  {
    path: '/pipeline/distro',
    name: 'PipelineDistro',
    component: () => import('@/pages/PipelineKanban.vue'),
    props: { pipeline: 'distro' },
  },
  {
    path: '/pipeline/tolling',
    name: 'PipelineTolling',
    component: () => import('@/pages/PipelineKanban.vue'),
    props: { pipeline: 'tolling' },
  },
  // Motley Terpz — Sales Intelligence
  {
    path: '/approvals',
    name: 'ApprovalsQueue',
    component: () => import('@/pages/ApprovalsQueue.vue'),
  },
  {
    path: '/copack-calculator',
    name: 'CoPackCalculator',
    component: () => import('@/pages/CoPackCalculator.vue'),
  },
  {
    path: '/tolling-calculator',
    name: 'TollingCalculator',
    component: () => import('@/pages/TollingCalculator.vue'),
  },
  {
    path: '/rep-leaderboard',
    name: 'RepLeaderboard',
    component: () => import('@/pages/RepLeaderboard.vue'),
  },
  {
    path: '/goal-vs-actual',
    name: 'GoalVsActual',
    component: () => import('@/pages/GoalVsActual.vue'),
  },
  {
    path: '/upcoming-deliveries',
    name: 'UpcomingDeliveries',
    component: () => import('@/pages/UpcomingDeliveries.vue'),
  },
  {
    path: '/purchase-insights',
    name: 'PurchaseInsights',
    component: () => import('@/pages/PurchaseInsights.vue'),
  },
  {
    path: '/sales-command-center',
    name: 'SalesCommandCenter',
    component: () => import('@/pages/SalesCommandCenter.vue'),
  },
  {
    path: '/cash-projection',
    name: 'CashProjection',
    component: () => import('@/pages/CashProjection.vue'),
  },
  {
    path: '/customer-health-scores',
    name: 'CustomerHealthScores',
    component: () => import('@/pages/CustomerHealthScores.vue'),
  },
  {
    path: '/sales-projection',
    name: 'SalesProjection',
    component: () => import('@/pages/SalesProjection.vue'),
  },
  {
    path: '/ar-aging-heatmap',
    name: 'ArAgingHeatmap',
    component: () => import('@/pages/ArAgingHeatmap.vue'),
  },
  {
    path: '/customer-segmentation',
    name: 'CustomerSegmentation',
    component: () => import('@/pages/CustomerSegmentation.vue'),
  },
  {
    path: '/my-day',
    name: 'MyDay',
    component: () => import('@/pages/MyDay.vue'),
  },
  {
    path: '/customer-dashboard/:customerId',
    name: 'CustomerDashboard',
    component: () => import('@/pages/CustomerDashboard.vue'),
    props: true,
  },
  {
    path: '/customer-records/:customerId',
    name: 'CustomerRecords',
    component: () => import('@/pages/CustomerRecords.vue'),
    props: true,
  },
  {
    alias: '/contacts',
    path: '/contacts/view/:viewType?',
    name: 'Contacts',
    component: () => import('@/pages/Contacts.vue'),
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    component: () => import(`@/pages/${handleMobileView('Contact')}.vue`),
    props: true,
  },
  {
    alias: '/organizations',
    path: '/organizations/view/:viewType?',
    name: 'Organizations',
    component: () => import('@/pages/Organizations.vue'),
  },
  {
    path: '/organizations/:organizationId',
    name: 'Organization',
    component: () => import(`@/pages/${handleMobileView('Organization')}.vue`),
    props: true,
  },
  {
    alias: '/call-logs',
    path: '/call-logs/view/:viewType?',
    name: 'Call Logs',
    component: () => import('@/pages/CallLogs.vue'),
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: () => import('@/pages/Calendar.vue'),
  },
  {
    path: '/data-import',
    name: 'DataImportList',
    component: () => import('@/pages/DataImport.vue'),
  },
  {
    path: '/data-import/doctype/:doctype',
    name: 'NewDataImport',
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/data-import/:importName',
    name: 'DataImport',
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: () => import('@/pages/Welcome.vue'),
  },
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
  {
    path: '/not-permitted',
    name: 'Not Permitted',
    component: () => import('@/pages/NotPermitted.vue'),
  },
]

const handleMobileView = (componentName) => {
  return window.innerWidth < 768 ? `Mobile${componentName}` : componentName
}

let router = createRouter({
  history: createWebHistory('/crm'),
  routes,
})

router.beforeEach(async (to, from, next) => {
  router.previousRoute = from

  const { isLoggedIn } = sessionStore()
  const { users, isCrmUser } = usersStore()

  if (isLoggedIn && !users.fetched) {
    try {
      await users.promise
    } catch (error) {
      console.error('Error loading users', error)
    }
  }

  if (isLoggedIn && to.name !== 'Not Permitted' && !isCrmUser()) {
    next({ name: 'Not Permitted' })
  } else if (to.name === 'Home' && isLoggedIn) {
    const { views, getDefaultView } = viewsStore()
    await views.promise

    let defaultView = getDefaultView()
    if (!defaultView) {
      next({ name: 'Leads' })
      return
    }

    let { route_name, type, name, is_standard } = defaultView
    route_name = route_name || 'Leads'

    if (name && !is_standard) {
      next({
        name: route_name,
        params: { viewType: type },
        query: { view: name },
      })
    } else {
      next({ name: route_name, params: { viewType: type } })
    }
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/crm'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else if (['Deal', 'Lead'].includes(to.name) && !to.hash) {
    let storageKey = to.name === 'Deal' ? 'lastDealTab' : 'lastLeadTab'
    const activeTab = localStorage.getItem(storageKey) || 'activity'
    const hash = '#' + activeTab
    next({ ...to, hash })
  } else if (
    [
      'Leads',
      'Deals',
      'Contacts',
      'Organizations',
      'Notes',
      'Tasks',
      'Call Logs',
    ].includes(to.name) &&
    !to.query?.view
  ) {
    const { views, standardViews, getDefaultView } = viewsStore()
    await views.promise

    const viewType = to.params?.viewType ?? ''
    const standardViewTypes = ['list', 'kanban', 'group_by']

    if (!viewType) {
      const doctypeMap = {
        Leads: 'CRM Lead',
        Deals: 'CRM Deal',
        Contacts: 'Contact',
        Organizations: 'CRM Organization',
        Notes: 'FCRM Note',
        Tasks: 'CRM Task',
        'Call Logs': 'CRM Call Log',
      }

      const doctype = doctypeMap[to.name]
      let defaultViewType = 'list'

      let globalDefault = getDefaultView()
      if (globalDefault && globalDefault.route_name === to.name) {
        defaultViewType = globalDefault.type || 'list'
        if (globalDefault.name && !globalDefault.is_standard) {
          next({
            name: to.name,
            params: { viewType: defaultViewType },
            query: { ...to.query, view: globalDefault.name },
          })
          return
        }
      }

      for (const viewType of standardViewTypes) {
        const standardView = standardViews.value?.[doctype + ' ' + viewType]
        if (standardView?.is_default) {
          defaultViewType = viewType
          break
        }
      }

      next({
        name: to.name,
        params: { viewType: defaultViewType },
        query: to.query,
      })
    } else if (!standardViewTypes.includes(viewType)) {
      const viewNameOrLabel = viewType

      let view = views.data?.find(
        (v) => v.name == viewNameOrLabel || v.label === viewNameOrLabel,
      )

      if (view) {
        next({
          name: to.name,
          params: { viewType: view.type || 'list' },
          query: { ...to.query, view: view.name },
        })
      } else {
        next({
          name: to.name,
          params: { viewType: 'list' },
          query: to.query,
        })
      }
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
