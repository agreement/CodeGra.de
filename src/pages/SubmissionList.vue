<template>
    <div class="page submission-list">
        <submission-list v-bind:assignmentId="assignmentId"></submission-list>
    </div>
</template>

<script>
import { SubmissionList } from '@/components';

export default {
    name: 'submission-list-page',

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
        };
    },

    components: {
        SubmissionList,
    },
};
</script>
