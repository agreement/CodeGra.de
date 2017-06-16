<template>
    <div class="page assignments">
        <div class="row">
            <loader class="col-md-11 text-center" v-if="loading"></loader>
            <div class="col-md-11" v-else>
                <h1>Assignments</h1>
                <assignment-list :assignments="assignments"></assignment-list>
            </div>
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
