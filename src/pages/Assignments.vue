<template>
    <div class="page assignments">
        <div class="row">
            <div class="text-center loader col-md-11" v-if="loading">
                <icon name="refresh" scale="4" spin></icon>
            </div>
            <div class="col-md-11" v-else>
                <h1>Assignments</h1>
                <assignment-list :assignments="assignments"></assignment-list>
            </div>
        </div>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';
import { AssignmentList } from '@/components';

export default {
    name: 'submission-list-page',

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
        Icon,
    },
};
</script>
