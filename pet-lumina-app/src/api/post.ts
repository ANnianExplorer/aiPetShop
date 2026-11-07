import request from './request'
import type { PageResult, Post } from '@/types'

export const postApi = {
  add: (data: { content: string; images?: string; tags?: string; category?: string; topicId?: string | number }): Promise<string> =>
    request.post<string>('/post/add', data),

  edit: (data: { id: string | number; content?: string; images?: string; tags?: string; category?: string }): Promise<boolean> =>
    request.post<boolean>('/post/edit', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/post/delete', { id }),

  getById: (id: string | number): Promise<Post> =>
    request.get<Post>('/post/get/vo', { params: { id: String(id) } }),

  listPage: (data: { current?: number; pageSize?: number; category?: string; searchText?: string; topicId?: string | number; authorId?: string | number }): Promise<PageResult<Post>> =>
    request.post<PageResult<Post>>('/post/list/page/vo', data),

  toggleLike: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/post/like/${String(id)}`),

  toggleFavorite: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/post/favorite/${String(id)}`),
}
