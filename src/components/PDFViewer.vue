<template>
    <vue-pdf-viewer height="800px" :url="url">
</template>

<script>
import VuePDFViewer from 'vue-instant-pdf-viewer';

export default {
    name: 'pdf-viewer',

    props: {
        id: {
            type: Number,
            required: true,
        },
    },

    computed: {
        url() {
            return `/api/v1/code/${this.id}`;
        },
    },

    components: {
        'vue-pdf-viewer': VuePDFViewer,
    },
};
</script>
