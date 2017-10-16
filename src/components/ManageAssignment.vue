<template>
    <div class="manage-assignment">
        <div class="header">
            <h5 class="assignment-title" @click="toggleRow">
                {{ assignment.name }}
            </h5>

            <b-button-group @click.native="updateState">
                <b-popover placement="top" triggers="hover" content="Hidden or open, managed by LTI" v-if="assignment.is_lti">
                    <b-button class="state-button larger" size="sm" value="hidden"
                              :variant="assignment.state !== assignmentState.DONE ? 'primary': 'outline-primary'">
                        <loader :scale="1" v-if="pendingState === assignmentState.HIDDEN"></loader>
                        <b-button-group v-else>
                            <icon name="eye-slash"></icon><icon name="clock-o"></icon>
                        </b-button-group>
                    </b-button>
                </b-popover>
                <b-button-group v-else>
                    <b-popover placement="top" triggers="hover" content="Hidden">
                        <b-button class="state-button" size="sm" value="hidden"
                                  :variant="assignment.state === assignmentState.HIDDEN ? 'danger' : 'outline-danger'">
                            <loader :scale="1" v-if="pendingState === assignmentState.HIDDEN"></loader>
                            <icon name="eye-slash" v-else></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Open">
                        <b-button class="state-button" size="sm" value="open"
                                  :variant="[assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(assignment.state) > -1 ? 'warning' : 'outline-warning'">
                            <loader :scale="1" v-if="[assignmentState.SUBMITTING, assignmentState.GRADING, 'open'].indexOf(pendingState) > -1"></loader>
                            <icon name="clock-o" v-else></icon>
                        </b-button>
                    </b-popover>
                </b-button-group>
                <b-popover placement="top" triggers="hover" content="Done">
                    <b-button class="state-button" size="sm" value="done"
                              :variant="assignment.state === assignmentState.DONE ? 'success' : 'outline-success'">
                        <loader :scale="1" v-if="pendingState === assignmentState.DONE"></loader>
                        <icon name="check" v-else></icon>
                    </b-button>
                </b-popover>
            </b-button-group>
            <b-button-group>
                <b-button class="submissions-button" @click="goToSubmissions">
                    Submissions
                </b-button>
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
                <div class="col-lg-5 divide-comp-wrapper">
                    <h5>Divide submissions</h5>
                    <divide-submissions :assignment="assignment"/>

                    <h5 style="margin-top: 1em">CGIgnore file</h5>
                    <CGIgnoreFile :assignment="assignment"/>
                </div>
                <div class="col-lg-7 linter-comp-wrapper">
                    <h5>Linters</h5>
                    <linters :assignment="assignment"></linters>
                </div>
            </div>

            <div class="col-md-12 rubric-editor-comp-wrapper" v-if="UserConfig.features.rubrics">
                <h5>Rubric</h5>
                    <rubric-editor :assignmentId="assignment.id"
                                   ref="rubricEditor"
                                   :editable="true"/>
                </b-form-fieldset>
            </div>

            <div class="col-md-12" v-if="UserConfig.features.blackboard_zip_upload">
                <h5>Upload blackboard zip</h5>
                    <b-popover
                        placement="top"
                        :triggers="assignment.is_lti ? ['hover'] : []"
                        content="Not available for LTI assignments">
                        <file-uploader
                            :url="`/api/v1/assignments/${assignment.id}/submissions/`"
                            :disabled="assignment.is_lti"/>
                    </b-popover>
                </b-form-fieldset>
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
import FileUploader from './FileUploader';
import Linters from './Linters';
import Loader from './Loader';
import SubmitButton from './SubmitButton';
import RubricEditor from './RubricEditor';
import CGIgnoreFile from './CGIgnoreFile';

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
            UserConfig,
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
            this.$refs.updateDeadline.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

        goToSubmissions() {
            this.$router.push({
                name: 'assignment_submissions',
                params: {
                    courseId: this.assignment.course.id,
                    assignmentId: this.assignment.id,
                },
            });
        },
    },

    components: {
        DivideSubmissions,
        FileUploader,
        Linters,
        Loader,
        SubmitButton,
        Icon,
        RubricEditor,
        CGIgnoreFile,
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
        padding: (@vpad + .5rem) 0 @vpad @hpad;
        margin: -@vpad 0 -@vpad -@hpad;;
    }

    .state-button.larger {
        width: 3.5em;
        .btn-group {
            display: block;
        }
        .fa-icon {
            margin-left: 0;
        }
        margin-left: 0;
    }

    .state-button {
        width: 1.75em;
        height: 1.75em;
        margin-top: .5em;
        margin-left: .375em;
        border-radius: 50%;
        border: 0;
        padding-left: .375rem;

        svg {
            width: 1em;
            height: 1em;
        }
    }

    .submissions-button {
        margin-left: .75em;
    }
}

.rubric-editor-comp-wrapper,
.linter-comp-wrapper,
.divide-comp-wrapper {
    margin-bottom: 1em;
}

[id^="assignment-"] {
    margin-top: 1em;
}
</style>
