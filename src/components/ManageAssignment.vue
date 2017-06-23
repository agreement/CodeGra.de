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
                        <loader :scale="1" v-if="pendingState === assignmentState.HIDDEN"></loader>
                        <icon name="eye-slash" v-else></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Open">
                    <b-button size="sm" value="open"
                        :variant="[assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(assignment.state) > -1 ? 'warning' : 'outline-warning'">
                        <loader :scale="1" v-if="[assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(pendingState) > -1"></loader>
                        <icon name="clock-o" v-else></icon>
                    </b-button>
                </b-popover>
                <b-popover placement="top" triggers="hover" content="Done">
                    <b-button size="sm" value="done"
                        :variant="assignment.state === assignmentState.DONE ? 'success' : 'outline-success'">
                        <loader :scale="1" v-if="pendingState === assignmentState.DONE"></loader>
                        <icon name="check" v-else></icon>
                    </b-button>
                </b-popover>
            </b-button-group>
        </div>
        <b-collapse :id="`assignment-${assignment.id}`">
            <b-form-fieldset>
                <b-input-group left="Name">
                    <b-form-input type="text" v-model="assignment.name" @keyup.native.enter="updateName"></b-form-input>
                    <b-input-group-button>
                        <submit-button :update="updateName" ref="updateName"></submit-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>
            <b-form-fieldset>
                <b-input-group left="Deadline">
                    <b-form-input type="datetime-local" v-model="assignment.deadline" @keyup.native.enter="updateDeadline"></b-form-input>
                    <b-input-group-button>
                        <submit-button :update="updateDeadline" ref="updateDeadline"></submit-button>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>

            <div class="row">
                <divide-submissions class="col-6" :assignment="assignment"></divide-submissions>
                <linters class="col-6" :assignment="assignment"></linters>
            </div>

            <b-form-fieldset label="Upload blackboard zip">
                <blackboard-uploader :assignment="assignment"></blackboard-uploader>
            </b-form-fieldset>
        </b-collapse>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bCollapse, bFormFieldset, bFormInput, bInputGroup, bPopover } from 'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

import DivideSubmissions from './DivideSubmissions';
import BlackboardUploader from './BlackboardUploader';
import Linters from './Linters';
import Loader from './Loader';
import SubmitButton from './SubmitButton';

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
            pendingState: '',
        };
    },

    computed: {
        assignmentUrl() {
            return `/api/v1/assignments/${this.assignment.id}`;
        },
    },

    methods: {
        toggleRow() {
            this.$root.$emit('collapse::toggle', `assignment-${this.assignment.id}`);
        },

        updateState({ target }) {
            const button = target.closest('button');
            if (!button) return;

            this.pendingState = button.getAttribute('value');

            this.$http.patch(this.assignmentUrl, {
                state: this.assignment.state,
            }).then(() => {
                this.assignment.state = this.pendingState;
                this.pendingState = '';
            }, () => {
                // handle error
            });
        },

        updateName() {
            this.$refs.updateName.submit(this.$http.patch(this.assignmentUrl, {
                name: this.assignment.name,
            })).then(() => {
                // success
            }, () => {
                // handle error
            });
        },

        updateDeadline() {
            this.$refs.updateDeadline.submit(this.$http.patch(this.assignmentUrl, {
                deadline: this.assignment.deadline,
            })).then(() => {
                // success
            }, () => {
                // handle error
            });
        },
    },

    components: {
        BlackboardUploader,
        DivideSubmissions,
        Linters,
        Loader,
        SubmitButton,
        bButton,
        bButtonGroup,
        bCollapse,
        bFormFieldset,
        bFormInput,
        bInputGroup,
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
}

[id^="assignment-"] {
    margin-top: 1em;
}
</style>
