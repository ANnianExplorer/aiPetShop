import request from './request'

export const commentApi = {
  add: (data: { postId: number | string; content: string; parentId?: number }) =>
    request.post('/comment/add', data),

  delete: (id: number) =>
    request.post('/comment/delete', { id }),

  listPage: (data: { postId: number | string; current?: number; pageSize?: number }) =>
    request.post('/comment/list/page/vo', data),

  toggleLike: (id: number | string) =>
    request.post(`/comment/like/${String(id)}`),
}
