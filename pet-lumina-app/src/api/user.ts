import request from './request'
import type { User } from '@/types'

export const userApi = {
  getById: (id: string | number): Promise<User> =>
    request.get<User>('/user/get/vo', { params: { id: String(id) } }),

  getLoginUser: (): Promise<User> =>
    request.get<User>('/user/get/login'),

  update: (data: { nickname?: string; bio?: string; location?: string }): Promise<boolean> =>
    request.post<boolean>('/user/update', data),

  updateAvatar: (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<string>('/user/update/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  updatePassword: (data: { oldPassword: string; newPassword: string }): Promise<boolean> =>
    request.post<boolean>('/user/update/password', data),
}
