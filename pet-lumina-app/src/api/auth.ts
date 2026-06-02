import request from './request'

export const authApi = {
  login: (data: { phone: string; password: string }) =>
    request.post('/auth/login', data),

  register: (data: { phone: string; code: string; password: string }) =>
    request.post('/auth/register', data),

  sendCode: (phone: string) =>
    request.post('/auth/send-code', { phone }),

  resetPassword: (data: { phone: string; code: string; password: string }) =>
    request.post('/auth/reset-password', data),

  getCurrentUser: () =>
    request.get('/auth/current'),

  logout: () =>
    request.post('/auth/logout'),
}
