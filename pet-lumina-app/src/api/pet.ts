import request from './request'
import type { PageResult, Pet } from '@/types'

export const petApi = {
  add: (data: { name: string; type: string; breed?: string; age?: string; notes?: string; avatar?: string }): Promise<string> =>
    request.post<string>('/pet/add', data),

  edit: (data: { id: string | number; name?: string; breed?: string; age?: string; notes?: string; avatar?: string }): Promise<boolean> =>
    request.post<boolean>('/pet/edit', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/pet/delete', { id }),

  getById: (id: string | number): Promise<Pet> =>
    request.get<Pet>('/pet/get/vo', { params: { id: String(id) } }),

  list: (): Promise<Pet[]> =>
    request.get<Pet[]>('/pet/list'),

  listPage: (data: { current?: number; pageSize?: number; name?: string; type?: string }): Promise<PageResult<Pet>> =>
    request.post<PageResult<Pet>>('/pet/list/page/vo', data),
}
