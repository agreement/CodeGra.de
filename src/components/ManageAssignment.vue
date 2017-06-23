<template>
    <div class="manage-assignment">
        <div class="header">
            <h5 class="assignment-title" @click="toggleRow">
                {{ assignment.name }}
            </h5>
            <b-button-group @click.native="updateState">
                <b-popover placement="top" triggers="hover" content="Hidden">
                    <b-button :variant="assignment.state === assignmentState.HIDDEN ? 'danger' : 'outline-danger'" size="sm" value="hidden">
                        <icon name="eye-slash"></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Open">
                    <b-button :variant="assignment.state === assignmentState.SUBMITTING || assignment.state === assignmentState.GRADING || assignment.state === 'open' ? 'warning' : 'outline-warning'" size="sm" value="open">
                        <icon name="clock-o"></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Done">
                    <b-button :variant="assignment.state === assignmentState.DONE ? 'success' : 'outline-success'" size="sm" value="done">
                        <icon name="check"></icon>
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
import { bCollapse, bPopover } from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

import DivideSubmissions from './DivideSubmissions';
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

            const newState = button.getAttribute('value');

            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                state: newState,
            }).then(() => {
                this.assignment.state = newState;
            }, (err) => {
                // show error
                console.dir(err);
            });
        },
    },

    components: {
        BlackboardUploader,
        DivideSubmissions,
        Linters,
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
    justify-content: space-between;
}

.assignment-title {
    flex-grow: 1;
    margin-bottom: 0;
    cursor: pointer;

    .icon {
        float: right;
    }
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
