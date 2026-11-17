/**
 * 触发浏览器下载一段文本。
 *
 * 单独抽出来是为了可测：jsdom 没有 `URL.createObjectURL`，
 * 组件测试里把这个模块 mock 掉即可，不用在测试里补浏览器 API。
 */
export function downloadTextFile(filename: string, content: string, mime = 'application/json;charset=utf-8'): void {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
