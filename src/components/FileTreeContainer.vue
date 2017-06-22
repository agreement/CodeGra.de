<template>
    <div class="file-tree-container">
        <b-form-fieldset>
            <div class="btn-group-vertical">
                <b-button @click="downloadArchive()" variant="primary" title="Download archive">
                    <icon name="download" class="download-icon"></icon>
                    <span class="text">Download archive</span>
                </b-button>
                <b-button @click="downloadFeedback()" variant="primary" title="Download feedback">
                    <icon name="download" class="download-icon"></icon>
                    <span class="text">Download feedback</span>
                </b-button>
            </div>
        </b-form-fieldset>
        <loader class="text-center" :scale="3" v-if="!fileTree"></loader>
        <file-tree :collapsed="false" :tree="fileTree" v-else></file-tree>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';

import { bFormFieldset, bButton } from 'bootstrap-vue/lib/components';

import FileTree from './FileTree';
import Loader from './Loader';

export default {
    name: 'file-tree-container',

    props: {
        fileTree: {
            type: Object,
        },
    },

    data() {
        return {
            submissionId: this.$route.params.submissionId,
        };
    },

    methods: {
        downloadArchive() {
            window.open(`/api/v1/submissions/${this.submissionId}?type=zip`);
        },
        downloadFeedback() {
            window.open(`/api/v1/submissions/${this.submissionId}?type=feedback`);
        },
    },

    components: {
        FileTree,
        Icon,
        Loader,
        bFormFieldset,
        bButton,
    },
};
</script>

<style lang="less" scoped>
.file-tree-container {
    .download-icon {
        position: relative;
        top: 2px;
        margin-right: .66em;
    }
}

</style>
