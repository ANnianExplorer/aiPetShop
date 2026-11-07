import request from './request'
import type { PageResult, Reminder } from '@/types'

export const reminderApi = {
  add: (data: {
    petId?: string | number; title: string; type?: string; remindTime?: string;
    location?: string; repeatType?: string; notes?: string
  }): Promise<string> => request.post<string>('/reminder/add', data),

  edit: (data: {
    id: string | number; title?: string; type?: string; remindTime?: string;
    location?: string; repeatType?: string; notes?: string
  }): Promise<boolean> => request.post<boolean>('/reminder/edit', data),

  delete: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/reminder/delete', { id }),

  getById: (id: string | number): Promise<Reminder> =>
    request.get<Reminder>('/reminder/get/vo', { params: { id: String(id) } }),

  listPage: (data: {
    current?: number; pageSize?: number; type?: string;
    petId?: string | number; isCompleted?: number; startDate?: string; endDate?: string
  }): Promise<PageResult<Reminder>> => request.post<PageResult<Reminder>>('/reminder/list/page', data),

  toggleComplete: (id: string | number): Promise<boolean> =>
    request.post<boolean>(`/reminder/complete/${String(id)}`),
}
