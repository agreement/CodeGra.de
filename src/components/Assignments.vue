<template>
    <ol>
        <li v-for="a in assignments_list">
            <a v-bind:href="submissionURL(a)">
                {{ a.name }}
            </a>
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
