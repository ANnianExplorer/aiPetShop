# AGENTS.md - PetLumina Development Guide

## Project Overview
- **Main App**: `pet-lumina-app/` - Vue 3 + Vite + TypeScript mobile web app for pet management
- **Entry Point**: `pet-lumina-app/index.html`

## Key Commands
```bash
# Frontend dev server
cd pet-lumina-app && npm run dev

# Build (typecheck + build)
cd pet-lumina-app && npm run build

# Preview build
cd pet-lumina-app && npm run preview
```

## Type Checking
- Uses `vue-tsc -b` for TypeScript + Vue template checking
- Strict mode enabled in `tsconfig.json`
- Run `npm run build` to verify type safety before commits

## Architecture (pet-lumina-app)
- **Framework**: Vue 3 (Composition API), Vite, TypeScript
- **State**: Pinia (`src/stores/user.ts`)
- **Routing**: Vue Router with lazy-loaded routes
- **UI**: Vant 4 + Tailwind CSS
- **Path Alias**: `@/` maps to `src/`

## Design System
- Tailwind colors defined in `tailwind.config.js` (Material Design 3 tokens)
- Custom utilities in `src/style.css` (e.g., `glass-card`, `no-scrollbar`)

## Code Conventions
- Views in `src/views/` dispatch to components in `src/components/`
- Types in `src/types/index.ts` - avoid `any`
- Use Pinia store (`src/stores/user.ts`) for cross-component state

## Existing Docs
- See `pet-lumina-app/AGENT.md` for detailed frontend development history and migration notes

## Notes
- Backend directory is currently empty (placeholder for future API)
- All data is mocked in the Pinia store - no actual API calls implemented yet

## GitHub Pages
- 构建输出目录：`pet-lumina-app/dist`（已在仓库中）
- CI workflow: `.github/workflows/deploy.yml`
- 访问地址：`https://ANnianExplorer.github.io/aiPetShop/`

## HBuilder 打包 APK
修改 `vite.config.ts` 将构建输出改为 HBuilder 可用目录：
```ts
build: {
  outDir: '../ai-pet-app',
  emptyOutDir: false
}
```
打包后用 HBuilder 打开 `ai-pet-app/` 目录选择"5+App"类型即可云打包生成 APK。