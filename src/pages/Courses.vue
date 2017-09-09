<template>
    <div class="page courses">
        <loader class="text-center" v-if="loading"></loader>
        <div class="" v-else>
            <h1>Courses</h1>
            <course-list :courses="courses"></course-list>
            <new-course v-if="canCreate"/>
        </div>
    </div>
</template>

<script>
import { CourseList, Loader, NewCourse } from '@/components';
import { mapActions } from 'vuex';

import { setPageTitle } from './title';

export default {
    name: 'course-list-page',

    data() {
        return {
            loading: true,
            courses: [],
            canCreate: false,
        };
    },

    methods: {
        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    mounted() {
        setPageTitle('Courses');

        Promise.all([
            this.$http.get('/api/v1/courses/'),
            this.$http.get('/api/v1/permissions/', {
                params: { permission: 'can_manage_course', course_id: 'all' },
            }),
            this.hasPermission({ name: 'can_create_courses', courseId: null }),
        ]).then(([coursesResponse, permsResponse, canCreate]) => {
            this.canCreate = canCreate;

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
        NewCourse,
    },
};
</script>
