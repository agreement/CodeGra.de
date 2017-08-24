<template>
    <div class="page assignments">
        <loader class="text-center" v-if="loading"></loader>
        <div v-else>
            <h1>Assignments</h1>
            <assignment-list :assignments="assignments" :canSeeHidden="canSeeHidden"></assignment-list>
        </div>
    </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { AssignmentList, Loader } from '@/components';
import moment from 'moment';

import { setPageTitle } from './title';

function formatDate(d) {
    return moment.utc(d, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
}

export default {
    name: 'assignment-list-page',

    data() {
        return {
            loading: true,
            assignments: [],
        };
    },

    mounted() {
        setPageTitle('Assignments');

        Promise.all([
            this.$http.get('/api/v1/assignments/'),
            this.$http.get('/api/v1/login?type=roles'),
        ]).then(([assignments, roles]) => {
            this.loading = false;
            this.assignments = assignments.data.map((assig) => {
                assig.course.role = roles.data[assig.course.id];
                assig.deadline = formatDate(assig.deadline);
                assig.created_at = formatDate(assig.created_at);
                return assig;
            });
        });
    },

    components: {
        AssignmentList,
        Loader,
    },
    methods: {
        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },
    computed: {
        ...mapGetters('user', [
            'canSeeHidden',
        ]),
    },
};
</script>
