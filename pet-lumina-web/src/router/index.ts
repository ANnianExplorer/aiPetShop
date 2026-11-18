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
        path: 'user/add',
        name: 'addUser',
        component: () => import('@/views/user/AddUser.vue'),
        meta: { title: '新增用户', parent: '用户管理' },
      },
      {
        path: 'user/edit/:id',
        name: 'editUser',
        component: () => import('@/views/user/EditUser.vue'),
        meta: { title: '编辑用户', parent: '用户管理' },
      },
      {
        path: 'pet',
        name: 'petList',
        component: () => import('@/views/pet/PetList.vue'),
        meta: { title: '宠物管理' },
      },
      {
        path: 'pet/add',
        name: 'addPet',
        component: () => import('@/views/pet/AddPet.vue'),
        meta: { title: '添加宠物', parent: '宠物管理' },
      },
      {
        path: 'pet/edit/:id',
        name: 'editPet',
        component: () => import('@/views/pet/EditPet.vue'),
        meta: { title: '编辑宠物', parent: '宠物管理' },
      },
      {
        path: 'pet/:id',
        name: 'petDetail',
        component: () => import('@/views/pet/PetDetail.vue'),
        meta: { title: '宠物详情', parent: '宠物管理' },
      },
      {
        path: 'post',
        name: 'postList',
        component: () => import('@/views/content/PostList.vue'),
        meta: { title: '帖子管理' },
      },
      {
        path: 'post/:id',
        name: 'postDetail',
        component: () => import('@/views/content/PostDetail.vue'),
        meta: { title: '帖子详情', parent: '帖子管理' },
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
        path: 'log/:id',
        name: 'recordDetail',
        component: () => import('@/views/content/RecordDetail.vue'),
        meta: { title: '记录详情', parent: '生活记录' },
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
      {
        path: 'violation',
        name: 'violationManage',
        component: () => import('@/views/content/ViolationManage.vue'),
        meta: { title: '违规管理' },
      },
      {
        path: 'agent/sessions',
        name: 'agentSessions',
        component: () => import('@/views/agent/SessionList.vue'),
        meta: { title: '会话工作台' },
      },
      {
        path: 'agent/sessions/:id',
        name: 'agentSessionDetail',
        component: () => import('@/views/agent/SessionDetail.vue'),
        meta: { title: '会话详情', parent: '会话工作台' },
      },
      {
        path: 'agent/queue',
        name: 'agentQueue',
        component: () => import('@/views/agent/Queue.vue'),
        meta: { title: '队列运维' },
      },
      {
        path: 'agent/model',
        name: 'agentModelConfig',
        component: () => import('@/views/agent/ModelConfig.vue'),
        meta: { title: '模型配置' },
      },
      {
        path: 'agent/memory',
        name: 'agentMemory',
        component: () => import('@/views/agent/Memory.vue'),
        meta: { title: '长期记忆' },
      },
      {
        path: 'agent/graph',
        name: 'agentGraph',
        component: () => import('@/views/agent/Graph.vue'),
        meta: { title: '知识图谱' },
      },
      {
        path: 'agent/profile',
        name: 'agentProfile',
        component: () => import('@/views/agent/Profile.vue'),
        meta: { title: '宠物画像' },
      },
      {
        path: 'settings',
        name: 'systemSettings',
        component: () => import('@/views/settings/SystemSettings.vue'),
        meta: { title: '系统设置' },
      },
      {
        path: 'profile',
        name: 'personalCenter',
        component: () => import('@/views/profile/PersonalCenter.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
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