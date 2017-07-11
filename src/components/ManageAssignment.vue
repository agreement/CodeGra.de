<template>
    <div class="manage-assignment">
        <div class="header">
            <h5 class="assignment-title" @click="toggleRow">
                {{ assignment.name }}
            </h5>

            <b-button-group @click.native="updateState">
                <b-popover placement="top" triggers="hover" content="Hidden or open, managed by LTI" v-if="assignment.is_lti">
                    <b-button class="larger" size="sm" value="hidden"
                              :variant="assignment.state !== assignmentState.DONE ? 'primary': 'outline-primary'">
                        <loader :scale="1" v-if="pendingState === assignmentState.HIDDEN"></loader>
                        <b-button-group v-else>
                            <icon name="eye-slash"></icon><icon name="clock-o"></icon>
                        </b-button-group>
                    </b-button>
                </b-popover>
                <b-button-group v-else>
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
                </b-button-group>
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
            <b-popover placement="top" :triggers="assignment.is_lti ? ['hover'] : []" content="Not available for LTI assignments">
                <b-form-fieldset>
                    <b-input-group left="Name">
                        <b-form-input type="text" v-model="assignment.name" @keyup.native.enter="updateName" :disabled="assignment.is_lti"/>
                        <b-input-group-button>
                            <submit-button @click="updateName" ref="updateName" :disabled="assignment.is_lti"/>
                        </b-input-group-button>
                    </b-input-group>
                </b-form-fieldset>
            </b-popover>

            <b-popover placement="top" :triggers="assignment.is_lti ? ['hover'] : []" content="Not available for LTI assignments">
                <b-form-fieldset>
                    <b-input-group left="Deadline">
                        <b-form-input type="datetime-local" v-model="assignment.deadline" @keyup.native.enter="updateDeadline" :disabled="assignment.is_lti"/>
                        <b-input-group-button>
                            <submit-button @click="updateDeadline" ref="updateDeadline" :disabled="assignment.is_lti"/>
                        </b-input-group-button>
                    </b-input-group>
                </b-form-fieldset>
            </b-popover>

            <div class="row">
                <divide-submissions class="col-md-6" :assignment="assignment"></divide-submissions>
                <linters class="col-md-6" :assignment="assignment"></linters>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <b-form-fieldset label="Upload blackboard zip">
                        <b-popover placement="top" :triggers="assignment.is_lti ? ['hover'] : []" content="Not available for LTI assignments">
                            <blackboard-uploader :disabled="assignment.is_lti" :assignment="assignment"></blackboard-uploader>
                        </b-popover>
                    </b-form-fieldset>
                </div>

                <div class="col-md-6">
                    <b-form-fieldset label="Misc.">
                        <b-button-toolbar>
                            <b-button
                                variant="primary"
                                @click="$emit('showRubric', assignment.id)">
                                Rubric
                            </b-button>
                        </b-button-toolbar>
                    </b-form-fieldset>
                </div>
            </div>
        </b-collapse>
    </div>
</template>

<script>
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
                state: this.pendingState,
            }).then(() => {
                this.assignment.state = this.pendingState;
                this.pendingState = '';
            }, (err) => {
                // TODO: visual feedback
                // eslint-disable-next-line
                console.dir(err);
            });
        },

        updateName() {
            const req = this.$http.patch(this.assignmentUrl, {
                name: this.assignment.name,
            });
            this.$refs.updateName.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        updateDeadline() {
            const req = this.$http.patch(this.assignmentUrl, {
                deadline: this.assignment.deadline,
            });
            req.catch(([err]) => {
                // TODO: visual feedback
                // eslint-disable-next-line
                console.dir(err);
            });
            this.$refs.updateDeadline.submit(req);
        },
    },

    components: {
        BlackboardUploader,
        DivideSubmissions,
        Linters,
        Loader,
        SubmitButton,
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

    button.larger {
        width: 3.5em;
        .btn-group {
            display: block;
        }
        .fa-icon {
            margin-left: 0;
        }
        margin-left: 0;
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
