import Vue from 'vue';
import Router from 'vue-router';
import store from '@/store';
import { Assignments, Home, Login, ManageCourse, Submission, Submissions, User } from '@/pages';

Vue.use(Router);

const router = new Router({
    mode: 'history',

    routes: [
        {
            path: '/',
            name: 'home',
            component: Home,
        },
        {
            path: '/login',
            name: 'login',
            component: Login,
        },
        {
            path: '/logout',
            name: 'logout',
            redirect: { name: 'home' },
        },
        {
            path: '/me',
            name: 'me',
            component: User,
        },
        {
            path: '/courses/:courseId/assignments/:assignmentId/submissions/:submissionId',
            name: 'submission',
            component: Submission,
        },
        {
            path: '/courses/:courseId/assignments/:assignmentId/submissions/:submissionId/files/:fileId',
            name: 'submission_file',
            component: Submission,
        },
        {
            path: '/courses/:courseId/assignments/:assignmentId/submissions/',
            name: 'assignment_submissions',
            component: Submissions,
        },
        {
            path: '/assignments/',
            name: 'assignments',
            component: Assignments,
        },
        {
            path: '/courses/:courseId',
            name: 'assignment_manage',
            component: ManageCourse,
        },
    ],
});

router.beforeEach((to, from, next) => {
    if (!store.getters['user/loggedIn'] && to.path !== '/login') {
        store.dispatch('user/verifyLogin').then(() => {
            next();
        }).catch(() => {
            next('/login');
        });
    } else if (store.getters['user/loggedIn'] && to === '/login') {
        next('/');
    } else {
        next();
    }
});

export default router;
