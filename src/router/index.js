import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import FileTree from '@/components/FileTree';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Hello',
            component: Hello,
        },
        {
            path: '/dir/:path',
            name: 'FileTree',
            component: FileTree,
        },
    ],
});
