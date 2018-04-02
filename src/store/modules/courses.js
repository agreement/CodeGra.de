import Vue from 'vue';
import axios from 'axios';
import moment from 'moment';

import { formatDate } from '@/utils';
import * as types from '../mutation-types';
import { MANAGE_ASSIGNMENT_PERMISSIONS, MANAGE_GENERAL_COURSE_PERMISSIONS } from '../../constants';

const getters = {
    courses: state => state.courses,
    assignments: (state) => {
        if (!state.courses) return {};

        return Object.values(state.courses).reduce(
            (assignments, course) => {
                course.assignments.forEach((assignment) => {
                    assignments[assignment.id] = assignment;
                });
                return assignments;
            },
            {},
        );
    },
};

let first = true;

const actions = {
    loadCourses({ state, commit }) {
        if (first || !Object.values(state.courses).length) {
            return actions.reloadCourses({ commit });
        }

        return null;
    },

    async reloadCourses({ commit }) {
        const params = new URLSearchParams();
        params.append('type', 'course');
        MANAGE_ASSIGNMENT_PERMISSIONS.forEach((perm) => {
            params.append('permission', perm);
        });
        MANAGE_GENERAL_COURSE_PERMISSIONS.forEach((perm) => {
            params.append('permission', perm);
        });
        params.append('permission', 'can_create_assignment');

        let courses;
        let perms;

        try {
            [{ data: courses }, { data: perms }] = await Promise.all([
                axios.get('/api/v1/courses/?extended=true'),
                axios.get('/api/v1/permissions/', {
                    params,
                }),
            ]);
        } catch (_) {
            return commit(types.CLEAR_COURSES);
        }

        const [manageCourses, manageAssigs, createAssigs] = Object.entries(
            perms,
        ).reduce(([course, assig, create], [key, val]) => {
            assig[key] = Object.entries(val).some(
                ([k, v]) => MANAGE_ASSIGNMENT_PERMISSIONS.indexOf(k) !== -1 && v,
            );

            course[key] = Object.entries(val).some(
                ([k, v]) => MANAGE_GENERAL_COURSE_PERMISSIONS.indexOf(k) !== -1 && v,
            );

            create[key] = Object.entries(val).some(
                ([k, v]) => k === 'can_create_assignment' && v,
            );

            return [course, assig, create];
        }, [{}, {}, {}]);

        return commit(
            types.SET_COURSES,
            [courses, manageCourses, manageAssigs, createAssigs, perms],
        );
    },

    updateCourse({ commit }, data) {
        commit(types.UPDATE_COURSE, data);
    },

    updateAssignment({ commit }, data) {
        commit(types.UPDATE_ASSIGNMENT, data);
    },
};

const mutations = {
    [types.SET_COURSES](state, [courses, manageCourses, manageAssigs, createAssigs, perms]) {
        first = false;
        state.courses = courses.reduce((res, course) => {
            course.assignments.forEach((assignment) => {
                const deadline = moment.utc(assignment.deadline, moment.ISO_8601).local();
                const reminderTime = moment.utc(assignment.reminder_time, moment.ISO_8601).local();
                let defaultReminderTime = deadline.clone().add(7, 'days');
                if (defaultReminderTime.isBefore(moment())) {
                    defaultReminderTime = moment().add(3, 'days');
                }

                assignment.course = course;
                assignment.deadline = formatDate(assignment.deadline);
                assignment.created_at = formatDate(assignment.created_at);
                assignment.canManage = manageAssigs[course.id];
                assignment.has_reminder_time = reminderTime.isValid();
                assignment.reminder_time = (
                    reminderTime.isValid() ?
                        reminderTime :
                        defaultReminderTime
                ).format('YYYY-MM-DDTHH:mm');
            });

            course.permissions = perms[course.id];
            course.canManage = manageCourses[course.id];
            course.canCreateAssignments = createAssigs[course.id];

            res[course.id] = course;
            return res;
        }, {});
    },

    [types.CLEAR_COURSES](state) {
        first = true;
        state.courses = {};
    },

    [types.UPDATE_COURSE](state, { courseId, courseProps }) {
        const course = state.courses[courseId];

        if (course == null) {
            throw ReferenceError(`Could not find course: ${courseId}`);
        }

        Object.keys(courseProps).forEach((key) => {
            if (!{}.hasOwnProperty.call(course, key) || key === 'id') {
                throw TypeError(`Cannot set course property: ${key}`);
            }

            Vue.set(course, key, courseProps[key]);
        });
    },

    [types.UPDATE_ASSIGNMENT](state, { assignmentId, assignmentProps }) {
        const assignment = getters.assignments(state)[assignmentId];

        if (assignment == null) {
            throw ReferenceError(`Could not find assignment: ${assignmentId}`);
        }

        Object.keys(assignmentProps).forEach((key) => {
            if (!{}.hasOwnProperty.call(assignment, key) || key === 'id') {
                throw TypeError(`Cannot set assignment property: ${key}`);
            }

            Vue.set(assignment, key, assignmentProps[key]);
        });
    },
};

export default {
    namespaced: true,
    state: {
        courses: {},
    },
    getters,
    actions,
    mutations,
};
