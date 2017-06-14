<template>
    <ol>
        <li v-for="a in assignments_list">
             <router-link :to="{ name: 'assignment_submissions', params: { assignmentId: a.id, }, }">
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
};
</script>

<style lang="less">

</style>
