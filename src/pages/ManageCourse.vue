<template>
    <div class="page manage-course">
        <div v-if="created">
            <b-alert variant="success" show dismissible>
                <center><span>Succesfully created course!</span></center>
            </b-alert>
        </div>
        <loader v-if="loading"></loader>
        <manage-course v-else :assignments="assignments"></manage-course>
    </div>
</template>

<script>
import { ManageCourse, Loader } from '@/components';
import moment from 'moment';

import { setPageTitle } from './title';

export default {
    name: 'manage-course-page',

    data() {
        return {
            assignments: [],
            loading: true,
            created: false,
        };
    },

    computed: {
        courseId() { return this.$route.params.courseId; },
    },

    mounted() {
        this.created = this.$route.query.created;

        this.$http.get(`/api/v1/courses/${this.courseId}/assignments/`).then(({ data }) => {
            this.loading = false;
            for (let i = 0, len = data.length; i < len; i += 1) {
                data[i].deadline = moment.utc(data[i].deadline, moment.ISO_8601).local().format('YYYY-MM-DDTHH:mm');
                data[i].created_at = moment.utc(data[i].created_at, moment.ISO_8601).local().format('YYYY-MM-DDTHH:mm');
            }
            this.assignments = data;
        });

        this.$http.get(`/api/v1/courses/${this.courseId}`).then(({ data }) => {
            setPageTitle(data.name);
        });
    },

    components: {
        Loader,
        ManageCourse,
    },
};
</script>
