<div align="center">

# PetLumina - 宠物生活管理 App

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3.5-4FC08D.svg" alt="Vue 3" />
  <img src="https://img.shields.io/badge/Vite-6.0-646CFF.svg" alt="Vite" />
  <img src="https://img.shields.io/badge/TypeScript-5.6-blue.svg" alt="TypeScript" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Pinia-2.3-yellowgreen.svg" alt="Pinia" />
  <img src="https://img.shields.io/badge/Vant-4.9-07c160.svg" alt="Vant" />
</p>

[English](#) | [简体中文](README.md)

**面向宠物主人的智能生活管理与社区互动移动 Web App**

<br />

</div>

## 页面预览

<div align="center">

| 登录页 | 首页 | 生活记录 |
|:---:|:---:|:---:|
| <img src="../image/登录页.png" width="240" /> | <img src="../image/首页.png" width="240" /> | <img src="../image/生活记录页面.png" width="240" /> |

| 宠物社区 | 饮食健康 | 个人中心 |
|:---:|:---:|:---:|
| <img src="../image/宠物社区页面.png" width="240" /> | <img src="../image/饮食健康页面.png" width="240" /> | <img src="../image/个人中心页面.png" width="240" /> |

</div>

## 核心亮点

| 模块 | 能力说明 |
| --- | --- |
| **首页仪表盘** | 宠物状态概览、今日提醒、快捷操作入口、社区动态流 |
| **生活记录** | 图文记录宠物日常、标签分类、图片轮播、分享功能 |
| **宠物社区** | 话题浏览与发布、帖子详情、评论互动、点赞收藏、用户关注 |
| **健康管理** | 健康数据录入、周度指标追踪、健康计划制定、趋势可视化 |
| **日程提醒** | 提醒创建与管理、按日期分组、通知中心 |
| **个人中心** | 用户资料编辑、宠物档案管理、账号安全、通用设置 |
| **认证系统** | 登录、注册、密码重置、验证码校验 |

## 快速体验

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 启动开发服务器 (默认 http://localhost:5173) |
| `npm run build` | 类型检查 + 生产构建 |
| `npm run preview` | 预览生产构建 |

## 项目源码

| 项目模块 | 路径 | 说明 |
| --- | --- | --- |
| **前端应用** | `pet-lumina-app/` | Vue 3 + Vite + TypeScript 移动 Web App |
| **HBuilder 项目** | `ai-pet-app/` | 5+App 打包配置，用于生成 Android APK |

## 技术架构

**前端架构**
- **核心框架**: Vue 3 (Composition API + `<script setup>`) + Vite 6
- **类型系统**: TypeScript 5.6 (严格模式)
- **状态管理**: Pinia (用户信息、宠物档案、健康数据)
- **UI 组件库**: Vant 4 (移动端组件)
- **样式方案**: Tailwind CSS 3 + 自定义设计令牌 (Material Design 3 色彩)
- **路由控制**: Vue Router 4 (Hash 模式，适配 5+App)
- **工程化**: 路径别名 `@/`、组件懒加载、代码分割

**设计系统**
- **玻璃拟态 UI**: `glass-card` 工具类 (backdrop-filter + 半透明背景)
- **响应式布局**: 移动优先，适配不同屏幕尺寸
- **动画系统**: fade-in、slide-up、pulse 等过渡动画
- **字体系统**: Plus Jakarta Sans + Be Vietnam Pro

## 目录结构

```text
pet-lumina-app/
├── src/
│   ├── api/          # 接口请求层
│   ├── assets/       # 静态资源
│   ├── components/   # 公共/业务组件
│   │   ├── common/   # 全局通用组件
│   │   ├── home/     # 首页组件
│   │   ├── lifelog/  # 生活记录组件
│   │   ├── community/# 社区组件
│   │   ├── wellness/ # 健康组件
│   │   └── profile/  # 个人中心组件
│   ├── composables/  # 组合式函数
│   ├── layout/       # 页面布局组件
│   ├── router/       # 路由配置
│   ├── stores/       # Pinia 状态管理
│   ├── types/        # TypeScript 类型定义
│   ├── utils/        # 工具函数
│   └── views/        # 页面级组件
│       ├── auth/     # 认证页面
│       ├── community/# 社区页面
│       ├── home/     # 首页
│       ├── lifelog/  # 生活记录页面
│       ├── pet/      # 宠物页面
│       ├── profile/  # 个人中心页面
│       ├── schedule/ # 日程页面
│       └── wellness/ # 健康页面
├── vite.config.ts    # Vite 构建配置
├── tailwind.config.js
└── package.json
```

## HBuilder APK 打包

1. 构建项目：`cd pet-lumina-app && node ./node_modules/vite/bin/vite.js build`
2. 构建产物自动输出到 `ai-pet-app/` 目录
3. 在 HBuilder 中打开 `ai-pet-app/` 目录
4. 右键项目 → **发行 → 发行为原生安装包** → 云打包生成 APK

## 更新日志 (Changelog)

### 1.0.0 (2026-05-01)

**基础工程搭建**
- Vue 3 + Vite + TypeScript 项目初始化
- Tailwind CSS 设计系统集成 (Material Design 3 色彩令牌)
- 全局底部导航布局 (`MainLayout`)

**页面开发**
- 认证系统：登录、注册、密码重置
- 首页仪表盘：宠物状态、提醒、快捷操作、社区动态
- 生活记录：列表、详情页、图片轮播
- 宠物社区：话题、帖子、评论、用户主页
- 健康管理：数据录入、周度指标、计划制定
- 日程提醒：列表、添加、通知中心
- 个人中心：资料编辑、设置、帮助反馈

**组件开发**
- 评论弹窗、表情选择器、分享弹窗、Toast 提示
- 各页面业务组件拆分

**APK 打包适配**
- Vite 构建配置优化 (相对路径、输出目录)
- 路由改为 Hash 模式 (适配 5+App)
- manifest.json 配置

---

<div align="center">
  <p>内部项目 | 持续迭代中</p>
</div>
