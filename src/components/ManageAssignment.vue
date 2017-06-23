<template>
    <div class="manage-assignment">
        <div class="header">
            <h5 class="assignment-title" @click="toggleRow">
                {{ assignment.name }}
            </h5>
            <b-button-group @click.native="updateState">
                <b-popover placement="top" triggers="hover" content="Hidden">
                    <b-button size="sm" value="hidden"
                        :variant="assignment.state === assignmentState.HIDDEN ? 'danger' : 'outline-danger'">
                        <loader scale="1" v-if="submitting && assignment.state === assignmentState.HIDDEN"></loader>
                        <icon name="eye-slash" v-else></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Open">
                    <b-button size="sm" value="open"
                        :variant="[assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(assignment.state) > -1 ? 'warning' : 'outline-warning'">
                        <loader scale="1" v-if="submitting && [assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(assignment.state) > -1"></loader>
                        <icon name="clock-o" v-else></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Done">
                    <b-button size="sm" value="done"
                        :variant="assignment.state === assignmentState.DONE ? 'success' : 'outline-success'">
                        <loader scale="1" v-if="submitting && assignment.state === assignmentState.DONE"></loader>
                        <icon name="check" v-else></icon>
                    </b-button>
                </b-popover>
            </b-button-group>
        </div>
        <b-collapse class="row" :id="`assignment-${assignment.id}`">
            <div class="col-12">Upload blackboard zip</div>
            <blackboard-uploader class="col-12" :assignment="assignment"></blackboard-uploader>
            <divide-submissions class="col-6" :assignment="assignment"></divide-submissions>
            <linters class="col-6" :assignment="assignment"></linters>
        </b-collapse>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bCollapse, bPopover } from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

import DivideSubmissions from './DivideSubmissions';
import BlackboardUploader from './BlackboardUploader';
import Linters from './Linters';
import Loader from './Loader';

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
            submitting: false,
        };
    },

    methods: {
        toggleRow() {
            this.$root.$emit('collapse::toggle', `assignment-${this.assignment.id}`);
        },

        updateState({ target }) {
            const button = target.closest('button');
            if (!button) return;

            const oldState = this.assignment.state;
            this.assignment.state = button.getAttribute('value');
            this.submitting = true;
            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                state: this.assignment.state,
            }).catch(() => {
                this.assignment.state = oldState;
            }).then(() => {
                this.submitting = false;
            });
        },
    },

    components: {
        BlackboardUploader,
        DivideSubmissions,
        Linters,
        Loader,
        bButton,
        bButtonGroup,
        bCollapse,
        bPopover,
        Icon,
    },
};
</script>

<style lang="less" scoped>
.manage-assignment {
    flex-grow: 1;
}

.header {
    display: flex;
    flex-direction: row;
}

.assignment-title {
    flex-grow: 1;
    cursor: pointer;

    /* Make the entire header clickable. */
    @hpad: 1.25rem;
    @vpad: .75rem;
    padding: @vpad 0 @vpad @hpad;
    margin: -@vpad 0 -@vpad -@hpad;;
}

button {
    width: 1.75em;
    height: 1.75em;
    margin-left: .375em;
    border-radius: 50%;
    border: 0;
    padding-left: .375rem;

    svg {
        width: 1em;
        height: 1em;
    }
}
</style>
