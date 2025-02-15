import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhTw from 'element-plus/dist/locale/zh-tw.mjs'
import App from './App.vue'
import router from './router'
import '@mdi/font/css/materialdesignicons.css'
// import '@material-icons/font'

// 引入 Toast
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css"

const app = createApp(App)
const pinia = createPinia()

// Toast 配置
const toastOptions = {
    position: "top-right",
    timeout: 3000,
    closeOnClick: true,
    pauseOnFocusLoss: true,
    pauseOnHover: true,
    draggable: true,
    draggablePercent: 0.6,
    showCloseButtonOnHover: false,
    hideProgressBar: true,
    closeButton: "button",
    icon: true,
    rtl: false
}

// 設置 Vue 應用程序的性能模式，非生產環境下開啟
// 加入性能優化配置
app.config.performance = process.env.NODE_ENV !== 'production'

// 註冊所有圖標
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(Toast, toastOptions)
app.use(ElementPlus, {
  locale: zhTw,
})

app.mount('#app')
