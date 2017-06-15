<template>
    <div id="pdf-viewer">
    </div>
</template>

<script>
import PDFObject from 'pdfobject';

export default {
    name: 'pdf-viewer',

    props: {
        id: {
            type: Number,
            required: true,
        },
    },

    watch: {
        id() {
            this.embedPdf();
        },
    },

    mounted() {
        this.embedPdf();
    },

    computed: {
        url() {
            return `/api/v1/binary/${this.id}`;
        },
    },

    methods: {
        embedPdf() {
            PDFObject.embed(this.url, '#pdf-viewer');
        },
    },
};
</script>

<style>
.pdfobject-container {
    height: 70vh;
}
</style>
