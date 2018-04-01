<template>
<div class="course-list sidebar-list-wrapper">
    <div class="sidebar-filter">
        <input class="form-control"
               placeholder="Filter courses"
               v-model="filter"
               ref="filter">
    </div>

    <ul class="sidebar-list"
        v-if="sortedCourses.length > 0">
        <course-list-item v-for="course in topCourses"
                          :key="`top-course-${course.id}`"
                          v-if="showTopCourses"
                          :course="course"
                          :current-id="currentCourse && currentCourse.id"
                          @open-menu="$emit('open-menu', $event)"/>

        <li v-if="showTopCourses">
            <hr class="separator">
        </li>

        <course-list-item v-for="course in (filteredCourses || sortedCourses)"
                          :key="`sorted-course-${course.id}`"
                          :course="course"
                          :current-id="currentCourse && currentCourse.id"
                          @open-menu="$emit('open-menu', $event)"/>
    </ul>
    <span v-else class="sidebar-list no-items-text">
        You don't have any courses yet.
    </span>

    <hr class="separator"
        v-if="showAddButton">

    <b-button-group>
        <b-btn class="add-course-button sidebar-footer-button"
               :id="addButtonId"
               v-if="showAddButton"
               v-b-popover.hover.top="'Add new course'">
            <icon name="plus" style="margin-right: 0;"/>
            <b-popover :target="addButtonId" triggers="click"
                       placement="top">
                <submit-input placeholder="New course name"
                              @create="createNewCourse"/>
            </b-popover>
        </b-btn>
    </b-button-group>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import moment from 'moment';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';

import { cmpNoCase } from '@/utils';

import SubmitInput from '../SubmitInput';
import CourseListItem from './CourseListItem';

let idNum = 0;

export default {
    name: 'course-list',

    props: {
        data: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            filter: '',
            addButtonId: `course-add-btn-${idNum++}`,
            showAddButton: false,
        };
    },

    computed: {
        ...mapGetters('courses', ['courses']),

        topCourses() {
            const now = moment();
            function closestDeadline(course) {
                return Math.min(...course.assignments.map(
                    assig => Math.abs(moment(assig.deadline).diff(now)),
                ));
            }

            const lookup = Object.values(this.courses).reduce((res, course) => {
                res[course.id] = closestDeadline(course);
                return res;
            }, {});

            return Object.values(this.courses).sort(
                (a, b) => lookup[a.id] - lookup[b.id],
            ).slice(0, 3);
        },

        showTopCourses() {
            return !this.filter &&
                this.sortedCourses.length >= this.topCourses.length + 2;
        },

        sortedCourses() {
            return Object.values(this.courses).sort(
                (a, b) => cmpNoCase(a.name, b.name),
            );
        },

        filteredCourses() {
            if (!this.filter) {
                return null;
            }

            const filterParts = this.filter.toLocaleLowerCase().split(' ');

            return this.sortedCourses.filter(course =>
                filterParts.every(part =>
                    course.name.toLocaleLowerCase().indexOf(part) > -1));
        },

        currentCourse() {
            return this.courses[this.$route.params.courseId];
        },

    },

    async mounted() {
        this.$root.$on('sidebar::reload', this.reload);

        this.$hasPermission('can_create_courses').then((create) => {
            this.showAddButton = create;
        });

        const res = this.loadCourses();
        if (res != null) {
            this.$emit('loading');
            await res;
            this.$emit('loaded');
        }

        await this.$nextTick();

        const activeEl = document.activeElement;
        if (!activeEl ||
            !activeEl.matches('input, textarea') ||
            activeEl.closest('.sidebar .submenu')) {
            this.$refs.filter.focus();
        }
    },

    destroyed() {
        this.$root.$off('sidebar::reload', this.reload);
    },

    methods: {
        ...mapActions('courses', ['loadCourses', 'reloadCourses']),

        reload() {
            this.$emit('loading');
            this.reloadCourses().then(() => {
                this.$emit('loaded');
            });
        },

        createNewCourse(name, resolve, reject) {
            this.$http.post('/api/v1/courses/', {
                name,
            }).then(({ data: course }) => {
                this.$emit('loading');
                resolve();
                return this.reloadCourses().then(() => {
                    this.$emit('loaded');
                    this.$router.push({
                        name: 'manage_course',
                        params: {
                            courseId: course.id,
                        },
                    });
                });
            }).catch((err) => {
                reject(err.response.data.message);
            });
        },
    },

    components: {
        CourseListItem,
        Icon,
        SubmitInput,
    },
};
</script>
