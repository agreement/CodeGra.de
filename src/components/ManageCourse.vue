<template>
    <div class="manage-course">
        <div class="collapse-wrapper"
             v-if="canManageAssignment">

            <h3 class="section-header" @click="toggleDiv('assignment-manager')">
                <a class="invisible-link" href="#" @click.prevent>Assignments</a>
            </h3>

            <b-collapse id="assignment-manager" visible>
                <b-list-group class="assigment-list">
                    <b-list-group-item
                        v-for="a in assignments"
                        :key="a.id">
                        <manage-assignment :assignment="a"
                                           :permissions="permissions"/>
                    </b-list-group-item>

                    <b-list-group-item
                        variant="info"
                        v-if="assignments.length === 0">
                        No assignments found
                    </b-list-group-item>
                </b-list-group>

                <new-assignment
                    v-if="!course.is_lti && permissions.can_create_assignment"
                    style="margin-top: 15px;"
                    :course-id="course.id"
                    @created="(assig) => { $emit('created', assig); }"/>
            </b-collapse>
        </div>

        <div class="collapse-wrapper"
             v-if="permissions.can_edit_course_users">

            <h3 class="section-header" @click="toggleDiv('users-manager')">
                <a class="invisible-link" href="#" @click.prevent>Users</a>
            </h3>

            <b-collapse id="users-manager">
                <users-manager :course="course"/>
            </b-collapse>
        </div>

        <div class="collapse-wrapper"
             v-if="permissions.can_edit_course_roles">

            <h3 class="section-header" @click="toggleDiv('permissions-manager')">
                <a class="invisible-link" href="#" @click.prevent>Roles</a>
            </h3>

            <b-collapse id="permissions-manager">
                <permissions-manager :courseId="course.id"/>
            </b-collapse>
        </div>
    </div>
</template>

<script>
import UsersManager from './UsersManager';
import PermissionsManager from './PermissionsManager';
import ManageAssignment from './ManageAssignment';
import NewAssignment from './NewAssignment';

export default {
    name: 'manage-course',

    props: {
        assignments: {
            type: Array,
            default: [],
        },

        course: {
            type: Object,
            default: {},
        },

        permissions: {
            type: Object,
            default: null,
        },
    },

    computed: {
        canManageAssignment() {
            return Object.keys(this.permissions).some((key) => {
                if (key === 'can_edit_course_roles' || key === 'can_edit_course_users') {
                    return false;
                }
                return this.permissions[key];
            });
        },
    },

    methods: {
        toggleDiv(id) {
            this.$root.$emit('bv::toggle::collapse', id);
        },
    },

    components: {
        NewAssignment,
        ManageAssignment,
        UsersManager,
        PermissionsManager,
    },
};
</script>

<style lang="less" scoped>
.collapse-wrapper {
    margin-top: 1em;
    background-color: #fff;
    border: 1px solid rgba(0, 0, 0, 0.125);
    padding: 0.75rem 1.25rem;
    border-radius: 0.25rem;

    &:first-child {
        margin-top: 0;
    }
}

.section-header {
    margin-bottom: 0;
    text-align: center;
    cursor: pointer;

    + div {
        margin-top: .5em;
    }
}
</style>
