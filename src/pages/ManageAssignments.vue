<template>
    <div class="page manage-assignment container-fluid">
        <div class="row justify-content-center">
            <b-list-group class="col-10">
                <b-list-group-item v-for="(a, i) in assignments">
                    <h5 class="assignment-title" @click="toggleRow(a.id)"
                        v-if="">
                        {{ a.name }}
                        <span class="icon text-muted">
                            <icon name="eye-slash" v-if="a.state_name == 'hidden'"></icon>
                            <icon name="clock-o" v-if="a.state_name == 'submitting' || a.state_name == 'grading'"></icon>
                            <icon name="check" v-if="a.state_name == 'done'"></icon>
                        </span>
                    </h5>
                    <b-collapse class="row" :id="`assignment-${a.id}`">
                        <assignment-state class="col-6" :assignment="a" @updateName="(n) => updateName(i, n)" @updateState="(s) => updateState(i, s)"></assignment-state>
                        <divide-submissions class="col-6" :assignment="a"></divide-submissions>
                    </b-collapse>
                </b-list-group-item>
            </b-list-group>
        </div>
    </div>
</template>

<script>
import { bCollapse, bListGroup, bListGroupItem } from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

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

        updateName(i, name) {
            this.assignments[i].name = name;
        },

        updateState(i, state) {
            this.assignments[i].state_name = state;
        },
    },

    components: {
        AssignmentState,
        DivideSubmissions,
        bCollapse,
        bListGroup,
        bListGroupItem,
        Icon,
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

    .icon {
        float: right;
    }
}
</style>
