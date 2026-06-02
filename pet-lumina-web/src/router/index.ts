import { createRouter, createWebHashHistory } from 'vue-router'
import AdminLayout from '@/layout/AdminLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/Login.vue'),
    meta: { title: '管理员登录' },
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '数据概览' },
      },
      {
        path: 'user',
        name: 'userList',
        component: () => import('@/views/user/UserList.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'pet',
        name: 'petList',
        component: () => import('@/views/pet/PetList.vue'),
        meta: { title: '宠物管理' },
      },
      {
        path: 'post',
        name: 'postList',
        component: () => import('@/views/content/PostList.vue'),
        meta: { title: '帖子管理' },
      },
      {
        path: 'comment',
        name: 'commentList',
        component: () => import('@/views/content/CommentList.vue'),
        meta: { title: '评论管理' },
      },
      {
        path: 'log',
        name: 'logList',
        component: () => import('@/views/content/LogList.vue'),
        meta: { title: '生活记录' },
      },
      {
        path: 'topic',
        name: 'topicList',
        component: () => import('@/views/content/TopicList.vue'),
        meta: { title: '话题管理' },
      },
      {
        path: 'health',
        name: 'healthData',
        component: () => import('@/views/health/HealthData.vue'),
        meta: { title: '健康数据' },
      },
      {
        path: 'notification',
        name: 'notificationList',
        component: () => import('@/views/notification/NotificationList.vue'),
        meta: { title: '通知管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('satoken')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
