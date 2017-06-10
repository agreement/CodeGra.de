<template>
    <div class="panel panel-default panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Submit files: (max: {{options.maxFiles}})</h4>
        </div>

        <!-- <div class="panel-body"> -->
            <dropzone class="panel-body container"
              ref='dz'
              id='dz-upload'
              v-bind:url="options.url"
              v-bind:useCustomDropzoneOptions="true"
              v-bind:dropzoneOptions="options"
              v-on:vdropzone-error="error"
              v-on:vdropzone-total-upload-progress="progress"
              v-on:vdropzone-file-added="fileAdded"
              v-on:vdropzone-success="success"
              v-on:vdropzone-queue-complete="queueComplete"
            >
            </dropzone>
        <!-- </div> -->
        <div class="panel-footer">
        <button
          class="btn btn-primary btn-sm upload"
          v-on:click="upload"
          v-bind:class="{disabled: startedUpload}"
        >Upload
        </button>   
        <div class="progress">
                <div ref='progress' class="progress-bar progress-bar-info progress-bar-striped"/>
            </div>
        </div>
    </div>
</template>

<script>
    import Dropzone from 'vue2-dropzone';

    const htmlTemplate = `
    <li class="list-group-item row file">
        <div class="col-xs-10"><span class="name" data-dz-name></span></div>
        <div class="col-xs-auto"><span class="size" data-dz-size></span></div>
    </li>
    `;


    export default {
        name: 'Upload',
        components: {
            Dropzone,
        },
        props: {
            workId: {
                type: Number,
                default: 0,
            },
            maxFilesize: {
                type: Number,
                default: 64,
            },
            maxFiles: {
                type: Number,
                default: 10,
            },
        },
        data() {
            return {
                startedUpload: false,
                options: {
                    url: `api/v1/works/${this.workId}/file`,
                    method: 'POST',
                    maxFiles: this.maxFiles,
                    maxFilesize: this.maxFilesize,
                    filesizeBase: 1000,
                    paramName: 'file',
                    createImageThumbnails: false,
                    autoProcessQueue: false,
                    addRemoveLinks: false,
                    dictDefaultMessage: 'Drop code here or click to submit',
                    uploadMultiple: true,
                    parallelUploads: this.maxFiles,
                    previewTemplate: htmlTemplate,
                    // previewsContainer: '#uploads',
                },
            };
        },
        methods: {
            upload: function upload() {
                if (!this.startedUpload) {
                    this.startedUpload = true;
                    this.$refs.dz.processQueue();
                }
            },
            removeAll: function removeAll() {
                this.$refs.dz.removeAllFiles();
            },
            error: function error(file, response) {
                let message = null;
                if (typeof response === 'string') {
                    // Internal dropzone response
                    message = response;
                } else {
                    // Server response
                    message = response.message;
                }
                file.previewElement.classList.remove('list-group-item-info');
                file.previewElement.classList.add('list-group-item-danger');
                file.previewElement.setAttribute('title', message);
            },
            progress: function progress(totalProgress) {
                this.$refs.progress.style.width = `${totalProgress}%`;
            },
            fileAdded: function fileAdded(file) {
                if (this.startedUpload) {
                    this.$refs.dz.removeFile(file);
                } else {
                    file.previewElement.classList.add('list-group-item-info');
                }
            },
            success: function success(file) {
                file.previewElement.classList.remove('list-group-item-info');
                file.previewElement.classList.add('list-group-item-success');
            },
            queueComplete: function queueComplete() {
                this.$refs.progress.classList.remove('progress-bar-info');
                this.$refs.progress.classList.add('progress-bar-success');
            },

        },
    };
</script>
<style>
.file div.col-xs-10 {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: pre;
}
.file div.col-xs-auto {
    overflow: visible;
    white-space: pre;
}
.progress {
    height: 20px;
    background-color: white;
}
</style>
