import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import CodeViewer from '@/components/CodeViewer';
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
            path: '/code/:id',
            name: 'CodeViewer',
            component: CodeViewer,
        },
        {
            path: '/dir/:path',
            name: 'FileTree',
            component: FileTree,
        },
    ],
});
