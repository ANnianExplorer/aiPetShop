import request from './request'
import type { PageResult, Post, Topic } from '@/types'

export const topicApi = {
  add: (data: { title: string; description?: string; image?: string; category?: string }): Promise<string> =>
    request.post<string>('/topic/add', data),

  edit: (data: { id: string | number; title?: string; description?: string; image?: string; category?: string }): Promise<boolean> =>
    request.post<boolean>('/topic/edit', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/topic/delete', { id }),

  getById: (id: string | number): Promise<Topic> =>
    request.get<Topic>('/topic/get/vo', { params: { id: String(id) } }),

  listPage: (data: { current?: number; pageSize?: number; category?: string; searchText?: string }): Promise<PageResult<Topic>> =>
    request.post<PageResult<Topic>>('/topic/list/page/vo', data),

  toggleFollow: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/topic/follow/${String(id)}`),

  listTopicPosts: (data: { topicId: string | number; current?: number; pageSize?: number }): Promise<PageResult<Post>> =>
    request.post<PageResult<Post>>('/topic/list/page/vo/posts', data),
}
