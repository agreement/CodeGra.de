<template>
    <div class="page manage-assignment container-fluid">
        <div class="row justify-content-center">
            <b-list-group class="col-10">
                <b-list-group-item v-for="a in assignments">
                    <h5 class="assignment-title" @click="toggleRow(a.id)">{{ a.name }}</h5>
                    <b-collapse class="row" :id="`assignment-${a.id}`">
                        <assignment-state class="col-6" :assignment="a"></assignment-state>
                        <divide-submissions class="col-6" :assignment="a"></divide-submissions>
                    </b-collapse>
                </b-list-group-item>
            </b-list-group>
        </div>
    </div>
</template>

<script>
import { bCollapse, bListGroup, bListGroupItem } from 'bootstrap-vue/lib/components';

import { AssignmentState, DivideSubmissions } from '@/components';

export default {
    name: 'manage-assignment-page',

    data() {
        return {
            assignments: [],
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
    },

    mounted() {
        this.getAssignments();
    },

    methods: {
        getAssignments() {
            this.$http.get(`/api/v1/courses/${this.courseId}/assignments/`).then(({ data }) => {
                this.assignments = data;
            });
        },

        toggleRow(id) {
            this.$root.$emit('collapse::toggle', `assignment-${id}`);
        },
    },

    components: {
        AssignmentState,
        DivideSubmissions,
        bCollapse,
        bListGroup,
        bListGroupItem,
    },
};
</script>

<style lang="less" scoped>
.row {
    width: 100%;
}

.assignment-title {
    width: 100%;
    cursor: pointer;
}
</style>
