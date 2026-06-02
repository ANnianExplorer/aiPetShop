import request from './request'

export const commentApi = {
  add: (data: { postId: number; content: string; parentId?: number }) =>
    request.post('/comment/add', data),

  delete: (id: number) =>
    request.post('/comment/delete', { id }),

  listPage: (data: { postId: number; current?: number; pageSize?: number }) =>
    request.post('/comment/list/page/vo', data),
}
