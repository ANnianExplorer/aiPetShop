import request from './request'
import type { LoginUser } from '@/types'

export const authApi = {
  login: (data: { phone: string; password: string }): Promise<LoginUser> =>
    request.post<LoginUser>('/auth/login', data),

  register: (data: { phone: string; code: string; password: string }): Promise<LoginUser> =>
    request.post<LoginUser>('/auth/register', data),

  sendCode: (phone: string): Promise<boolean> =>
    request.post<boolean>('/auth/send-code', { phone }),

  resetPassword: (data: { phone: string; code: string; password: string }): Promise<boolean> =>
    request.post<boolean>('/auth/reset-password', data),

  getCurrentUser: (): Promise<LoginUser> =>
    request.get<LoginUser>('/auth/current'),

  logout: (): Promise<boolean> =>
    request.post<boolean>('/auth/logout'),
}
