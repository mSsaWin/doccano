import axios from 'axios'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

class ApiService {
  constructor() {
    this.instance = axios.create({
      baseURL: (process.env.API_URL || '') + process.env.baseUrl
    })
    
    // Add request interceptor to include auth token
    this.instance.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Token ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )
  }

  getAuthToken() {
    // Try to get token from localStorage or cookies
    if (process.client) {
      return localStorage.getItem('auth_token') || this.getCookie('auth_token')
    }
    return null
  }

  getCookie(name) {
    if (process.client) {
      const value = `; ${document.cookie}`
      const parts = value.split(`; ${name}=`)
      if (parts.length === 2) return parts.pop().split(';').shift()
    }
    return null
  }

  setAuthToken(token) {
    if (process.client) {
      localStorage.setItem('auth_token', token)
    }
  }

  clearAuthToken() {
    if (process.client) {
      localStorage.removeItem('auth_token')
    }
  }

  request(method, url, data = {}, config = {}) {
    return this.instance({
      method,
      url,
      data,
      ...config
    })
  }

  get(url, config = {}) {
    return this.request('GET', url, {}, config)
  }

  post(url, data, config = {}) {
    return this.request('POST', url, data, config)
  }

  put(url, data, config = {}) {
    return this.request('PUT', url, data, config)
  }

  patch(url, data, config = {}) {
    return this.request('PATCH', url, data, config)
  }

  delete(url, data = {}, config = {}) {
    return this.request('DELETE', url, data, config)
  }
}

export default new ApiService()
