import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // API 호출을 백엔드로 프록시 (개발 환경)
      // 프로덕션에서는 nginx가 프록시 역할을 함
    }
  }
})
