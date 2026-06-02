import request from './request'

export const authApi = {
  login: (data: { phone: string; password: string }) =>
    request.post('/auth/login', data),
  logout: () => request.post('/auth/logout'),
  getCurrent: () => request.get('/auth/current'),
}
