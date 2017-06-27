<template>
    <div class="page assignments">
        <loader class="text-center" v-if="loading1 || loading2"></loader>
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

export default {
    name: 'assignment-list-page',

    data() {
        return {
            loading1: true,
            loading2: true,
            assignments: [],
            course_roles: [],
        };
    },

    mounted() {
        const request1 = this.$http.get('/api/v1/assignments/').then(({ data }) => {
            const promises = [];
            for (let i = 0, len = data.length; i < len; i += 1) {
                data[i].deadline = moment.utc(data[i].deadline, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DD HH:mm');
                const promise = this.hasPermission({ name: 'can_grade_work', course_id: data[i].course_id });
                promise.then((response) => { data[i].can_grade = response; });
                promises.push(promise);
            }
            Promise.all(promises).then(() => {
                this.assignments = data;
                this.loading1 = false;
            });
        });
        const request2 = this.$http.get('/api/v1/login?type=roles').then(({ data }) => {
            this.course_roles = data;
            this.loading2 = false;
        });
        Promise.all([request1, request2]).then(() => {
            for (let i = 0, len = this.assignments.length; i < len; i += 1) {
                const assignment = this.assignments[i];
                assignment.course_role = this.course_roles[assignment.course_id];
            }
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
