import Vue from 'vue';
import Router from 'vue-router';
import store from '@/store';
import { LTILaunch, Assignments, Courses, Home, Login, ManageCourse, Submission, Submissions, User } from '@/pages';
import { NewCourse, UsersManager, RubricEditor } from '@/components';

import { setTitle } from '@/pages/title';

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
            path: '/lti_launch/',
            name: 'lti-launch',
            component: LTILaunch,
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
        {
            path: '/manage-permissions/:courseId/',
            name: 'manage-permissions',
            component: UsersManager,
        },
        {
            path: '/edit-rubric/:assignmentId',
            name: 'edit-rubric',
            component: RubricEditor,
        },
    ],
});

// Stores path of page that requires login when user is not
// logged in, so we can restore it when the user logs in.
let restorePath = '';

router.beforeEach((to, from, next) => {
    // Unset page title. Pages will set  title,
    // this is mostly to catch pages that don't.
    setTitle();

    const loggedIn = store.getters['user/loggedIn'];
    if (loggedIn && restorePath) {
        // Reset restorePath before calling (synchronous) next.
        const path = restorePath;
        restorePath = '';
        next({ path });
    } else if (!loggedIn && to.path !== '/login' && to.name !== 'home' && to.name !== 'lti-launch') {
        store.dispatch('user/verifyLogin').then(() => {
            next();
        }).catch(() => {
            // Store path so we can go to the requested route
            // when the user is logged in.
            restorePath = to.path;
            next('/login');
        });
    } else if (loggedIn && to.name === 'login') {
        next('/');
    } else {
        next();
    }
});

export default router;
