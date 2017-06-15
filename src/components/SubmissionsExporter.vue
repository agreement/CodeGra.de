<template>
    <b-button v-on:click="downloadCSV">Export as CSV</b-button>
</template>

<script>
import { bButton } from 'bootstrap-vue/lib/components';

export default {
    name: 'submissions-exporter',

    components: {
        bButton,
    },

    props: ['assignment'],

    computed: {
        fileName: () => `${this.assignment.course_name}-${this.assignment.name}.csv`,
    },

    methods: {
        downloadCSV: function downloadCSV() {
            this.$http.get(`/api/v1/assignments/${this.assignment.course_id}/submissions/?csv=${this.fileName}`).then((response) => {
                const blob = new Blob([response.data], { type: response.headers['content-type'] });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.setAttribute('download', this.fileName);
                link.download = this.fileName;
                link.click();
            });
        },
    },
};
</script>

<style lang="less" scoped>
button {
    cursor: pointer;
}
</style>
