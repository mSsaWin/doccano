import ApiService from '@/services/api.service'

export class APIAuthRepository {
  constructor(private readonly request = ApiService) {}

  async login(username: string, password: string): Promise<string> {
    const url = `/auth/login/`
    const response = await this.request.post(url, { username, password })
    
    // Extract token from response
    const token = response.data.key || response.data.token
    if (token) {
      this.request.setAuthToken(token)
    }
    
    return token
  }

  async logout(): Promise<void> {
    const url = '/auth/logout/'
    await this.request.post(url)
    this.request.clearAuthToken()
  }

  async socialLink(): Promise<any[]> {
    const url = '/social/links/'
    const response = await this.request.get(url)
    return response.data
  }
}
