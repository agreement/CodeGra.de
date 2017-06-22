<template>
    <div id="pdf-viewer"></div>
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
            return `/api/v1/code/${this.id}?type=binary`;
        },
    },

    methods: {
        embedPdf() {
            let options = {};
            if (!PDFObject.supportsPDFs) {
                options = {
                    forcePDFJS: true,
                    PDFJS_URL: '/static/web/viewer.html',
                };
            }
            PDFObject.embed(this.url, '#pdf-viewer', options);
        },
    },
};
</script>

<style>
.pdfobject-container {
    height: 100%;
}
</style>
