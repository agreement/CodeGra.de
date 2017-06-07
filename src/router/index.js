import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import CodeUploader from '@/components/CodeUploader';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Hello',
            component: Hello,
        },
        {
            path: '/upload',
            name: 'CodeUploader',
            component: CodeUploader,
        },
    ],
});
