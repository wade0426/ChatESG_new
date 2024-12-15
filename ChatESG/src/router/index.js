import { createRouter, createWebHistory } from 'vue-router'
import Home from '../components/home.vue'
import Login from '../components/login.vue'
import Signup from '../components/signup.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'Home',
            component: Home
        },
        {
            path: '/login',
            name: 'Login',
            component: Login
        },
        {
            path: '/signup',
            name: 'Signup',
            component: Signup
        }
    ]
})

export default router 