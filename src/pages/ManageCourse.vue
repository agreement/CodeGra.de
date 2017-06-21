<template>
    <div class="page manage-course">
        <loader v-if="loading"></loader>
        <manage-course v-else :assignments="assignments"></manage-course>
    </div>
</template>

<script>
import { ManageCourse, Loader } from '@/components';

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
