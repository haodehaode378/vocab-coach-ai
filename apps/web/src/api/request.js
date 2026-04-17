import axios from 'axios'
import { useAppStore } from '../stores/app.js'

const request = axios.create({
  baseURL: '/',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const store = useAppStore()
  if (store.userEmail) {
    const sep = config.url.includes('?') ? '&' : '?'
    config.url = `${config.url}${sep}user_email=${encodeURIComponent(store.userEmail)}`
  }
  return config
})

export default request
