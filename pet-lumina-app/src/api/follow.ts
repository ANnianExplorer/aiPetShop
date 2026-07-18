import request from './request'

export const followApi = {
  toggle: (userId: number | string) =>
    request.post(`/follow/${String(userId)}`),

  listFollowers: (data?: { current?: number; pageSize?: number }) =>
    request.post('/follow/list/followers', data || {}),

  listFollowing: (data?: { current?: number; pageSize?: number }) =>
    request.post('/follow/list/following', data || {}),
}
