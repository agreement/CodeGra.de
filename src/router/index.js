import Vue from 'vue';
import Router from 'vue-router';
import HomePage from '@/components/HomePage';
import Login from '@/components/Login';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'HomePage',
            component: HomePage,
        },
        {
            path: '/login',
            name: 'Login',
            component: Login,
        },
    ],
});
