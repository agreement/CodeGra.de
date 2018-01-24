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
import { MANAGE_COURSE_PERMISSIONS } from '@/constants';

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

    async mounted() {
        setPageTitle('Courses');
        const params = new URLSearchParams();
        params.append('type', 'course');
        MANAGE_COURSE_PERMISSIONS.forEach((perm) => {
            params.append('permission', perm);
        });

        const [courses, { data: canManage }, canCreate] = await Promise.all([
            this.$http.get('/api/v1/courses/'),
            this.$http.get('/api/v1/permissions/', {
                params,
            }),
            this.$hasPermission('can_create_courses'),
        ]);

        this.canCreate = canCreate;

        this.courses = courses.data;
        this.loading = false;
        for (let i = 0; i < this.courses.length; i += 1) {
            const course = this.courses[i];
            course.manageable = Object.values(canManage[course.id]).some(x => x);
        }
    },

    components: {
        CourseList,
        Loader,
        NewCourse,
    },
};
</script>
