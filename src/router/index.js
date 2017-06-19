import Vue from 'vue';
import Router from 'vue-router';
import { Assignments, Submission, Home, Login, Submit, Submissions } from '@/pages';

Vue.use(Router);

export default new Router({
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
        },
        {
            path: '/course/:courseId/assignments/:assignmentId/submissions/:submissionId',
            name: 'submission',
            component: Submission,
        },
        {
            path: '/course/:courseId/assignments/:assignmentId/submissions/:submissionId/files/:fileId',
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
            path: '/course/:courseId/assignments/:assignmentId/submit',
            name: 'assignment_submit',
            component: Submit,
        },
    ],
});
