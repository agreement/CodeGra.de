import Vue from 'vue';
import Router from 'vue-router';
import { Submission, Home, Login } from '@/pages';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Home',
            component: Home,
        },
        {
            path: '/login',
            name: 'Login',
            component: Login,
        },
        {
            path: '/submission/:submissionId',
            name: 'Student assignment',
            component: Submission,
        },
        {
            path: '/submission/:submissionId/files/:fileId',
            name: 'Student assignment',
            component: Submission,
        },
    ],
});
