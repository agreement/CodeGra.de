import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import CodeViewer from '@/components/CodeViewer';
import FileTree from '@/components/FileTree';
import Login from '@/components/Login';

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
            props: {
                editable: true,
            },
        },
        {
            path: '/login',
            name: 'Login',
            component: Login,
        },
    ],
});
