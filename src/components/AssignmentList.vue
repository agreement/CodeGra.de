<template>
<div>
    <b-form-fieldset class="table-control">
        <b-input-group>
            <input v-model="filter"
                   class="form-control"
                   placeholder="Type to Search"
                   v-on:keyup.enter="submit"/>
            <b-input-group-append is-text
                                  v-for="role in getUniqueRoles()"
                                  :key="role">
                <b-form-checkbox class="input-group-addon"
                                 :checked="checkboxRoles[role] === true"
                                 @change="setRoleFilter(role)"
                                 :key="`role-${role}`">
                    {{ role }}
                </b-form-checkbox>
            </b-input-group-append>
            <b-input-group-append>
                    <b-button class="btn-info" :class="{ 'btn-outline-info': !toggles.hidden}"
                              @click="toggleFilter('hidden')"
                              v-if="canSeeHidden"
                              v-b-popover.top.hover="'Hidden'">
                        <icon name="eye-slash"></icon>
                    </b-button>
            </b-input-group-append>
            <b-input-group-append>
                    <b-button class="btn-danger" :class="{ 'btn-outline-danger': !toggles.submitting }"
                              @click="toggleFilter('submitting')"
                              v-b-popover.top.hover="'Submitting'">
                        <icon name="clock-o"></icon>
                    </b-button>
            </b-input-group-append>
            <b-input-group-append>
                    <b-button class="btn-warning" :class="{ 'btn-outline-warning': !toggles.grading }"
                              @click="toggleFilter('grading')"
                              v-b-popover.top.hover="'Grading'">
                        <icon name="pencil"></icon>
                    </b-button>
            </b-input-group-append>
            <b-input-group-append>
                    <b-button class="btn-success" :class="{ 'btn-outline-success': !toggles.done }"
                              @click="toggleFilter('done')"
                              v-b-popover.top.hover="'Done'">
                        <icon name="check"></icon>
                    </b-button>
            </b-input-group-append>
        </b-input-group>
        </b-form-fieldset>

        <b-table striped hover
                 ref="table"
                 @row-clicked="gotoAssignment"
                 :items="assignments"
                 :fields="fields"
                 :current-page="currentPage"
                 :sort-compare="sortTable"
                 :filter="filterItems"
                 sort-by="deadline"
                 :show-empty="true">
            <template slot="name" slot-scope="item">
                <a class="invisible-link"
                   href="#"
                   @click.prevent>
                    {{item.value ? item.value : '-'}}
                </a>
            </template>
            <template slot="course_name" slot-scope="item">
                {{item.item.course.name ? item.item.course.name : '-'}}
            </template>
            <template slot="deadline" slot-scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="course_role" slot-scope="item">
                {{item.item.course.role ? item.item.course.role : '-'}}
            </template>
            <template slot="state" slot-scope="item">
                <assignment-state :assignment="item.item"/>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

import { cmpOneNull, cmpNoCase } from '@/utils';
import * as assignmentState from '../store/assignment-states';

import AssignmentState from './AssignmentState';

export default {
    name: 'assignment-list',

    props: {
        assignments: {
            type: Array,
            default: [],
        },
        canSeeHidden: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            assignmentState,
            filter: '',
            pushedUrl: true,
            toggles: {
                hidden: false,
                submitting: true,
                grading: false,
                done: true,
            },
            currentPage: 1,
            fields: [
                {
                    key: 'name',
                    label: 'Assignment',
                    sortable: true,
                    index: 0,
                }, {
                    key: 'course_name',
                    label: 'Course',
                    sortable: true,
                    index: 1,
                }, {
                    key: 'deadline',
                    label: 'Deadline',
                    sortable: true,
                    index: 2,
                }, {
                    key: 'course_role',
                    label: 'Role',
                    sortable: true,
                    index: 3,
                }, {
                    key: 'state',
                    label: 'State',
                    sortable: true,
                    class: 'text-center',
                    index: 4,
                },
            ],
            checkboxRoles: {},
        };
    },

    watch: {
        $route() {
            if (this.pushedUrl) {
                this.pushedUrl = false;
                return;
            }
            this.submit();
        },
    },

    mounted() {
        const q = this.$route.query;
        const nullOrTrue = val => val == null || val === 'true';
        this.toggles.hidden = nullOrTrue(q.hidden);
        this.toggles.submitting = nullOrTrue(q.submitting);
        this.toggles.grading = nullOrTrue(q.grading);
        this.toggles.done = nullOrTrue(q.done);

        let roles;
        if (q.roles === undefined) {
            roles = this.getUniqueRoles();
        } else {
            roles = JSON.parse(q.roles);
        }
        roles.forEach((val) => {
            this.$set(this.checkboxRoles, val, true);
        });

        this.filter = q.q;
    },

    methods: {
        sortTable(a, b, sortBy) {
            if (typeof a[sortBy] === 'number' && typeof b[sortBy] === 'number') {
                return a[sortBy] - b[sortBy];
            } else if (sortBy === 'name' || sortBy === 'deadline') {
                const first = a[sortBy];
                const second = b[sortBy];

                const ret = cmpOneNull(first, second);

                return ret === null ? cmpNoCase(first, second) : ret;
            } else if (sortBy === 'course_name') {
                const first = a.course;
                const second = b.course;

                const ret = cmpOneNull(first, second);

                return ret === null ? cmpNoCase(first.name, second.name) : ret;
            } else if (sortBy === 'course_role') {
                const first = a.course;
                const second = b.course;

                const ret = cmpOneNull(first, second);

                return ret === null ? cmpNoCase(first.role, second.role) : ret;
            } else if (sortBy === 'state') {
                const first = a.state;
                const second = b.state;

                const ret = cmpOneNull(first, second);

                const states = [
                    assignmentState.HIDDEN,
                    assignmentState.SUBMITTING,
                    assignmentState.GRADING,
                    assignmentState.DONE,
                ];
                return ret === null ? states.indexOf(first) - states.indexOf(second) : ret;
            }
            return 0;
        },

        filterItems(item) {
            if (!this.checkboxRoles[item.course.role]) {
                return false;
            }

            if (!this.filterState(item)) {
                return false;
            } else if (!this.filter) {
                return true;
            }
            const terms = {
                name: item.name.toLowerCase(),
                course_name: item.course.name.toLowerCase(),
                course_role: item.course.role,
                deadline: item.deadline,
            };
            return this.filter.toLowerCase().split(' ').every(word =>
                Object.keys(terms).some(key =>
                    terms[key].indexOf(word) >= 0));
        },

        setRoleFilter(role) {
            this.$set(this.checkboxRoles, role, !this.checkboxRoles[role]);
            this.submit();
        },

        getUniqueRoles() {
            const seen = {};
            const res = [];
            this.assignments.forEach((assig) => {
                if (!seen[assig.course.role]) {
                    seen[assig.course.role] = true;
                    res.push(assig.course.role);
                }
            });
            return res;
        },

        filterState(item) {
            switch (item.state) {
            case assignmentState.SUBMITTING: return this.toggles.submitting;
            case assignmentState.GRADING: return this.toggles.grading;
            case assignmentState.DONE: return this.toggles.done;
            case assignmentState.HIDDEN: return this.toggles.hidden;
            default: throw TypeError(`Unknown assignment state "${item.state}"`);
            }
        },

        matchesWord(item, word) {
            return item.name.indexOf(word) >= 0 ||
                item.course.name.indexOf(word) >= 0 ||
                item.deadline.indexOf(word) >= 0;
        },

        toggleFilter(filter) {
            this.toggles[filter] = !this.toggles[filter];
            this.submit();
        },

        gotoAssignment(assignment) {
            this.submit();
            this.$router.push({
                name: 'assignment_submissions',
                params: {
                    courseId: assignment.course.id,
                    assignmentId: assignment.id,
                },
            });
        },

        submit() {
            this.pushedUrl = true;
            const query = Object.assign({}, this.toggles);
            if (this.filter) {
                query.q = this.filter;
            }

            const q = [];
            Object.keys(this.checkboxRoles).forEach((key) => {
                if (this.checkboxRoles[key]) {
                    q.push(key);
                }
            });
            query.roles = JSON.stringify(q);

            this.$router.replace({ query });
        },
    },

    components: {
        AssignmentState,
        Icon,
    },
};
</script>
