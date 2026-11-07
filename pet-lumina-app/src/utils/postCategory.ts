/**
 * 社区分类：把"展示文案"和"筛选条件"彻底分开。
 *
 * 历史原因，`post.category` 里存的是中文展示名（`猫狗`/`狗狗`/`异宠`/`医疗健康`），
 * 也有新入口写 `daily`。之前的筛选直接拿它跟 `t('community.cat')` 比，
 * 切到英文/日文后两边永远不相等 —— 表现为"切语言后社区一片空白"。
 *
 * 这里的做法：分类归一化成稳定的 key（与语言无关），筛选比 key；
 * 老数据靠 `LEGACY_LABELS` 兜底，未知值归到 `other`（不冒充任何一类）。
 */

export type PostCategory = 'daily' | 'cat' | 'dog' | 'exotic' | 'medical' | 'other'

/** 顶部分类栏的顺序：全部 + 五个真实分类 */
export const POST_CATEGORY_TABS = ['all', 'daily', 'cat', 'dog', 'exotic', 'medical'] as const
export type PostCategoryTab = (typeof POST_CATEGORY_TABS)[number]

const LEGACY_LABELS: Record<string, PostCategory> = {
  // 英文 key（新数据）
  daily: 'daily',
  cat: 'cat',
  dog: 'dog',
  exotic: 'exotic',
  medical: 'medical',
  // 中文展示名（历史数据）
  日常: 'daily',
  猫咪: 'cat',
  猫狗: 'cat',
  狗狗: 'dog',
  异宠: 'exotic',
  医疗: 'medical',
  医疗健康: 'medical'
}

export function normalizeCategory(raw: string | null | undefined): PostCategory {
  const key = (raw ?? '').trim().toLowerCase()
  if (!key) return 'other'
  return LEGACY_LABELS[key] ?? LEGACY_LABELS[(raw ?? '').trim()] ?? 'other'
}

/**
 * 某条帖子是否属于当前 tab。
 * `all` 永远命中；其余按归一化后的 key 比较，未知分类只在 `all` 里出现。
 */
export function matchesCategory(rawCategory: string | null | undefined, tab: PostCategoryTab): boolean {
  if (tab === 'all') return true
  return normalizeCategory(rawCategory) === tab
}
