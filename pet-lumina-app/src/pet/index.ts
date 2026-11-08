/**
 * 桌宠引擎的对外出口。
 *
 * 外壳（DeskPet.vue）只需要 createDeskPetEngine + 少数类型；
 * 片段目录与片段库也导出，方便测试与「预览某个动作」这类扩展。
 */
export { createDeskPetEngine } from './engine'
export type { DeskPetEngine, DeskPetOptions, PetRuntime } from './engine'
export { CATALOG } from './catalog'
export { CLIPS } from './clips'
export { createMotion } from './physics'
export type { Motion, MotionState, PetSize, Viewport } from './physics'
export { publishWorkState, subscribeWorkState } from './signal'
export type { WorkState } from './types'
