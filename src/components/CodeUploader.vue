<template>
    <div class="card card-primary card-inverse">
        <div class="card-block">
            <h4 class="card-title">Submit files: (max: {{options.maxFiles}})</h4>
        </div>
        <!-- <div class="panel-body"> -->
            <dropzone class="container card-block card-inverse"
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
              v-on:vdropzone-mounted="dropzoneMounted"
            >
                <ul id="queue" class="list-group dropzone-previews">
                    <li ref='previewTemplate' class="list-group-item row file hidden-xs-up">
                        <div class="col-9"><span class="name" data-dz-name></span></div>
                        <div class="col-2"><span class="size" data-dz-size></span></div>
                        <div class="col-1">
                            <button
                              type="button"
                              class="btn btn-danger btn-sm cancel"
                              data-dz-remove>
                                <icon name="times" aria-hidden="true"></icon>
                            </button>
                        </div>
                    </li>
                </ul>
            </dropzone>
        <!-- </div> -->
        <div class="card-block">
        <button
          class="btn btn-success upload"
          v-on:click="upload"
          v-bind:class="{disabled: startedUpload}">
          <icon name="refresh" spin v-if="startedUpload"></icon>
          <span v-else>Upload</span>
        </button>
        <button
          class="btn btn-outline-danger remove"
          v-on:click="removeAll"
          v-bind:class="{disabled: startedUpload}"
        >Remove All
        </button>
        </div>
    </div>
</template>

<script>
    import Dropzone from 'vue2-dropzone';
    import Icon from 'vue-awesome/components/Icon';
    import 'vue-awesome/icons/times';
    import 'vue-awesome/icons/refresh';

    export default {
        name: 'code-uploader',
        components: {
            Dropzone,
            Icon,
        },
        props: {
            assignmentId: {
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
                    url: `/api/v1/assignments/${this.assignmentId}/submission`,
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
                    previewsContainer: '#queue',
                    successmultiple: this.successmMultiple,
                },
            };
        },
        methods: {
            dropzoneMounted: function dropzoneMounted() {
                this.$refs.dz.setOption('previewTemplate', this.$refs.previewTemplate.outerHTML);
            },
            upload: function upload() {
                if (this.$refs.dz.getAcceptedFiles().length === 0) {
                    return;
                }
                if (!this.startedUpload) {
                    const acceptedFiles = this.$refs.dz.getAcceptedFiles();
                    for (let i = 0; i < acceptedFiles.length; i += 1) {
                        acceptedFiles[i].previewElement.children[2].children[0].classList.add('disabled');
                    }
                    this.startedUpload = true;
                    this.$refs.dz.processQueue();
                }
            },
            removeAll: function removeAll() {
                if (!this.startedUpload) {
                    this.$refs.dz.removeAllFiles();
                }
            },
            removeRejected: function removeRejected() {
                if (!this.startedUpload) {
                    const rejectedFiles = this.$refs.dz.getRejectedFiles();
                    for (let i = 0; i < rejectedFiles.length; i += 1) {
                        this.$refs.dz.removeFile(rejectedFiles[i]);
                    }
                }
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
                if (this.startedUpload) {
                    file.previewElement.classList.add('list-group-item-danger');
                } else {
                    file.previewElement.classList.add('list-group-item-warning');
                }
                file.previewElement.setAttribute('title', message);
            },
            progress: function progress(totalProgress) {
                if (this.startedUpload) {
                    this.$refs.progress.style.width = `${totalProgress}%`;
                }
            },
            fileAdded: function fileAdded(file) {
                if (this.startedUpload) {
                    this.$refs.dz.removeFile(file);
                } else {
                    file.previewElement.classList.add('list-group-item-info');
                    file.previewElement.classList.remove('hidden-xs-up');
                }
            },
            success: function success(file) {
                file.previewElement.classList.remove('list-group-item-info');
                file.previewElement.classList.add('list-group-item-success');
            },
            successmMultiple: function successmMultiple(files, response) {
                this.$router.push({ name: 'submission', params: { submissionId: response.id } });
            },
            queueComplete: function queueComplete() {
                this.$refs.progress.classList.remove('progress-bar-striped');
                this.$refs.progress.classList.remove('progress-bar-animated');
                this.$refs.progress.innerHTML = 'Done';
            },
        },
    };
</script>
<style scoped>
.btn {
    border-radius: 0.2em;
    border-width: 0.1em;
    cursor: pointer;
}
.btn-success {
    float:left;
}
.btn-outline-danger {
    float: right;
}
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
    margin: 1em 0 1em 0;
    background-color: #32475b;
}
.card-primary {
    background-color: #2c3e50;
    border-color: #2c3e50;
}
</style>
