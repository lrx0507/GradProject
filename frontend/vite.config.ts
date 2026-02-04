import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
// 新增：按需导入插件
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
    // 新增：自动导入 API 和组件
    AutoImport({
      imports: ['vue'], // 自动导入 Vue 的 ref, reactive 等
      resolvers: [ElementPlusResolver()], // 自动解析 Element Plus 组件和指令
    }),
    Components({
      resolvers: [ElementPlusResolver()], // 自动注册 Element Plus 组件
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})