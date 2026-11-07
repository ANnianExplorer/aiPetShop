import request from './request'

/**
 * 违规管理（BACKLOG E9）
 */
export const violationApi = {
  // 敏感词
  listWords: (data: any) => request.post('/admin/violation/word/list/page', data),
  addWord: (data: any) => request.post('/admin/violation/word/add', data),
  updateWord: (data: any) => request.post('/admin/violation/word/update', data),
  deleteWord: (id: number | string) => request.post('/admin/violation/word/delete', { id }),

  // 违规记录
  listRecords: (data: any) => request.post('/admin/violation/record/list/page', data),
  handleRecord: (id: number | string) => request.post('/admin/violation/record/handle', { id }),
}
