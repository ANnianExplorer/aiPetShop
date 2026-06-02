import request from './request'

export const userApi = {
  getById: (id: string | number) =>
    request.get('/user/get/vo', { params: { id } }),

  getLoginUser: () =>
    request.get('/user/get/login'),

  update: (data: { nickname?: string; bio?: string; location?: string }) =>
    request.post('/user/update', data),

  updateAvatar: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/user/update/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  updatePassword: (data: { oldPassword: string; newPassword: string }) =>
    request.post('/user/update/password', data),
}
