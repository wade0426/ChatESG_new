import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
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

app.use(pinia)
app.use(router)
app.use(Toast, toastOptions)

app.mount('#app')
