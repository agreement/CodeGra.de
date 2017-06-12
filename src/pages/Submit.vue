<template>
    <div class="page submit">
        <h1>Submit work for assignment {{ assignmentId }}</h1>
        <code-uploader v-bind:assignmentId="assignmentId"></code-uploader>
    </div>
</template>

<script>
import { CodeUploader } from '@/components';

export default {
    name: 'submit-page',

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
        };
    },

    components: {
        CodeUploader,
    },
};
</script>
