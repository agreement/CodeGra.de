import Vue from 'vue';
import Router from 'vue-router';
import { Assignments, Submission, Home, Login, Submit, SubmissionList } from '@/pages';
import { DivideSubmissions } from '@/components';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Home',
            component: Home,
        },
        {
            path: '/login/',
            name: 'Login',
            component: Login,
        },
        {
            path: '/assignments/:assignmentId/submissions/:submissionId/',
            name: 'Assignment submission',
            component: Submission,
        },
        {
            path: '/assignments/:assignmentId/submissions/:submissionId/files/:fileId/',
            name: 'Assignment submission file',
            component: Submission,
        },
        {
            path: '/assignments/:assignmentId/submissions/',
            name: 'Assignment submissions',
            component: SubmissionList,
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
        {
            path: '/assignments/:assignmentId/divide-submissions',
            name: 'Divide Submissions',
            component: DivideSubmissions,
        },
    ],
});
