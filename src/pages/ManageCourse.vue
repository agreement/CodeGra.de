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
        ]).then(([assignments, course, perms]) => {
            this.permissions = perms;

            let data = assignments.data;
            for (let i = 0, len = data.length; i < len; i += 1) {
                const deadline = moment.utc(data[i].deadline, moment.ISO_8601).local();
                const reminderTime = moment.utc(data[i].reminder_time, moment.ISO_8601).local();
                let defaultReminderTime = deadline.clone().add(7, 'days');

                if (defaultReminderTime.isBefore(moment())) {
                    defaultReminderTime = moment().add(3, 'days');
                }

                data[i].deadline = deadline.format('YYYY-MM-DDTHH:mm');
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601)
                    .local()
                    .format('YYYY-MM-DDTHH:mm');
                data[i].reminder_time = (reminderTime.isValid() ?
                                         reminderTime :
                                         defaultReminderTime)
                    .format('YYYY-MM-DDTHH:mm');
            }
            this.assignments = data;

            data = course.data;
            this.course = data;
            setPageTitle(data.name);

            this.loading = false;
        });
    },

    components: {
        Loader,
        ManageCourse,
    },
};
</script>
