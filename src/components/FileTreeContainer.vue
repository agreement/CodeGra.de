<template>
    <div class="file-tree-container">
        <b-form-fieldset class="button-bar">
            <b-button @click="downloadArchive()" variant="primary" title="Download archive">
                <icon name="download"></icon>
                <span>Archive</span>
            </b-button>
            <b-button @click="downloadFeedback()" v-if="canSeeFeedback" variant="primary" title="Download feedback">
                <icon name="download"></icon>
                <span>Feedback</span>
            </b-button>
        </b-form-fieldset>
        <loader class="text-center" :scale="3" v-if="!fileTree"></loader>
        <file-tree class="form-control" :collapsed="false" :tree="fileTree" v-else></file-tree>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';

import FileTree from './FileTree';
import Loader from './Loader';

export default {
    name: 'file-tree-container',

    props: {
        fileTree: {
            type: Object,
        },
        canSeeFeedback: {
            type: Boolean,
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
    },
};
</script>

<style lang="less" scoped>
.file-tree-container {
    display: flex;
    flex-direction: column;
}

.button-bar {
    flex-grow: 0;
    flex-shrink: 0;
}

.file-tree {
    flex-grow: 0;
    flex-shrink: 1;
    overflow: auto;
}
</style>
