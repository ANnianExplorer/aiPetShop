import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite';
import { fileURLToPath, URL } from 'node:url';
export default defineConfig({
    plugins: [
        vue(),
        VueI18nPlugin({
            include: fileURLToPath(new URL('./src/locales/**', import.meta.url)),
            runtimeOnly: false,
            compositionOnly: true,
        }),
    ],
    base: './',
    build: {
        outDir: 'dist',
        emptyOutDir: true
    },
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    }
});
