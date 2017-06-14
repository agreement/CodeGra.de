<template>
    <ol>
        <li v-for="s in submissions">
            <router-link :to="submissionURL(s)">
                <!-- TODO: Moet denk ik `s.date` worden -->
                {{ s.id }}
            </router-link>
        </li>
    </ol>
</template>

<script>
export default {
    name: 'submission-list',

    props: {
        assignmentId: {
            type: Number,
            default: 0,
        },
    },

    data() {
        return {
            submissions: [],
        };
    },

    mounted() {
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/works`).then((data) => {
            this.submissions = data.data;
        });
    },

    methods: {
        submissionURL(submission) {
            return `#/assignments/${this.assignmentId}/submissions/${submission.id}/`;
        },
    },
};
</script>

<style lang="less">

</style>
