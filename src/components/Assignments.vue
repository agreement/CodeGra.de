<template>
    <ol>
        <li v-for="a in assignments_list">
            <router-link :to="submissionsURL(a)">
                {{a.name}}
            </router-link>
        </li>
    </ol>
</template>

<script>
export default {
    name: 'assignments',

    data() {
        return {
            assignments_list: [],
        };
    },

    mounted() {
        this.$http.get('/api/v1/assignments/').then((data) => {
            this.assignments_list = data.data;
        });
    },

    methods: {
        submissionURL(assignment) {
            return `#/assignments/${assignment.id}/submissions`;
        },
    },
};
</script>

<style lang="less">

</style>
