import Vue from 'vue';
import Router from 'vue-router';
import store from '@/store';
import { Assignments, Courses, Home, Login, ManageCourse, Submission, Submissions, User } from '@/pages';
import { NewCourse } from '@/components';

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
            path: '/courses/',
            name: 'courses',
            component: Courses,
        },
        {
            path: '/courses/:courseId',
            name: 'assignment_manage',
            component: ManageCourse,
        },
        {
            path: '/add-course',
            name: 'new-course',
            component: NewCourse,
        },
    ],
});

router.beforeEach((to, from, next) => {
    if (!store.getters['user/loggedIn'] && to.path !== '/login') {
        next('/login');
        return;
    }

    if (store.getters['user/loggedIn'] && to === '/login') {
        next('/');
        return;
    }

    next();
});

export default router;
