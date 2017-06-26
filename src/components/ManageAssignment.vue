<template>
    <div class="manage-assignment">
        <h5 class="assignment-title" @click="toggleRow">
            {{ assignment.name }}
            <span class="icon text-muted">
                <icon name="eye-slash" v-if="assignment.state == assignmentState.HIDDEN"></icon>
                <icon name="clock-o" v-if="assignment.state === assignmentState.SUBMITTING || assignment.state === assignmentState.GRADING || assignment.state === 'open'"></icon>
                <icon name="check" v-if="assignment.state == assignmentState.DONE"></icon>
            </span>
        </h5>
        <b-collapse class="row" :id="`assignment-${assignment.id}`">
            <assignment-state class="col-6" :assignment="assignment" @nameUpdated="updateName" @stateUpdated="updateState"></assignment-state>
            <divide-submissions class="col-6" :assignment="assignment"></divide-submissions>
            <div class="col-6">Linters</div>
            <div class="col-6">Upload blackboard zip</div>
            <linters class="col-6" :assignment="assignment"></linters>
            <blackboard-uploader class="col-6" :assignment="assignment"></blackboard-uploader>
        </b-collapse>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

import DivideSubmissions from './DivideSubmissions';
import AssignmentState from './AssignmentState';
import BlackboardUploader from './BlackboardUploader';
import Linters from './Linters';

import * as assignmentState from '../store/assignment-states';

export default {
    name: 'manage-assignment',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            assignmentState,
        };
    },

    methods: {
        toggleRow() {
            this.$root.$emit('collapse::toggle', `assignment-${this.assignment.id}`);
        },

        updateName(name) {
            this.assignment.name = name;
        },

        updateState(state) {
            this.assignment.state = state;
        },
    },

    components: {
        AssignmentState,
        BlackboardUploader,
        DivideSubmissions,
        Linters,
        Icon,
    },
};
</script>

<style lang="less" scoped>
.manage-assignment,
.assignment-title {
    width: 100%;
}

.assignment-title {
    margin-bottom: 0;
    cursor: pointer;

    .icon {
        float: right;
    }
}
</style>
