<template>
    <div class="page assignment">
        <ol>
            <li v-for="a in assignments">
                <a v-bind:href="submissionURL(a)">
                    {{ a.name }}
                </a>
            </li>
        </ol>
    </div>
</template>

<script>
export default {
    name: 'assignments-page',

    data() {
        return {
            studentId: this.$route.params.studentId,
            assignments: [],
        };
    },

    mounted() {
        this.$http.get(`/api/v1/students/${this.studentId}/assignments`).then((data) => {
            this.assignments = data.body;
        });
    },

    methods: {
        submissionURL(assignment) {
            return `#/students/${this.studentId}/assignments/${assignment.id}/submit`;
        },
    },
};
</script>
