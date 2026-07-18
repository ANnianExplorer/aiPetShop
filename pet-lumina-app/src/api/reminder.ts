import request from './request'

export const reminderApi = {
  add: (data: {
    petId?: number; title: string; type?: string; remindTime?: string;
    location?: string; repeatType?: string; notes?: string
  }) => request.post('/reminder/add', data),

  edit: (data: {
    id: number; title?: string; type?: string; remindTime?: string;
    location?: string; repeatType?: string; notes?: string
  }) => request.post('/reminder/edit', data),

  delete: (id: number) =>
    request.post('/reminder/delete', { id }),

  getById: (id: number | string) =>
    request.get('/reminder/get/vo', { params: { id: String(id) } }),

  listPage: (data: {
    current?: number; pageSize?: number; type?: string;
    petId?: number; isCompleted?: number; startDate?: string; endDate?: string
  }) => request.post('/reminder/list/page', data),

  toggleComplete: (id: number | string) =>
    request.post(`/reminder/complete/${String(id)}`),
}
