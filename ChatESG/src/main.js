import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@mdi/font/css/materialdesignicons.css'
// import '@material-icons/font'

const app = createApp(App)
const pinia = createPinia()

// 設置 Vue 應用程序的性能模式，非生產環境下開啟
// 加入性能優化配置
app.config.performance = process.env.NODE_ENV !== 'production'

app.use(pinia)
app.use(router)

app.mount('#app')
