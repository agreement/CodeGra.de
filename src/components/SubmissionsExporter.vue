<template>
    <b-button :href="link">Export as CSV</b-button>
</template>

<script>
export default {
    name: 'submissions-exporter',

    props: ['assignment'],

    computed: {
        fileName: function fileName() {
            return this.assignment ? `${this.assignment.course_name}-${this.assignment.name}.csv` : 'export.csv';
        },
        link: function line() {
            return this.assignment ? `/api/v1/assignments/${this.assignment.id}/submissions/?csv=${this.fileName}` : null;
        },
    },
};
</script>
