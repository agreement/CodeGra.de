<template>
    <div
        class="manage-course">
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

        <b-modal
            class="rubric-modal"
            size="lg"
            :visible="!!this.assignmentId"
            @hidden="assignmentId = null">
            <rubric-editor
                :assignmentId="assignmentId"/>
        </b-modal>
    </div>
</template>

<script>
import ManageAssignment from './ManageAssignment';
import RubricEditor from './RubricEditor';

export default {
    name: 'manage-course',

    props: {
        assignments: {
            type: Array,
            default: [],
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
    },

    components: {
        RubricEditor,
        ManageAssignment,
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
