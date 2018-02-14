<template>
    <div class="page manage-course">
        <div v-if="created">
            <b-alert variant="success" show dismissible>
                <center><span>Succesfully created course!</span></center>
            </b-alert>
        </div>
        <loader v-if="loading"></loader>
        <manage-course v-else
                       :assignments="assignments"
                       :course="course"
                       :permissions="permissions"
                       @created="(assig) => { assignments.push(assig); }"/>
    </div>
</template>

<script>
import { ManageCourse, Loader } from '@/components';
import moment from 'moment';

import { MANAGE_COURSE_PERMISSIONS } from '@/constants';

import { setPageTitle } from './title';

export default {
    name: 'manage-course-page',

    data() {
        return {
            assignments: [],
            loading: true,
            created: false,
            course: null,
            permissions: {},
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
    },

    mounted() {
        this.created = this.$route.query.created;

        Promise.all([
            this.$http.get(`/api/v1/courses/${this.courseId}/assignments/`),
            this.$http.get(`/api/v1/courses/${this.courseId}`),
            this.$hasPermission(
                MANAGE_COURSE_PERMISSIONS,
                this.courseId,
                true,
            ),
        ]).then(([{ data: assignments }, { data: course }, perms]) => {
            this.permissions = perms;

            for (let i = 0, len = assignments.length; i < len; i += 1) {
                const deadline = moment.utc(assignments[i].deadline, moment.ISO_8601).local();
                const reminderTime = moment.utc(
                    assignments[i].reminder_time,
                    moment.ISO_8601,
                ).local();
                let defaultReminderTime = deadline.clone().add(7, 'days');

                if (defaultReminderTime.isBefore(moment())) {
                    defaultReminderTime = moment().add(3, 'days');
                }

                assignments[i].deadline = deadline.format('YYYY-MM-DDTHH:mm');
                assignments[i].created_at = moment.utc(assignments[i].created_at, moment.ISO_8601)
                    .local()
                    .format('YYYY-MM-DDTHH:mm');
                assignments[i].has_reminder_time = reminderTime.isValid();
                assignments[i].reminder_time = (reminderTime.isValid() ?
                    reminderTime :
                    defaultReminderTime)
                    .format('YYYY-MM-DDTHH:mm');
            }
            this.assignments = assignments;

            this.course = course;
            setPageTitle(course.name);

            this.loading = false;
        });
    },

    components: {
        Loader,
        ManageCourse,
    },
};
</script>
