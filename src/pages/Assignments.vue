<template>
    <div class="page assignments">
        <loader class="text-center" v-if="loading"></loader>
        <div v-else>
            <h1>Assignments</h1>
            <assignment-list :assignments="assignments"></assignment-list>
        </div>
    </div>
</template>

<script>
import { AssignmentList, Loader } from '@/components';

export default {
    name: 'assignment-list-page',

    data() {
        return {
            loading: true,
            assignments: [],
        };
    },

    mounted() {
        this.$http.get('/api/v1/assignments/').then(({ data }) => {
            this.loading = false;
            this.assignments = data;
        });
    },

    components: {
        AssignmentList,
        Loader,
    },
};
</script>
