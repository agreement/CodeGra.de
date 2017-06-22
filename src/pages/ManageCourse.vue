<template>
    <div class="page manage-course">
        <loader v-if="loading"></loader>
        <manage-course v-else :assignments="assignments"></manage-course>
    </div>
</template>

<script>
import { ManageCourse, Loader } from '@/components';
import moment from 'moment';

export default {
    name: 'manage-course-page',

    data() {
        return {
            assignments: [],
            loading: true,
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
    },

    mounted() {
        this.getAssignments();
    },

    methods: {
        getAssignments() {
            this.$http.get(`/api/v1/courses/${this.courseId}/assignments/`).then(({ data }) => {
                this.loading = false;
                for (let i = 0, len = data.length; i < len; i += 1) {
                    data[i].deadline = moment.utc(data[i].deadline, moment.ISO_8601).local().format('YYYY-MM-DDTHH:mm');
                    data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DDTHH:mm');
                }
                this.assignments = data;
            });
        },
    },

    components: {
        Loader,
        ManageCourse,
    },
};
</script>
