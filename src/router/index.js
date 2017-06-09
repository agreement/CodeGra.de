import Vue from 'vue';
import Router from 'vue-router';
import { Assignment, Home, Login } from '@/pages';

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
            path: '/students/:sid/assignment/:aid',
            name: 'Student assignment',
            component: Assignment,
        },
        {
            path: '/code/:id',
            name: 'CodeViewer',
            component: CodeViewer,
            props: {
                editable: true,
            },
        },
    ],
});
