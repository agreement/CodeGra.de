import Vue from 'vue';
import Router from 'vue-router';
import { Assignments, Submission, Home, Login } from '@/pages';
import CodeUploader from '@/components/CodeUploader';

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
        {
            path: '/students/:studentId/assignments/',
            name: 'Student assignments',
            component: Assignments,
        },
        {
            path: '/upload',
            name: 'CodeUploader',
            component: CodeUploader,
        },
    ],
});
