import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHashHistory(),
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
      component: () => import('@/views/auth/Login.vue')
    },
    {
      path: '/sign-up',
      name: 'signUp',
      component: () => import('@/views/auth/SignUp.vue')
    },
    {
      path: '/reset-password',
      name: 'resetPassword',
      component: () => import('@/views/auth/ResetPassword.vue')
    },
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/app',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/home/Home.vue')
        },
        {
          path: 'community',
          name: 'community',
          component: () => import('@/views/community/Community.vue')
        },
        {
          path: 'wellness',
          name: 'wellness',
          component: () => import('@/views/wellness/Wellness.vue')
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/profile/Profile.vue')
        },
        {
          path: 'life-log',
          name: 'lifeLog',
          component: () => import('@/views/lifelog/LifeLog.vue')
        },
        {
          path: 'post/:id',
          name: 'postDetail',
          component: () => import('@/views/community/PostDetail.vue')
        },
        {
          path: 'log/:id',
          name: 'logDetail',
          component: () => import('@/views/lifelog/LifeLogDetail.vue')
        },
        {
          path: 'schedules',
          name: 'scheduleList',
          component: () => import('@/views/schedule/ScheduleList.vue')
        },
        {
          path: 'add-reminder',
          name: 'addReminder',
          component: () => import('@/views/schedule/AddReminder.vue')
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/schedule/Notifications.vue')
        },
        {
          path: 'new-topic',
          name: 'newTopic',
          component: () => import('@/views/community/NewTopic.vue')
        },
        {
          path: 'topic/:id',
          name: 'topicDetail',
          component: () => import('@/views/community/TopicDetail.vue')
        },
        {
          path: 'topics-list',
          name: 'topicsList',
          component: () => import('@/views/community/TopicsList.vue')
        },
        {
          path: 'add-plan',
          name: 'addPlan',
          component: () => import('@/views/wellness/AddPlan.vue')
        },
        {
          path: 'weekly-health-detail',
          name: 'weeklyHealthDetail',
          component: () => import('@/views/wellness/WeeklyHealthDetail.vue')
        },
        {
          path: 'record-health-data',
          name: 'recordHealthData',
          component: () => import('@/views/wellness/RecordHealthData.vue')
        },
        {
          path: 'add-pet',
          name: 'addPet',
          component: () => import('@/views/pet/AddPet.vue')
        },
        {
          path: 'pet-detail/:id',
          name: 'petDetail',
          component: () => import('@/views/pet/PetDetail.vue')
        },
        {
          path: 'edit-profile',
          name: 'editProfile',
          component: () => import('@/views/profile/EditProfile.vue')
        },
        {
          path: 'account-security',
          name: 'accountSecurity',
          component: () => import('@/views/profile/AccountSecurity.vue')
        },
        {
          path: 'general-settings',
          name: 'generalSettings',
          component: () => import('@/views/profile/GeneralSettings.vue')
        },
        {
          path: 'help-feedback',
          name: 'helpFeedback',
          component: () => import('@/views/profile/HelpFeedback.vue')
        },
        {
          path: 'user/:id',
          name: 'userProfile',
          component: () => import('@/views/community/UserProfile.vue')
        }
      ]
    }
  ]
})

export default router
