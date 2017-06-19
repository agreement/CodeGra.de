<template>
    <b-form method="post" :action="action" enctype="multipart/form-data">
        <b-form-file name="file" v-model="file"></b-form-file>
        <br> Selected file: {{file && file.name}}
        <br>
        <b-button type="submit">Submit</b-button>
    </b-form>
</template>

<script>
export default {
    name: 'blackboard-uploader',

    props: ['assignmentId'],

    computed: {
        action: function action() {
            return this.assignmentId ? `/api/v1/assignments/${this.assignmentId}/submissions/` : null;
        },
    },

    data() {
        return {
            file: null,
        };
    },
};
</script>