<template>
    <div class="page assignment">
        <code-viewer></code-viewer>
        <file-tree></file-tree>
    </div>
</template>

<script>
export default {
    name: 'assignment-page',

    data() {
        return {
            studentId: this.$route.params.sid,
            assignmentId: this.$route.params.aid,
        };
    },

    mounted() {
        if (!this.assignment) {
            this.getStudentAssignment();
        }
    },

    methods: {
        getStudentAssignment() {
            this.$http.get(`/api/v1/students/${this.studentId}/assignments/${this.assignmentId}`).then((data) => {
                Object.assign(this, data.body);
            });
        },
    },
};
</script>

<style lang="less">

</style>
