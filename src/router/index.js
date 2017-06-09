import Vue from 'vue';
import Router from 'vue-router';
import Hello from '@/components/Hello';
import GradingAssignment from '@/components/GradingAssignment';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            name: 'Hello',
            component: Hello,
        },
        {
            path: '/GradingAssignment/:id',
            name: 'GradingAssignment',
            component: GradingAssignment,
        },
    ],
});
