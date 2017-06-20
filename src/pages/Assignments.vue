<template>
    <div class="page assignments">
        <div class="row justify-content-center">
            <loader class="col-md-10 text-center" v-if="loading"></loader>
            <div class="col-md-10" v-else>
                <h1>Assignments</h1>
                <assignment-list :assignments="assignments" :canSeeHidden="canSeeHidden"></assignment-list>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
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
    computed: {
        ...mapGetters('user', [
            'canSeeHidden',
        ]),
    },
};
</script>
