<template>
    <b-list-group class="manage-course">
        <b-form-fieldset>
            <b-input-group>
                <b-form-input v-model="filter"
                    placeholder="Type to search"
                    @keyup.enter="submit"></b-form-input>
            </b-input-group>
        </b-form-fieldset>
        <b-list-group-item v-for="a in assignments" :key="a.id"
            v-if="shouldShowAssignment(a)">
            <manage-assignment :assignment="a"></manage-assignment>
        </b-list-group-item>
    </b-list-group>
</template>

<script>
import ManageAssignment from './ManageAssignment';

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
    },

    components: {
        ManageAssignment,
    },
};
</script>
