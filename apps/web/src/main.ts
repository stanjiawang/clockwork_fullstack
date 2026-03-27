import { createApp } from 'vue'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles.css'

const app = createApp(App)
const pinia = createPinia()
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

app.use(pinia)
app.use(VueQueryPlugin, { queryClient })
app.mount('#app')
