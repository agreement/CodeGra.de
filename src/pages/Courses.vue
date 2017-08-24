<template>
    <div class="page courses">
        <loader class="text-center" v-if="loading"></loader>
        <div class="" v-else>
            <h1>Courses</h1>
            <course-list :courses="courses"></course-list>
        </div>
    </div>
</template>

<script>
import { CourseList, Loader } from '@/components';

import { setPageTitle } from './title';

export default {
    name: 'course-list-page',

    data() {
        return {
            loading: true,
            courses: [],
        };
    },

    mounted() {
        setPageTitle('Courses');

        Promise.all([
            this.$http.get('/api/v1/courses/'), this.$http.get('/api/v1/permissions/', {
                params: { permission: 'can_manage_course', course_id: 'all' },
            })]).then(([coursesResponse, permsResponse]) => {
                this.courses = coursesResponse.data;
                this.loading = false;
                for (let i = 0; i < this.courses.length; i += 1) {
                    const course = this.courses[i];
                    course.manageable = permsResponse.data[course.id];
                }
            },
        );
    },

    components: {
        CourseList,
        Loader,
    },
};
</script>
