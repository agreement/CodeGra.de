<template>
    <div class="file-tree-container">
        <b-form-fieldset class="button-bar">
            <b-button @click="downloadType('zip')" variant="primary" title="Download archive">
                <icon name="download"></icon>
                <span>Archive</span>
            </b-button>
            <b-button @click="downloadType('feedback')" v-if="canSeeFeedback" variant="primary" title="Download feedback">
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
        downloadType(type) {
            this.$http.get(`/api/v1/submissions/${this.submissionId}?type=${type}`).then(({ data }) => {
                const params = new URLSearchParams();
                params.append('name', data.output_name);
                window.open(`/api/v1/files/${data.name}?${params.toString()}`);
            });
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
