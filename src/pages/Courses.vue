<template>
    <div class="page courses">
        <div class="row justify-content-center">
            <loader class="col-md-10 text-center" v-if="loading"></loader>
            <div class="col-md-10" v-else>
                <h1>Courses</h1>
                <course-list :courses="courses"></course-list>
            </div>
        </div>
    </div>
</template>

<script>
import { CourseList, Loader } from '@/components';

export default {
    name: 'course-list-page',

    data() {
        return {
            loading: true,
            courses: [],
        };
    },

    mounted() {
        Promise.all([
            this.$http.get('/api/v1/courses/'), this.$http.get('/api/v1/permissions/', {
                params: { permission: 'can_manage_course', type: 'all' },
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
