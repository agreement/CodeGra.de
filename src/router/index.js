import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import CodeViewer from '@/components/CodeViewer';

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
            data: {
                code: 'test',
                feedback: [],
            },
        },
    ],
});
