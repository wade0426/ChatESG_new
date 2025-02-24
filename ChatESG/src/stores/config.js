import { defineStore } from 'pinia'
import { API_BASE_URL, API_BASE_URL2 } from '@/config/env'

export const useConfigStore = defineStore('config', {
  state: () => ({
    apiBaseUrl: API_BASE_URL,
    apiBaseUrl2: API_BASE_URL2
  }),
})