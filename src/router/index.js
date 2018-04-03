import Vue from 'vue';
import Router from 'vue-router';
import store from '@/store';
import {
    ResetPassword,
    LTILaunch,
    Home,
    ManageCourse,
    ManageAssignment,
    Submission,
    Submissions,
    Admin,
} from '@/pages';

import { resetPageTitle } from '@/pages/title';

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
            path: '/reset_password',
            name: 'reset-password',
            component: ResetPassword,
        },
        {
            path: '/lti_launch/',
            name: 'lti-launch',
            component: LTILaunch,
        },
        {
            path: '/admin',
            name: 'admin',
            component: Admin,
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
            path: '/courses/:courseId',
            name: 'manage_course',
            component: ManageCourse,
        },
        {
            path: '/courses/:courseId/assignments/:assignmentId',
            name: 'manage_assignment',
            component: ManageAssignment,
        },
    ],
});

// Stores path of page that requires login when user is not
// logged in, so we can restore it when the user logs in.
let restorePath = '';

const notLoggedInRoutes = new Set([
    'home',
    'lti-launch',
    'reset-password',
]);

router.beforeEach((to, from, next) => {
    // Unset page title. Pages will set title,
    // this is mostly to catch pages that don't.
    resetPageTitle();

    const loggedIn = store.getters['user/loggedIn'];
    if (loggedIn && restorePath) {
        // Reset restorePath before calling (synchronous) next.
        const path = restorePath;
        restorePath = '';
        next({ path });
    } else if (!loggedIn && !notLoggedInRoutes.has(to.name)) {
        store.dispatch('user/verifyLogin').then(() => {
            next();
        }).catch(() => {
            // Store path so we can go to the requested route
            // when the user is logged in.
            restorePath = to.path;
            next('/?sbloc=l');
        });
    } else {
        next();
    }
});

export default router;
