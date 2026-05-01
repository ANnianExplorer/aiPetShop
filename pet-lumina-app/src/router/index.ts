import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/sign-up',
      name: 'signUp',
      component: () => import('@/views/SignUp.vue')
    },
    {
      path: '/reset-password',
      name: 'resetPassword',
      component: () => import('@/views/ResetPassword.vue')
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/Home.vue')
        },
        {
          path: 'community',
          name: 'community',
          component: () => import('@/views/Community.vue')
        },
        {
          path: 'wellness',
          name: 'wellness',
          component: () => import('@/views/Wellness.vue')
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/Profile.vue')
        },
        {
        path: 'life-log',
        name: 'lifeLog',
        component: () => import('@/views/LifeLog.vue')
      },
      {
        path: 'post/:id',
        name: 'postDetail',
        component: () => import('@/views/PostDetail.vue')
      },
      {
        path: 'log/:id',
        name: 'logDetail',
        component: () => import('@/views/LifeLogDetail.vue')
      },
      {
        path: 'schedules',
        name: 'scheduleList',
        component: () => import('@/views/ScheduleList.vue')
      },
      {
        path: 'add-reminder',
        name: 'addReminder',
        component: () => import('@/views/AddReminder.vue')
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/Notifications.vue')
      },
      {
        path: 'new-topic',
        name: 'newTopic',
        component: () => import('@/views/NewTopic.vue')
      },
      {
        path: 'topic/:id',
        name: 'topicDetail',
        component: () => import('@/views/TopicDetail.vue')
      },
      {
        path: 'topics-list',
        name: 'topicsList',
        component: () => import('@/views/TopicsList.vue')
      },
      {
        path: 'add-plan',
        name: 'addPlan',
        component: () => import('@/views/AddPlan.vue')
      },
      {
        path: 'weekly-health-detail',
        name: 'weeklyHealthDetail',
        component: () => import('@/views/WeeklyHealthDetail.vue')
      },
      {
        path: 'record-health-data',
        name: 'recordHealthData',
        component: () => import('@/views/RecordHealthData.vue')
      },
      {
        path: 'add-pet',
        name: 'addPet',
        component: () => import('@/views/AddPet.vue')
      },
      {
        path: 'pet-detail/:id',
        name: 'petDetail',
        component: () => import('@/views/PetDetail.vue')
      },
      {
        path: 'edit-profile',
        name: 'editProfile',
        component: () => import('@/views/EditProfile.vue')
      },
      {
        path: 'account-security',
        name: 'accountSecurity',
        component: () => import('@/views/AccountSecurity.vue')
      },
      {
        path: 'general-settings',
        name: 'generalSettings',
        component: () => import('@/views/GeneralSettings.vue')
      },
      {
        path: 'help-feedback',
        name: 'helpFeedback',
        component: () => import('@/views/HelpFeedback.vue')
      },
      {
        path: 'user/:id',
        name: 'userProfile',
        component: () => import('@/views/UserProfile.vue')
      }
      ]
    }
  ]
})

export default router
