<template>
<li :class="{ 'light-selected': selected }"
    class="sidebar-list-item assignment-list-item">
    <router-link class="sidebar-item name"
                 :class="{ selected: submissionsSelected || (small && selected) }"
                 :to="submissionsRoute(assignment)">
        <div class="assignment-wrapper">
            <span class="assignment">{{ assignment.name }}</span>

            <assignment-state :assignment="assignment"
                              :editable="false"
                              v-if="!small"
                              size="sm"/>
            <small v-else class="deadline">Due {{ readableDeadline }}</small>
        </div>
        <small v-if="!small" class="deadline">Due {{ readableDeadline }}</small>
        <small v-if="!small" class="course">{{ assignment.course.name }}</small>
    </router-link>
    <router-link class="sidebar-item manage-link"
                 v-if="assignment.canManage && !small"
                 :class="{ selected: manageSelected }"
                 :to="manageRoute(assignment)">
        <icon name="gear"/>
    </router-link>
</li>
</template>

<script>
import moment from 'moment';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/gear';

import AssignmentState from '../AssignmentState';

export default {
    name: 'assignment-list-item',

    props: {
        assignment: {
            type: Object,
            required: true,
        },

        small: {
            type: Boolean,
            default: false,
        },

        currentId: {
            type: Number,
            default: null,
        },

        now: {
            type: Object,
            default: null,
        },

        sbloc: {
            default: undefined,
        },
    },

    computed: {
        selected() {
            return this.assignment.id === this.currentId;
        },

        submissionsSelected() {
            return this.selected && this.$route.name === 'assignment_submissions';
        },

        manageSelected() {
            return this.selected && this.$route.name === 'manage_assignment';
        },

        readableDeadline() {
            return moment(this.assignment.deadline).from(this.now);
        },

    },

    methods: {
        submissionsRoute(assignment) {
            return {
                name: 'assignment_submissions',
                params: {
                    courseId: assignment.course.id,
                    assignmentId: assignment.id,
                },
                query: {
                    sbloc: this.sbloc,
                },
            };
        },

        manageRoute(assignment) {
            return {
                name: 'manage_assignment',
                params: {
                    courseId: assignment.course.id,
                    assignmentId: assignment.id,
                },
                query: {
                    sbloc: this.sbloc,
                },
            };
        },
    },

    components: {
        Icon,
        AssignmentState,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.name {
    flex: 1 1 auto;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
}

.manage-link {
    flex: 0 0 auto;
    padding-top: 6px;
}

a {
    text-decoration: none;
    color: inherit;
}

.deadline {
    display: block;
    margin-bottom: -5px;
}

.assignment-wrapper {
    display: flex;
    max-width: 100%;
    text-overflow: ellipsis;
    align-items: baseline;
    .deadline {
        padding-left: 2px;
    }
    .assignment {
        line-height: 1.1;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1 1 auto;
    }
    margin-bottom: 2px;
}
</style>
