<template>
    <div class="page manage-course container-fluid">
        <div v-if="created">
            <b-alert id="success" variant="success" show>
                <center><span>Succesfully created course!</span></center>
            </b-alert>
        </div>
        <div class="row justify-content-center">
            <loader v-if="loading"></loader>
            <manage-course v-else :assignments="assignments"></manage-course>
        </div>
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
            created: false,
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
    },

    mounted() {
        this.created = this.$route.query.created;
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

<style lang="less" scoped>
.row {
    width: 100%;
}
</style>
