<template>
    <div class="file-tree-container">
        <b-form-fieldset>
            <b-button @click="download()" variant="primary" title="Download archive">
                <icon name="download"></icon>
                <span class="text">Download archive</span>
            </b-button>
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
        download() {
            window.open(`/api/v1/submissions/${this.submissionId}?type=zip`);
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
