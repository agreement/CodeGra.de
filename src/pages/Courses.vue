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
        this.$http.get('/api/v1/courses/').then(({ data }) => {
            this.loading = false;
            this.courses = data;
        });
    },

    components: {
        CourseList,
        Loader,
    },
};
</script>
