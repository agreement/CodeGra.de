<template>
    <div class="page courses">
        <h1>Courses</h1>
        <course-list/>
    </div>
</template>

<script>
import { CourseList } from '@/components';
import { setPageTitle } from './title';

export default {
    name: 'course-list-page',

    mounted() {
        setPageTitle('Courses');
    },

    components: {
        CourseList,
    },
};
</script>
