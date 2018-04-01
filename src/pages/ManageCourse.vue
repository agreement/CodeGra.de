<template>
<div v-else class="manage-course">
    <local-header>
        <b-form-fieldset class="filter-input">
            <input v-model="filter"
                    class="form-control"
                    placeholder="Type to Search"/>
        </b-form-fieldset>

        <toggle label-off="Users" label-on="Roles"
                :value-off="0" :value-on="1"
                :colors="false"
                class="component-toggler"
                v-model="tabIndex"
                :disabled-text="course ? `You don't have permission to edit the ${course.permissions.can_edit_course_users ? 'roles' : 'users'}.` : ''"
                :disabled="!course || !course.canManage"/>
    </local-header>

    <loader v-if="!course" page-loader/>
    <div class="content" v-else>
        <users-manager v-show="tabIndex === 0"
                       :course="course"
                       :filter="filter"/>
        <permissions-manager v-show="tabIndex === 1"
                             :course-id="course.id"
                             :filter="filter"/>
    </div>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import UsersManager from '@/components/UsersManager';
import PermissionsManager from '@/components/PermissionsManager';
import LocalHeader from '@/components/LocalHeader';
import Loader from '@/components/Loader';
import Toggle from '@/components/Toggle';

import { setPageTitle } from './title';

export default {
    name: 'manage-course-page',

    data() {
        return {
            tabIndex: 0,
            filter: '',
        };
    },

    computed: {
        ...mapGetters('courses', ['courses']),

        course() {
            return this.courses[this.$route.params.courseId];
        },

        courseId() {
            return this.$route.params.courseId;
        },
    },

    async mounted() {
        await this.loadCourses();
        this.tabIndex = this.getInitialTab();
    },

    watch: {
        tabIndex(newVal) {
            this.filter = '';
            this.$router.replace(Object.assign({}, this.$route, {
                hash: newVal === 1 ? '#roles' : '#users',
            }));
        },

        course() {
            setPageTitle(this.course.name);
        },

        $route(newVal, oldVal) {
            if (newVal.hash !== oldVal.hash) {
                if (newVal.params.courseId !== oldVal.params.courseId) {
                    setPageTitle(this.course.name);
                }
                this.tabIndex = this.getInitialTab();
            }
        },
    },

    methods: {
        ...mapActions('courses', ['loadCourses']),

        getInitialTab() {
            const oldPage = this.$route.hash;

            if (oldPage === '#users' && this.course.permissions.can_edit_course_users) {
                return 0;
            } else if (oldPage === '#roles' && this.course.permissions.can_edit_course_roles) {
                return 1;
            } else {
                return this.course.permissions.can_edit_course_users ? 0 : 1;
            }
        },
    },

    components: {
        UsersManager,
        PermissionsManager,
        LocalHeader,
        Loader,
        Toggle,
    },
};
</script>

<style lang="less">
@import "~mixins.less";

.manage-course {
    display: flex;
    flex-direction: column;
}
.manage-course > .content {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
}

.filter-input {
    flex: 1 1 auto;
    margin-right: 1rem;
    margin-bottom: 0;
}

.component-toggler {
    flex: 0 0 auto;
    .default-text-colors;
    font-size: 1.2em;
}
</style>
