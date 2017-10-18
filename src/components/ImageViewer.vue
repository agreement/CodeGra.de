<template>
    <div class="image-viewer form-control">
        <loader v-if="loading"/>
        <img :src="imgURL"
             :title="name"
             v-else-if="imgURL !== ''"/>
        <b-alert variant="danger"
                 :show="error !== ''">
            {{ error }}
        </b-alert>
    </div>
</template>

<script>
import Loader from './Loader';

export default {
    name: 'image-viewer',

    props: {
        id: {
            type: Number,
            default: -1,
        },
        name: {
            type: String,
            default: '',
        },
    },

    data() {
        return {
            imgURL: '',
            loading: true,
            error: '',
        };
    },

    watch: {
        id() {
            this.embedImg();
        },
    },

    mounted() {
        this.embedImg();
    },

    methods: {
        embedImg() {
            this.loading = true;
            this.error = '';
            this.imgURL = '';
            this.$http.get(`/api/v1/code/${this.id}?type=file-url`).then(({ data }) => {
                this.loading = false;
                this.$emit('load');
                this.imgURL = `/api/v1/files/${data.name}?not_as_attachment&mime=${this.getMimeType()}`;
            }, ({ response }) => {
                this.error = `An error occurred while loading the image: ${response.data.message}.`;
            });
        },

        getMimeType() {
            const ext = this.name.split('.').reverse()[0];
            const types = {
                gif: 'image/gif',
                jpg: 'image/jpeg',
                jpeg: 'image/jpeg',
                png: 'image/png',
                svg: 'image/svg%2Bxml',
            };
            return types[ext];
        },
    },

    components: {
        Loader,
    },
};
</script>

<style lang="less" scoped>
.image-viewer {
    padding: 0;
    overflow: hidden;
    text-align: center;

    img {
        max-width: 100%;
        max-height: 100%;
    }
}
</style>
