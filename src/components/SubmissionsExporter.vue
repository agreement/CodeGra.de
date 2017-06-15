<template>
    <b-button v-on:click="downloadCSV">Export as CSV</b-button>
</template>

<script type="text/javascript">
import { bButton } from 'bootstrap-vue/lib/components';

export default {
    name: 'submissions-exporter',

    components: {
        bButton,
    },

    props: {
        id: { },
        fileName: { default: null },
    },

    data() {
        return {
            assignmentId: this.id,
            name: this.fileName,
        };
    },

    computed: {
        fileName: function fileName() {
            return this.name != null ? this.name : `${this.assignmentId}.csv`;
        },
    },

    methods: {
        downloadCSV: function downloadCSV() {
            this.$http.get(`/api/v1/assignments/${this.assignmentId}/submissions/?csv=${this.name}`).then((response) => {
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
