<template>
    <div class="pdf-viewer">
        <loader v-if="loading"/>
        <object :data="pdfURL"
                type="application/pdf"
                width="100%"
                height="100%"
                v-else-if="pdfURL !== ''">
            <b-alert variant="danger" :show="true">
                Your browser doesn't support the PDF viewer. Please download
                the PDF <a class="alert-link" :href="pdfURL">here</a>.
            </b-alert>
        </object>
        <b-alert variant="danger"
                 :show="error !== ''">
            {{ error }}
        </b-alert>
    </div>
</template>

<script>
import Loader from './Loader';

export default {
    name: 'pdf-viewer',

    props: {
        id: {
            type: Number,
            default: -1,
        },
    },

    data() {
        return {
            pdfURL: '',
            loading: true,
            error: '',
        };
    },

    watch: {
        id() {
            this.embedPdf();
        },
    },

    mounted() {
        this.embedPdf();
    },

    methods: {
        embedPdf() {
            this.loading = true;
            this.error = '';
            this.pdfURL = '';
            this.$http.get(`/api/v1/code/${this.id}?type=file-url`).then(({ data }) => {
                this.loading = false;
                this.$emit('load');
                this.pdfURL = `/api/v1/files/${data.name}?not_as_attachment&mime=application/pdf`;
            }, ({ response }) => {
                this.error = `An error occurred while loading the PDF: ${response.data.message}.`;
            });
        },
    },

    components: {
        Loader,
    },
};
</script>

<style lang="less" scoped>
.pdf-viewer {
    position: relative;
}

object {
    position: absolute;
    width: 100%;
    height: 100%;
}
</style>
