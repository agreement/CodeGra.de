<template>
<li :class="{
            'selected': selected && !manageSelected,
            'light-selected': selected,
            }"
    class="sidebar-list-item course-list-item">
    <a class="sidebar-item course-name"
       @click="openAssignmentsList">
        {{ course.name }}
    </a>
    <router-link class="sidebar-item manage-link"
                    v-if="course.canManage"
                    :class="{ selected: manageSelected }"
                    :to="manageRoute">
        <icon name="gear"/>
    </router-link>
</li>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/gear';

export default {
    name: 'course-list-item',

    props: {
        course: {
            type: Object,
            required: true,
        },

        currentId: {
            type: Number,
            default: null,
        },
    },

    computed: {
        selected() {
            return this.course.id === this.currentId;
        },

        manageSelected() {
            return this.selected && this.$route.name === 'manage_course';
        },

        manageRoute() {
            return {
                name: 'manage_course',
                params: {
                    courseId: this.course.id,
                },
            };
        },
    },

    methods: {
        openAssignmentsList() {
            this.$emit('open-menu', {
                header: this.course.name,
                component: 'assignment-list',
                data: {
                    course: this.course,
                },
                reload: true,
            });
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.course-name {
    flex: 1 1 auto;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

a {
    text-decoration: none;
    color: inherit;
}
</style>
