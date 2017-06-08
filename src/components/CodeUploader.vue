<template>
    <div id='upload'>
        <dropzone
          ref='dz'
          id='dz-upload'
          :url=options.url
          :useCustomDropzoneOptions=true
          :dropzoneOptions=options>
        </dropzone>
        <button type="button" v-on:click="submit">Submit</button>
    </div>
</template>

<script>
    import Dropzone from 'vue2-dropzone';

    const htmlTemplate = `
    <div class="dz-preview dz-file-preview">
        <div class="dz-image" style="width: 200px;height: 200px"><img data-dz-thumbnail /></div>
        <div class="dz-details">
            <div class="dz-filename"><span data-dz-name></span></div>
            <div class="dz-size"><span data-dz-size></span></div>
        </div>
        <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>
        <div class="dz-error-message"><span data-dz-errormessage></span></div>
        <div class="dz-success-mark"><i class="fa fa-check"></i></div>
        <div class="dz-error-mark"><i class="fa fa-close"></i></div>
    </div>
`;

    export default {
        name: 'Upload',
        components: {
            Dropzone,
        },
        props: {
            assignmentId: {
                type: Number,
                default: 0,
            },
            workId: {
                type: Number,
                default: 0,
            },
            maxFilesize: {
                type: Number,
                default: 16,
            },
            maxFiles: {
                type: Number,
                default: 1,
            },
        },
        data() {
            return {
                options: {
                    url: `api/v1/assignments/${this.assignmentId}/works/${this.workId}/file`,
                    method: 'POST',
                    maxFiles: this.maxFiles,
                    maxFilesize: this.maxFilesize,
                    filesizeBase: 1000,
                    paramName: 'file',
                    createImageThumbnails: false,
                    autoProcessQueue: false,
                    addRemoveLinks: true,
                    dictDefaultMessage: 'Drop code here or click to upload',
                    previewTemplate: htmlTemplate,
                },
            };
        },
        methods: {
            submit: function submit() {
                this.$refs.dz.processQueue();
            },
        },
    };
</script>

<style>
.dz-remove {
    right: 15px;
}
.dz-image {
    width: 200px;
    height: 200px;
}
</style>
