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

import { setTitle } from './title';

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
        setTitle('Assignments');

        let courseRoles = null;
        let assignments = null;
        // I cant use this.assignments because as soon as this.assignments
        // is set, it will pass its value to the AssignmentList components\
        // which then wont have all the data needed
        const request1 = this.$http.get('/api/v1/assignments/').then(({ data }) => {
            assignments = data;

            return Promise.all(assignments.map((ass) => {
                ass.deadline = formatDate(ass.deadline);
                ass.created_at = formatDate(ass.created_at);
                return this.hasPermission({
                    name: 'can_grade_work',
                    course_id: ass.course_id,
                }).then((response) => {
                    ass.can_grade = response;
                });
            }));
        });
        const request2 = this.$http.get('/api/v1/login?type=roles').then(({ data }) => {
            courseRoles = data;
        });

        Promise.all([request1, request2]).then(() => {
            for (let i = 0, len = assignments.length; i < len; i += 1) {
                const assignment = assignments[i];
                assignment.course_role = courseRoles[assignment.course_id];
            }
            this.loading = false;
            this.assignments = assignments;
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
