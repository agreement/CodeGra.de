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
import { mapGetters } from 'vuex';
import { AssignmentList, Loader } from '@/components';
import moment from 'moment';

export default {
    name: 'assignment-list-page',

    data() {
        return {
            loading: true,
            assignments: [],
        };
    },

    mounted() {
        this.$http.get('/api/v1/assignments/').then(({ data }) => {
            this.loading = false;
            for (let i = 0, len = data.length; i < len; i += 1) {
                data[i].deadline = moment.utc(data[i].deadline, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
            }
            this.assignments = data;
        });
    },

    components: {
        AssignmentList,
        Loader,
    },
    computed: {
        ...mapGetters('user', [
            'canSeeHidden',
        ]),
    },
};
</script>
