<template>
    <div id="pdf-viewer"></div>
</template>

<script>
import PDFObject from 'pdfobject';

export default {
    name: 'pdf-viewer',

    props: ['id'],

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
            return `/api/v1/code/${this.id}?type=pdf`;
        },
    },

    methods: {
        embedPdf() {
            let options = {};
            if (!PDFObject.supportsPDFs) {
                options = {
                    forcePDFJS: true,
                    PDFJS_URL: '/static/vendor/pdf.js/web/viewer.html',
                };
            }
            this.$http.get(this.url).then(({ data }) => {
                const pdfUrl = data.name;
                PDFObject.embed(`/api/v1/files/${pdfUrl}?not_as_attachment&mime=application/pdf`, '#pdf-viewer', options);
            });
        },
    },
};
</script>

<style>
.pdfobject-container {
    height: 100%;
}
</style>
