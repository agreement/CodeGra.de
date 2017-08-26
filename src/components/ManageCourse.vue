<template>
    <div class="manage-course">
        <div class="assignment-manager collapse-wrapper">
            <h3 @click="toggleDiv('assignment-manager')">Assignments</h3>
            <b-collapse id="assignment-manager" visible>
                <b-form-fieldset>
                    <b-input-group>
                        <b-form-input
                            v-model="filter"
                            placeholder="Type to search"
                            @keyup.enter="submit"/>
                    </b-input-group>
                </b-form-fieldset>
                <b-list-group
                    class="manage-course">
                    <b-list-group-item
                        v-if="shouldShowAssignment(a)"
                        v-for="a in assignments"
                        :key="a.id">
                        <manage-assignment
                            :assignment="a"
                            @showRubric="showRubric"/>
                    </b-list-group-item>
                </b-list-group>
            </b-collapse>

            <b-modal
                class="rubric-modal"
                size="lg"
                :visible="!!this.assignmentId"
                @hidden="assignmentId = null">
                <rubric-editor
                    :assignmentId="assignmentId"/>
            </b-modal>

        </div>

        <div class="collapse-wrapper">
            <h3 @click="toggleDiv('users-manager')">Users</h3>
            <b-collapse id="users-manager">
                <users-manager :course="course"/>
            </b-collapse>
        </div>
        <div class="collapse-wrapper">
            <h3 @click="toggleDiv('permissions-manager')">Roles</h3>
            <b-collapse id="permissions-manager">
                <permissions-manager/>
            </b-collapse>
        </div>
    </div>
</template>

<script>
import UsersManager from './UsersManager';
import PermissionsManager from './PermissionsManager';
import ManageAssignment from './ManageAssignment';
import RubricEditor from './RubricEditor';

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
    },

    data() {
        return {
            filter: this.$route.query.q,
            assignmentId: null,
        };
    },

    methods: {
        shouldShowAssignment(assignment) {
            if (!this.filter) return true;
            const name = assignment.name.toLowerCase();
            return name.indexOf(this.filter.toLowerCase()) > -1;
        },

        submit() {
            const query = {};
            if (this.filter) query.q = this.filter;
            this.$router.replace({ query });
        },

        showRubric(assignmentId) {
            this.assignmentId = assignmentId;
        },
        toggleDiv(id) {
            this.$root.$emit('collapse::toggle', id);
        },
    },

    components: {
        RubricEditor,
        ManageAssignment,
        UsersManager,
        PermissionsManager,
    },
};
</script>

<style lang="less">
@media (min-width: 992px) {
    .rubric-modal .modal-lg {
        max-width: 1280px;
    }
}
</style>

<style lang="less" scoped>
.collapse-wrapper {
    margin-top: 1em;
    background-color: #fff;
    border: 1px solid rgba(0, 0, 0, 0.125);
    padding: 0.75rem 1.25rem;
    border-radius: 0.25rem;
    h3 {
        cursor: pointer;
        margin-bottom: 0;
    }
    h3 + div {
        margin-top: 0.5em;
    }
}
.collapse-wrapper:first-child {
    margin-top: 0em;
}
h3 {
    text-align: center;
}
</style>
