import request from './request'
import type { Comment, PageResult } from '@/types'

export const commentApi = {
  add: (data: { postId: string | number; content: string; parentId?: string | number }): Promise<string> =>
    request.post<string>('/comment/add', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/comment/delete', { id }),

  listPage: (data: { postId: string | number; current?: number; pageSize?: number }): Promise<PageResult<Comment>> =>
    request.post<PageResult<Comment>>('/comment/list/page/vo', data),

  toggleLike: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/comment/like/${String(id)}`),
}
