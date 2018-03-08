<template>
<div class="manage-assignment">
    <div class="header">
        <h5 class="assignment-title" @click="toggleRow">
            <a class="invisible-link" href="#" @click.native.prevent>
                {{ assignment.name }} - <small>{{ assignment.deadline }}</small>
            </a>
        </h5>

        <assignment-state :assignment="assignment"
                          :editable="!assignment.is_lti"
                          :permissions="permissions"
                          size="sm"/>

        <b-button-group>
            <b-button class="submissions-button" @click="goToSubmissions">
                Submissions
            </b-button>
        </b-button-group>
    </div>

    <b-collapse :id="`assignment-${assignment.id}`">
        <div v-if="!assignment.is_lti && permissions.can_edit_assignment_info">
            <b-form-fieldset>
                <b-input-group left="Name">
                    <input type="text"
                           class="form-control"
                           v-model="assignmentTempName"
                           @keyup.ctrl.enter="updateName"/>
                    <b-input-group-append>
                        <submit-button @click="updateName"
                                       ref="updateName"/>
                    </b-input-group-append>
                </b-input-group>
            </b-form-fieldset>

            <b-form-fieldset>
                <b-input-group left="Deadline">
                    <input type="datetime-local"
                           class="form-control"
                           v-model="assignment.deadline"
                           @keyup.ctrl.enter="updateDeadline"/>
                    <b-input-group-append>
                        <submit-button @click="updateDeadline"
                                       ref="updateDeadline"/>
                    </b-input-group-append>
                </b-input-group>
            </b-form-fieldset>
        </div>

        <div class="row">
            <div class="col-lg-5">
                <div v-if="permissions.can_assign_graders"
                     class="comp-wrapper">
                    <h5>
                        Divide submissions
                        <description-popover
                            description="Divide this assignment. When dividing
                                         users are assigned to submissions based on weights.
                                         When new submissions are uploaded graders are
                                         also automatically assigned. When graders assign
                                         themselves the weights are not updated to
                                         reflect this."/>
                    </h5>
                    <loader class="text-center" v-if="gradersLoading && !gradersLoadedOnce"/>
                    <divide-submissions :assignment="assignment"
                                        @divided="loadGraders"
                                        :graders="graders"
                                        v-else/>
                </div>

                <div v-if="permissions.can_edit_cgignore"
                     class="comp-wrapper">
                    <h5>CGIgnore file</h5>
                    <CGIgnoreFile :assignment="assignment"/>
                </div>
            </div>

            <div class="col-lg-7">
                <div v-if="permissions.can_use_linter && UserConfig.features.linters"
                     :course-id="assignment.course.id"
                     class="comp-wrapper">
                    <h5>Linters</h5>
                    <linters :assignment="assignment"/>
                </div>

                <div v-if="permissions.can_update_grader_status || permissions.can_grade_work"
                     class="comp-wrapper">
                    <h5>
                        Finished grading
                        <description-popover
                            description="Indicate that a grader is done with
                                         grading. All graders that have indicated that they
                                         are done will not receive notification e-mails."/>
                    </h5>
                    <loader class="text-center" v-if="gradersLoading"/>
                    <finished-grader-toggles :assignment="assignment"
                                             :graders="graders"
                                             :others="permissions.can_update_grader_status || false"
                                             v-else/>
                </div>

                <div v-if="permissions.can_update_course_notifications"
                     class="comp-wrapper">
                    <h5>
                        Notifications
                        <description-popover
                            description="Send a reminder e-mail to the selected
                                         graders on the selected time if they have not yet
                                         finished grading."/>
                    </h5>
                    <div class="form-control reminders-wrapper">
                        <notifications :assignment="assignment"
                                       class="reminders"/>
                    </div>
                </div>
            </div>
        </div>

        <div class="row"
             v-if="permissions.manage_rubrics && UserConfig.features.rubrics">
            <div class="col-md-12 comp-wrapper">
                <h5>Rubric</h5>
                <rubric-editor :assignmentId="assignment.id"
                               ref="rubricEditor"
                               :editable="true"/>
            </div>
        </div>

        <div class="row"
             v-if="permissions.can_upload_bb_zip &&
                   UserConfig.features.blackboard_zip_upload">
            <div class="col-md-12">
                <h5>Upload blackboard zip</h5>
                <b-popover placement="top"
                           v-if="assignment.is_lti"
                           :target="`file-uploader-assignment-${assignment.id}`"
                           triggers="hover">
                    Not available for LTI assignments
                </b-popover>
                <file-uploader :url="`/api/v1/assignments/${assignment.id}/submissions/`"
                               :disabled="assignment.is_lti"
                               :id="`file-uploader-assignment-${assignment.id}`"/>
            </div>
        </div>
    </b-collapse>
</div>
</template>

<script>
import { convertToUTC } from '@/utils';

import AssignmentState from './AssignmentState';
import DivideSubmissions from './DivideSubmissions';
import FileUploader from './FileUploader';
import Linters from './Linters';
import Loader from './Loader';
import SubmitButton from './SubmitButton';
import RubricEditor from './RubricEditor';
import CGIgnoreFile from './CGIgnoreFile';
import Notifications from './Notifications';
import DescriptionPopover from './DescriptionPopover';
import FinishedGraderToggles from './FinishedGraderToggles';

export default {
    name: 'manage-assignment',

    props: {
        assignment: {
            type: Object,
            default: null,
        },

        permissions: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            UserConfig,
            graders: [],
            gradersLoading: true,
            gradersLoadedOnce: false,
            assignmentTempName: '',
        };
    },

    computed: {
        assignmentUrl() {
            return `/api/v1/assignments/${this.assignment.id}`;
        },
    },

    mounted() {
        this.assignmentTempName = this.assignment.name;
        this.loadGraders();
    },

    methods: {
        async loadGraders() {
            if (!this.gradersLoading) {
                this.gradersLoading = true;
            }

            const { data } = await this.$http.get(`/api/v1/assignments/${this.assignment.id}/graders/`);
            this.graders = data;
            this.gradersLoading = false;
            this.gradersLoadedOnce = true;
        },

        toggleRow() {
            this.$root.$emit('bv::toggle::collapse', `assignment-${this.assignment.id}`);
        },

        updateName() {
            const req = this.$http.patch(this.assignmentUrl, {
                name: this.assignmentTempName,
            });
            this.$refs.updateName.submit(req.then(() => {
                this.assignment.name = this.assignmentTempName;
            }, (err) => {
                throw err.response.data.message;
            }));
        },

        updateDeadline() {
            const req = this.$http.patch(this.assignmentUrl, {
                deadline: convertToUTC(this.assignment.deadline),
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
        AssignmentState,
        DivideSubmissions,
        FileUploader,
        Linters,
        Loader,
        SubmitButton,
        RubricEditor,
        CGIgnoreFile,
        Notifications,
        DescriptionPopover,
        FinishedGraderToggles,
    },
};
</script>

<style lang="less" scoped>
.manage-assignment {
    flex-grow: 1;
    max-width: 100%;
}

.header {
    display: flex;
    align-items: center;
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

    .submissions-button {
        margin-left: .75em;
    }
}

.comp-wrapper {
    margin-bottom: 1em;
}

[id^="assignment-"] {
    margin-top: 1em;
}
</style>
