import request from './request'

export const fileApi = {
  /**
   * 上传图片
   * @param file 图片文件
   * @param category 分类: post/image, pet/image, log/image, common
   */
  uploadImage(file: File, category: string = 'common'): Promise<string> {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<string>('/file/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { category },
    })
  },

  /**
   * 通用文件上传
   */
  upload(file: File, category: string = 'common'): Promise<string> {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<string>('/file/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { category },
    })
  },
}
