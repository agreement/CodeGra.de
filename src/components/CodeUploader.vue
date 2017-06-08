<template>
    <div id='upload'>
        <dropzone
          id='dz-upload'
          :url=options.url
          :useCustomDropzoneOptions=true
          :dropzoneOptions=options>
            <!-- <input type="hidden" name="token" value="xxx"> -->
        </dropzone>
    </div>
</template>

<script>
    import Dropzone from 'vue2-dropzone';

    export default {
        name: 'Upload',
        components: {
            Dropzone,
        },
        data() {
            return {
                options: {
                    url: 'api/upload-code',
                    method: 'POST',
                    maxFiles: 1,
                    maxFilesize: 16,
                    filesizeBase: 1024 * 1024,
                    paramName: 'file',
                    createImageThumbnails: false,
                    headers: {
                        student: 11,
                        assignment: 12,
                    },
                },
            };
        },
    };
</script>
