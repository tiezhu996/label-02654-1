import request from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export const authApi = {
  login: (params: LoginParams): Promise<LoginResponse> => {
    return request.post('/auth/login', params)
  },

  getMe: (): Promise<User> => {
    return request.get('/auth/me')
  },
}
