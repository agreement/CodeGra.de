<template>
    <div id='upload'>
        <h2>Submit files: (max: {{options.maxFiles}})</h2>
        <dropzone
          ref='dz'
          id='dz-upload'
          :url=options.url
          :useCustomDropzoneOptions=true
          :dropzoneOptions=options
          v-on:vdropzone-error="error">
        </dropzone>
        <ul id="uploads" class="list-group">

        </ul>
        <div style='align:center'>
        <button class="btn btn-primary upload" v-on:click="submit">Upload</button>
        <button class="btn btn-danger upload" v-on:click="removeAll">Remove all</button>
        </div>
    </div>
</template>

<script>
    import Dropzone from 'vue2-dropzone';

    const htmlTemplate = `
    <li class="list-group-item s-file">
        <span class="error label label-as-badge label-danger">Upload error</span>
        <span class="warning label label-as-badge label-warning" data-dz-errormessage></span>
        <span class="success label label-as-badge label-success">Uploaded</span>
        <span class="name" data-dz-name></span>
        <span class="size" data-dz-size></span>
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
                    previewTemplate: htmlTemplate,
                    // previewsContainer: '#uploads',
                },
            };
        },
        methods: {
            submit: function submit() {
                this.$refs.dz.processQueue();
            },
            removeAll: function removeAll() {
                this.$refs.dz.removeAllFiles();
            },
            error: function error(file, response) {
                let message = null;
                if (typeof response === 'string') {
                    message = response;
                } else {
                    message = response.message;
                }
                const child = file.previewElement.children[0];
                child.innerText = message;
            },
        },
    };
</script>

<style>
.dz-details {
    width: 100%;
    background-color: lightblue;
    padding: 5px;
}

.dz-error .dz-details {
    background-color: yellow;
}

.dz-success .dz-details {
    background-color: lightgreen;
}
/*
.s-file {
    padding: 5px;
    margin: 5px;
    background-color: lightgray;
}
*/
.s-file {
    overflow: hidden;
    text-overflow: ellipsis;
    padding-right: 60px;
}

.s-file .name {
    white-space: pre;
}

.s-file .size {
    position: absolute;
    right: 10px;
    top: 10px;
}

.s-file .label {
    text-overflow: ellipsis;
    overflow: hidden;
}

.s-file.dz-error.dz-processing .warning, .s-file .warning, .s-file .success, .s-file .error {
    display: none;
}

.s-file.dz-error .warning, .s-file.dz-success .success, .s-file.dz-error.dz-processing .error {
    display: block;
}

.s-file.dz-success {
    background-color: #dff0d8;
    color: #3c763d
}

.s-file.dz-error {
    background-color: #fcf8e3;
    color: #8a6d3b;
}

.s-file.dz-processing.dz-error {
    background-color: #f2dede;
    color: #a94442;
}


</style>
