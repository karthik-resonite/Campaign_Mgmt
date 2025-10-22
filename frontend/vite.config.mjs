import { fileURLToPath, URL } from 'node:url';
import fs from 'fs'
import { PrimeVueResolver } from '@primevue/auto-import-resolver';
import vue from '@vitejs/plugin-vue';
import Components from 'unplugin-vue-components/vite';
import { defineConfig } from 'vite';
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    optimizeDeps: {
        noDiscovery: true,
        include: ['quill']
    },
    plugins: [
        vue(),
        Components({
            resolvers: [PrimeVueResolver()]
        })
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    css: {
        preprocessorOptions: {
            scss: {
                api: 'modern-compiler'
            }
        }
    },
    server: {
    host: true,
    port: 2053,
    https: {
      key: fs.readFileSync(path.resolve(__dirname, 'redsocks.mu.key')),
      cert: fs.readFileSync(path.resolve(__dirname, 'redsocks_mu.pem')),
    },
  }
});
