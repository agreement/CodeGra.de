import Vue from 'vue';
import Router from 'vue-router';
import { Assignments, Submission, Home, Login, Submit } from '@/pages';

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
            path: '/assignments/',
            name: 'Assignments',
            component: Assignments,
        },
        {
            path: '/assignments/:assignmentId/submit/',
            name: 'Submit assignment',
            component: Submit,
        },
    ],
});
