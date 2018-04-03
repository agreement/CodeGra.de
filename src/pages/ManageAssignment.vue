<template>
<div class="manage-assignment loading" v-if="loading">
    <local-header title=" ">
        <loader :scale="1"/>
    </local-header>
    <loader page-loader/>
</div>
<div class="manage-assignment" v-else>
    <local-header title="">
        <span slot="title">
            {{ assignment.name }} - <small>{{ assignment.deadline }}</small>
        </span>

        <assignment-state :assignment="assignment"
                          class="assignment-state"
                          :editable="permissions.can_edit_assignment_info"
                          size="sm"/>
    </local-header>

    <div class="page-content">
        <b-alert v-if="$route.query.created"
                 variant="success"
                 class="text-center"
                 show
                 dismissible>
            Succesfully created assignment!
        </b-alert>

        <div v-if="!assignment.is_lti && permissions.can_edit_assignment_info">
            <b-form-fieldset>
                <b-input-group prepend="Name">
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
                <b-input-group prepend="Deadline">
                    <input type="datetime-local"
                           class="form-control"
                           v-model="assignmentTempDeadline"
                           @keyup.ctrl.enter="updateDeadline"/>
                    <b-input-group-append>
                        <submit-button @click="updateDeadline"
                                       ref="updateDeadline"/>
                    </b-input-group-append>
                </b-input-group>
            </b-form-fieldset>
        </div>

        <div class="row">
            <div class="col-lg-6">
                <b-card v-if="permissions.can_assign_graders">
                    <span slot="header">
                        Divide submissions
                        <description-popover
                            description="Divide this assignment. When dividing
                                         users are assigned to submissions based on weights.
                                         When new submissions are uploaded graders are
                                         also automatically assigned. When graders assign
                                         themselves the weights are not updated to
                                         reflect this."/>
                    </span>
                    <loader class="text-center" v-if="gradersLoading && !gradersLoadedOnce"/>
                    <divide-submissions :assignment="assignment"
                                        @divided="loadGraders"
                                        :graders="graders"
                                        v-else/>
                </b-card>

                <b-card v-if="permissions.can_edit_cgignore">
                    <span slot="header">
                        CGIgnore
                        <description-popover
                            description="This file enables you to filter files
                                         from submissions. Its format is the
                                         same as `.gitignore`. If a file should
                                         be excluded according to this list a
                                         user will get a warning popup when
                                         submitting."/>
                    </span>
                    <c-g-ignore-file :assignment-id="assignmentId"/>
                </b-card>
            </div>

            <div class="col-lg-6">
                <b-card v-if="permissions.can_use_linter && UserConfig.features.linters"
                        header="Linters"
                        :course-id="assignment.course.id">
                    <linters :assignment="assignment"/>
                </b-card>

                <b-card v-if="permissions.can_update_grader_status || permissions.can_grade_work">
                    <span slot="header">
                        Finished grading
                        <description-popover
                            description="Indicate that a grader is done with
                                         grading. All graders that have indicated that they
                                         are done will not receive notification e-mails."/>
                    </span>
                    <loader class="text-center" v-if="gradersLoading"/>
                    <finished-grader-toggles :assignment="assignment"
                                             :graders="graders"
                                             :others="permissions.can_update_grader_status || false"
                                             v-else/>
                </b-card>

                <b-card v-if="permissions.can_update_course_notifications">
                    <span slot="header">
                        Notifications
                        <description-popover
                            description="Send a reminder e-mail to the selected
                                         graders on the selected time if they have not yet
                                         finished grading."/>
                    </span>
                    <notifications :assignment="assignment"
                                   class="reminders"/>
                </b-card>
            </div>
        </div>

        <b-card header="Rubric"
                v-if="permissions.manage_rubrics && UserConfig.features.rubrics">
            <rubric-editor :assignment="assignment"
                           ref="rubricEditor"
                           editable/>

        </b-card>


        <b-card v-if="permissions.can_submit_others_work">
            <span slot="header">
                Upload submission
                <description-popover
                    description="Upload work for this assignment. With the
                    author field you can select who should be the author. This
                    function can be used to submit work for a student."/>
            </span>
            <submission-uploader :assignment="assignment" for-others/>
        </b-card>

        <b-card header="Blackboard zip"
                v-if="permissions.can_upload_bb_zip &&
                      UserConfig.features.blackboard_zip_upload">
            <b-popover placement="top"
                       v-if="assignment.is_lti"
                       :target="`file-uploader-assignment-${assignment.id}`"
                       triggers="hover">
                Not available for LTI assignments
            </b-popover>
            <file-uploader :url="`/api/v1/assignments/${assignment.id}/submissions/`"
                           :disabled="assignment.is_lti"
                           :id="`file-uploader-assignment-${assignment.id}`"/>
        </b-card>
    </div>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import { convertToUTC } from '@/utils';
import { MANAGE_COURSE_PERMISSIONS } from '@/constants';

import {
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
    LocalHeader,
    SubmissionUploader,
} from '@/components';

export default {
    name: 'manage-assignment',

    data() {
        return {
            UserConfig,
            graders: [],
            gradersLoading: true,
            gradersLoadedOnce: false,
            assignmentTempName: '',
            assignmentTempDeadline: '',
            permissions: null,
            loading: true,
        };
    },

    computed: {
        ...mapGetters('courses', ['assignments']),

        assignmentId() {
            return Number(this.$route.params.assignmentId);
        },

        assignment() {
            return this.assignments[this.assignmentId];
        },

        assignmentUrl() {
            return `/api/v1/assignments/${this.assignment.id}`;
        },
    },

    watch: {
        assignment(newVal, oldVal) {
            if (!oldVal || newVal.id === oldVal.id) {
                return;
            }
            this.loadData();
        },
    },

    mounted() {
        this.loadData();
    },

    methods: {
        ...mapActions('courses', ['updateAssignment', 'loadCourses']),

        async loadData() {
            this.loading = true;
            await this.loadCourses();
            this.assignmentTempName = this.assignment.name;
            this.assignmentTempDeadline = this.assignment.deadline;
            await Promise.all([
                this.loadPermissions(),
                this.loadGraders(),
            ]);
            this.loading = false;
        },

        async loadPermissions() {
            this.permissions = null;
            this.permissions = await this.$hasPermission(
                MANAGE_COURSE_PERMISSIONS,
                this.assignment.course.id,
                true,
            );
        },

        async loadGraders() {
            if (!this.gradersLoading) {
                this.gradersLoading = true;
            }

            const { data } = await this.$http.get(`/api/v1/assignments/${this.assignment.id}/graders/`);
            this.graders = data;
            this.gradersLoading = false;
            this.gradersLoadedOnce = true;
        },

        updateName() {
            const req = this.$http.patch(this.assignmentUrl, {
                name: this.assignmentTempName,
            });

            this.$refs.updateName.submit(req.then(() => {
                this.updateAssignment({
                    courseId: this.assignment.course.id,
                    assignmentId: this.assignment.id,
                    assignmentProps: {
                        name: this.assignmentTempName,
                    },
                });
            }, (err) => {
                throw err.response.data.message;
            }));
        },

        updateDeadline() {
            const req = this.$http.patch(this.assignmentUrl, {
                deadline: convertToUTC(this.assignmentTempDeadline),
            });

            this.$refs.updateDeadline.submit(req.then(() => {
                this.updateAssignment({
                    assignmentId: this.assignment.id,
                    assignmentProps: {
                        deadline: this.assignmentTempDeadline,
                    },
                });
            }, (err) => {
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
        LocalHeader,
        SubmissionUploader,
    },
};
</script>

<style lang="less" scoped>
.assignment-title {
    margin-bottom: 0;
}

.manage-assignment.loading {
    display: flex;
    flex-direction: column;
}

.card {
    margin-bottom: 1em;
}

.card-header {
    font-size: 1.25rem;
    font-family: inherit;
    font-weight: 500;
    line-height: 1.2;
    color: inherit;
}

.divide-submissions {
    margin: -1.25rem -1.25rem -.25rem;
}

.finished-grader-toggles {
    margin: -1.25rem;
}
</style>
