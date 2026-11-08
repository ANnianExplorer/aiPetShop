import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'
import { useUserStore } from '@/stores/user'

// 公开路径（不需要登录）
const publicPaths = ['/login', '/sign-up', '/reset-password']

// 是否已初始化（防止重复调用）
let storeInitialized = false

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
      path: '/',
      redirect: '/login'
    },
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
      path: '/app',
      component: MainLayout,
      redirect: '/home',
      children: [
        {
          path: '/home',
          name: 'home',
          component: () => import('@/views/home/Home.vue')
        },
        {
          path: '/pet-studio',
          name: 'petStudio',
          component: () => import('@/views/pet/PetStudio.vue')
        },
        {
          path: '/chat',
          name: 'chat',
          component: () => import('@/views/chat/ChatView.vue')
        },
        {
          path: '/community',
          name: 'community',
          component: () => import('@/views/community/Community.vue')
        },
        {
          path: '/wellness',
          name: 'wellness',
          component: () => import('@/views/wellness/Wellness.vue')
        },
        {
          path: '/profile',
          name: 'profile',
          component: () => import('@/views/profile/Profile.vue')
        },
        {
          path: '/life-log',
          name: 'lifeLog',
          component: () => import('@/views/lifelog/LifeLog.vue')
        },
        {
          path: '/post/:id',
          name: 'postDetail',
          component: () => import('@/views/community/PostDetail.vue')
        },
        {
          path: '/log/:id',
          name: 'logDetail',
          component: () => import('@/views/lifelog/LifeLogDetail.vue')
        },
        {
          path: '/schedules',
          name: 'scheduleList',
          component: () => import('@/views/schedule/ScheduleList.vue')
        },
        {
          path: '/add-reminder',
          name: 'addReminder',
          component: () => import('@/views/schedule/AddReminder.vue')
        },
        {
          path: '/notifications',
          name: 'notifications',
          component: () => import('@/views/schedule/Notifications.vue')
        },
        {
          path: '/new-log',
          name: 'newLog',
          component: () => import('@/views/community/NewLog.vue')
        },
        {
          path: '/new-topic',
          name: 'newTopic',
          component: () => import('@/views/community/NewTopic.vue')
        },
        {
          path: '/create-post',
          name: 'createPost',
          component: () => import('@/views/community/CreatePost.vue')
        },
        {
          path: '/topic/:id',
          name: 'topicDetail',
          component: () => import('@/views/community/TopicDetail.vue')
        },
        {
          path: '/topics-list',
          name: 'topicsList',
          component: () => import('@/views/community/TopicsList.vue')
        },
        {
          path: '/add-plan',
          name: 'addPlan',
          component: () => import('@/views/wellness/AddPlan.vue')
        },
        {
          path: '/weekly-health-detail',
          name: 'weeklyHealthDetail',
          component: () => import('@/views/wellness/WeeklyHealthDetail.vue')
        },
        {
          path: '/record-health-data',
          name: 'recordHealthData',
          component: () => import('@/views/wellness/RecordHealthData.vue')
        },
        {
          path: '/add-pet',
          name: 'addPet',
          component: () => import('@/views/pet/AddPet.vue')
        },
        {
          path: '/pet-detail/:id',
          name: 'petDetail',
          component: () => import('@/views/pet/PetDetail.vue')
        },
        {
          path: '/edit-profile',
          name: 'editProfile',
          component: () => import('@/views/profile/EditProfile.vue')
        },
        {
          path: '/account-security',
          name: 'accountSecurity',
          component: () => import('@/views/profile/AccountSecurity.vue')
        },
        {
          path: '/general-settings',
          name: 'generalSettings',
          component: () => import('@/views/profile/GeneralSettings.vue')
        },
        {
          path: '/help-feedback',
          name: 'helpFeedback',
          component: () => import('@/views/profile/HelpFeedback.vue')
        },
        {
          path: '/user/:id',
          name: 'userProfile',
          component: () => import('@/views/community/UserProfile.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('satoken')
  const isPublicPath = publicPaths.includes(to.path)

  if (!token && !isPublicPath) {
    next('/login')
  } else if (token && isPublicPath) {
    next('/home')
  } else {
    // 已登录访问非公开页面 → 确保 store 已初始化
    if (token && !storeInitialized) {
      const userStore = useUserStore()
      try {
        await userStore.init()
        storeInitialized = true
      } catch (e) {
        // 初始化失败（token 过期等），清除登录状态
        localStorage.removeItem('satoken')
        storeInitialized = false
        next('/login')
        return
      }
    }
    next()
  }
})

export default router
