import request from './request'
import type { LogEntry, PageResult } from '@/types'

export const logApi = {
  add: (data: { petId: string | number; type: string; title: string; content: string; images?: string; tags?: string }): Promise<string> =>
    request.post<string>('/log/add', data),

  edit: (data: { id: string | number; title?: string; content?: string; images?: string; tags?: string }): Promise<boolean> =>
    request.post<boolean>('/log/edit', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/log/delete', { id }),

  getById: (id: string | number): Promise<LogEntry> =>
    request.get<LogEntry>('/log/get/vo', { params: { id: String(id) } }),

  listPage: (data: { current?: number; pageSize?: number; type?: string; petId?: string | number }): Promise<PageResult<LogEntry>> =>
    request.post<PageResult<LogEntry>>('/log/list/page/vo', data),

  toggleLike: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/log/like/${String(id)}`),
}
