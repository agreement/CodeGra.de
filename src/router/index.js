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
            path: '/students/:sid/assignments/:aid',
            name: 'Student assignment',
            component: Assignment,
        },
        {
            path: '/students/:sid/assignments/:aid/files/:fid',
            name: 'Student assignment',
            component: Assignment,
        },
    ],
});
