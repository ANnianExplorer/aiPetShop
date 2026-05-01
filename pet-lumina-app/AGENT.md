# PetLumina 前端开发记录 (AGENT.md)

## 1. 项目定位与架构目标
本项目 (PetLumina) 旨在提供一个现代、流畅的宠物生活管理与社区互动移动端 Web App。
为保证**企业级代码开发规范**和**过程质量**，我们确立以下架构目标：
- **高内聚低耦合 (Componentization)**：杜绝单文件面条代码，页面级组件 (`views`) 仅负责路由接入与数据分发，UI 呈现严格下沉至 `components` 目录。
- **类型安全 (Type Safety)**：全程使用 TypeScript 严格模式，核心业务实体必须在 `src/types` 中定义接口 (`Interface`)，拒绝 `any`。
- **集中状态管理 (State Management)**：使用 Pinia 进行全局状态共享（如用户信息、宠物档案），页面组件不应直接持有应共享的业务数据。
- **样式规范 (Design System)**：统一使用 Tailwind CSS 结合 `DESIGN.md` 中提取的设计令牌 (Tokens)，避免硬编码魔法值 (Magic Numbers)。

## 2. 目录规范
```text
src/
├── api/          # 接口请求层 (Axios 封装)
├── assets/       # 静态资源 (图片、SVG等)
├── components/   # 公共/业务组件
│   ├── common/   # 全局通用组件 (如自定义Button, Card)
│   ├── home/     # 首页拆分组件 (TodayReminders, PetStatusBento 等)
│   ├── lifelog/  # 记录页拆分组件 (LogCard 等)
│   ├── community/# 社区页拆分组件 (TrendingSlider, PostFeed 等)
│   ├── wellness/ # 饮食健康拆分组件 (BentoDashboard, DailyTasks 等)
│   └── profile/  # 个人中心拆分组件 (UserInfo, PetList 等)
├── layout/       # 页面布局组件
├── router/       # 路由配置
├── stores/       # Pinia 状态管理 (如 user.ts)
├── types/        # TypeScript 类型定义 (如 index.ts)
├── utils/        # 工具函数
├── views/        # 页面级组件 (视图入口)
├── App.vue
└── main.ts
```

## 3. 迁移进度与决策记录

### Phase 1: 基础工程初始化 (完成)
- [x] Vue 3 + Vite + TS 搭建
- [x] 注入 `DESIGN.md` 设计 Token 到 Tailwind 配置
- [x] 配置全局底部导航 `MainLayout`
- [x] 初步迁移 Login 与 Home 静态页

### Phase 2: 企业级重构与深度迁移 (完成)
- [x] 提取业务数据接口 (`src/types/index.ts`)，包含 `User`, `Pet`, `Reminder`, `Post`, `Topic`, `LogEntry` 等
- [x] 建立全局状态 (`src/stores/user.ts`)，使用 Pinia 存放当前用户、宠物信息、健康数据、任务列表，跨页面共享
- [x] 重构 Home 页面：将原来几百行的代码拆分为 `TodayReminders.vue`, `PetStatusBento.vue`, `QuickActions.vue`, `CommunityTrends.vue`，提高可维护性
- [x] 迁移 LifeLog (生活记录) 页面：基于原型，实现标签过滤逻辑，并抽离了复用卡片组件 `LogCard.vue`
- [x] 迁移 Community (宠物社区) 页面：实现了顶部横向滑动的话题推荐 (`TrendingSlider.vue`) 和瀑布流帖子列表 (`PostFeed.vue`)
- [x] 迁移 Wellness (饮食健康) 页面：拆分 `BentoDashboard.vue`, `DailyTasks.vue`, `WeeklyIndicators.vue`，实现健康数据大屏展现
- [x] 迁移 Profile (个人中心) 页面：拆分 `UserInfo.vue`, `PetList.vue`, `SettingsMenu.vue`，实现用户信息与宠物卡片的模块化渲染

### Phase 3: 代码质量保障 (完成)
- [x] 配置 `vite-env.d.ts` 以解决 `import.meta.env` 类型报错，确保构建安全
- [x] 执行全局 TypeScript 与 Vue 模板校验 (`vue-tsc -b`) 确认全量代码 **0 Errors**

### Phase 4: 认证页面开发 (完成)
- [x] 创建登录页面 (`src/views/Login.vue`)：实现账号密码输入、密码显示切换、忘记密码跳转、注册跳转
- [x] 创建注册页面 (`src/views/SignUp.vue`)：实现手机号/邮箱输入、验证码获取、密码设置、登录跳转
- [x] 创建重置密码页面 (`src/views/ResetPassword.vue`)：实现账号验证、新密码设置、验证码输入
- [x] 配置路由 (`src/router/index.ts`)：添加 `/login`, `/signUp`, `/resetPassword` 路由
- [x] 添加玻璃拟态样式 (`src/style.css`)：定义 `glass-panel` 工具类
- [x] 添加动画工具类 (`tailwind.config.js`)：定义 `animate-fade-in`, `animate-slide-up` 等

### Phase 5: 认证页面布局优化 (完成)
- [x] 统一认证页面布局：使用 `fixed inset-0 flex items-center justify-center` 实现内容居中
- [x] 优化 Logo 区域：添加 `pt-lg` 顶部内边距，Logo 尺寸调整为 `w-14 h-14`，图标大小 `text-[28px]`
- [x] 优化表单高度：输入框和按钮高度从 `h-14` 调整为 `h-12`，表单间距从 `space-y-md` 改为 `space-y-sm`
- [x] 优化卡片内边距：从 `p-xl` 改为 `p-lg`，标题间距从 `mb-xl` 改为 `mb-lg`
- [x] 优化底部间距：统一使用 `mt-lg`，移除多余的 spacer 元素
- [x] 解决滚动问题：使用 `overflow-hidden` 防止页面滚动，确保内容完全适配视口

### Phase 6: 功能页面深度开发 (完成)
- [x] 生活记录详情页 (`LifeLogDetail.vue`)：展示记录详情、图片轮播、标签信息
- [x] 帖子详情页 (`PostDetail.vue`)：展示帖子内容、评论列表、点赞收藏功能
- [x] 话题列表页 (`TopicsList.vue`)：展示所有话题分类、话题卡片
- [x] 话题详情页 (`TopicDetail.vue`)：展示话题下的帖子列表
- [x] 新话题发布页 (`NewTopic.vue`)：实现话题创建表单
- [x] 日程列表页 (`ScheduleList.vue`)：展示所有日程安排、按日期分组
- [x] 添加提醒页 (`AddReminder.vue`)：实现提醒创建表单、时间选择、类型选择
- [x] 通知中心页 (`Notifications.vue`)：展示系统通知、消息列表
- [x] 周健康详情页 (`WeeklyHealthDetail.vue`)：展示周度健康数据趋势、图表
- [x] 记录健康数据页 (`RecordHealthData.vue`)：实现健康数据录入表单
- [x] 添加计划页 (`AddPlan.vue`)：实现健康计划创建表单
- [x] 添加宠物页 (`AddPet.vue`)：实现宠物信息录入表单、图片上传
- [x] 宠物详情页 (`PetDetail.vue`)：展示宠物详细信息、健康数据、历史记录
- [x] 编辑资料页 (`EditProfile.vue`)：实现用户资料编辑表单
- [x] 账号安全页 (`AccountSecurity.vue`)：展示账号安全设置、密码修改
- [x] 通用设置页 (`GeneralSettings.vue`)：展示应用设置选项
- [x] 帮助反馈页 (`HelpFeedback.vue`)：展示帮助中心、反馈表单

### Phase 7: 公共组件开发 (完成)
- [x] 评论弹窗 (`CommentModal.vue`)：实现评论输入、表情选择、提交功能
- [x] 表情选择器 (`EmojiPicker.vue`)：实现表情网格展示、选择功能
- [x] 分享弹窗 (`ShareModal.vue`)：实现分享渠道选择、复制链接功能
- [x] 提示组件 (`Toast.vue`)：实现全局提示消息展示
- [x] Toast 组合式函数 (`useToast.ts`)：提供全局 Toast 调用方法

### Phase 8: 功能修复与目录重组 (完成)
- [x] 修复话题详情页相关帖子点击跳转 (`TopicDetail.vue`)：添加 `goToPostDetail` 方法
- [x] 修复表情选择器空表情渲染问题 (`EmojiPicker.vue`)：使用 `.filter(e => e.trim() !== '')` 过滤空字符串
- [x] 创建用户详情页 (`UserProfile.vue`)：支持查看用户信息、帖子列表、关注/取关功能
- [x] 帖子详情页添加发帖人头像点击跳转 (`PostDetail.vue`)：点击头像跳转到用户主页
- [x] 帖子详情页添加返回上一页功能 (`PostDetail.vue`)：使用 `router.back()`
- [x] views 目录按功能页面分级重组：
  - `auth/` - 认证相关页面 (Login, SignUp, ResetPassword)
  - `community/` - 社区相关页面 (Community, PostDetail, TopicDetail, TopicsList, NewTopic, UserProfile)
  - `home/` - 首页 (Home)
  - `lifelog/` - 生活记录相关页面 (LifeLog, LifeLogDetail)
  - `pet/` - 宠物相关页面 (AddPet, PetDetail)
  - `profile/` - 个人中心相关页面 (Profile, EditProfile, AccountSecurity, GeneralSettings, HelpFeedback)
  - `schedule/` - 日程提醒相关页面 (ScheduleList, AddReminder, Notifications)
  - `wellness/` - 健康管理相关页面 (Wellness, WeeklyHealthDetail, RecordHealthData, AddPlan)
- [x] 更新路由配置 (`router/index.ts`)：同步所有路由路径引用到新目录结构
- [x] 修复路由跳转一致性 (`ScheduleList.vue`)：将路径跳转改为命名路由跳转
- [x] 记录详情页添加分享弹窗 (`LifeLogDetail.vue`)：导入 ShareModal 组件，添加分享按钮点击事件
- [x] 修复 ShareModal 关闭逻辑 (`ShareModal.vue`)：将 `emit('close')` 改为 `emit('update:visible', false)` 支持 `v-model:visible`
- [x] 统一所有 ShareModal 使用方式 (`PostDetail.vue`, `PostFeed.vue`)：使用 `v-model:visible` 替代 `:visible` + `@close`，并添加 `Teleport`

### Phase 9: HBuilder APK 打包适配 (完成)
- [x] 配置 Vite 构建输出到 HBuilder 项目目录 (`vite.config.ts` / `vite.config.js`)：
  - `base: './'` - 资源路径改为相对路径，适配本地文件加载
  - `outDir: '../ai-pet-app'` - 构建产物直接输出到 `ai-pet-app` 目录
  - `emptyOutDir: false` - 保留 `manifest.json` 等配置文件不被清空
- [x] 路由模式改为 Hash 模式 (`router/index.ts`)：将 `createWebHistory` 改为 `createWebHashHistory`，解决 5+App `file://` 协议下白屏问题
- [x] 调整路由结构：
  - `/` 重定向到 `/login`（默认打开登录页）
  - 主应用路由改为 `/app` 前缀（避免与根路由冲突）
- [x] 更新所有路由跳转引用：
  - `Login.vue` - 登录后跳转到 `/app`
  - `MainLayout.vue` - 底部导航首页按钮跳转到 `/app`
  - `QuickActions.vue` - "更多"按钮路径改为 `/app`
- [x] 创建 `manifest.json` 配置文件 (`ai-pet-app/manifest.json`)：
  - 应用标识：`com.petlumina.app`
  - 应用名称：宠物 Lumina
  - 配置必要权限（摄像头、位置、存储等）
  - 配置 Android 打包参数

### 架构与开发心得
1. **数据下沉**：我们在 `views` 层统一获取 Store 状态或请求接口（目前用 Mock 数据），通过 Props 传递给 `components`，实现了完美的单向数据流。
2. **样式解耦**：使用 Tailwind CSS 工具类时，充分复用了 `glass-card`, `no-scrollbar` 等在 `style.css` 中定义的工具，保证了代码优雅度。
3. **TypeScript 赋能**：利用 TS 接口有效规范了卡片所需的数据格式，使组件之间传递数据时拥有完善的类型提示和错误校验。
4. **布局一致性**：认证页面采用统一的布局结构，通过 `fixed inset-0 flex items-center justify-center` 实现内容居中，避免滚动问题。
5. **间距规范**：使用 Tailwind 的间距系统 (`pt-lg`, `mb-lg`, `mt-lg` 等) 保持页面元素间距的一致性，避免硬编码像素值。
