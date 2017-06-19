<template>
    <div class="file-tree" v-bind:class="{ collapsed: isCollapsed, }">
        <b-button class="btn" @click="download()" title="Download archive">
            <icon name="download" class="download-icon"></icon><span class="text"> Download archive </span>
        </b-button>
        <div v-on:click="toggle($event)">
            <icon name="caret-right" v-if="isCollapsed"></icon>
            <icon name="caret-down" v-else></icon>
            <icon name="folder" v-if="isCollapsed"></icon>
            <icon name="folder-open" v-else></icon>
            {{ tree.name }}
        </div>
        <ol v-show="!isCollapsed">
            <li v-for="f in tree.entries">
                <file-tree v-bind:tree="f" v-if="f.entries"></file-tree>
                <router-link :class="{ 'active-file': $route.params.fileId == f.id }" :to="{ name: 'submission_file', params: { courseId: courseId, assignmentId: assignmentId, submissionId: submissionId, fileId: f.id, }, }" replace v-else>
                    <icon name="file"></icon> {{ f.name }}
                </router-link>
            </li>
        </ol>
    </div>
    
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/folder';
import 'vue-awesome/icons/folder-open';
import 'vue-awesome/icons/file';
import 'vue-awesome/icons/caret-right';
import 'vue-awesome/icons/caret-down';
import 'vue-awesome/icons/download';

export default {
    name: 'file-tree',

    props: {
        tree: {
            type: Object,
            default: null,
        },
        collapsed: {
            type: Boolean,
            default: true,
        },
    },

    data() {
        return {
            isCollapsed: this.collapsed,
            courseId: this.$route.params.courseId,
            assignmentId: this.$route.params.assignmentId,
            submissionId: this.$route.params.submissionId,
        };
    },

    methods: {
        toggle(event) {
            event.stopPropagation();
            this.isCollapsed = !this.isCollapsed;
        },
        download() {
            window.open(`/api/v1/submissions/${this.submissionId}/zip`);
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
.file-tree {
    user-select: none;
    cursor: default;
    color: #2c3e50;

    ol {
        list-style: none;
        margin: 0;
        padding: 0;
        padding-left: 1.5em;
        overflow: hidden;
    }

    .active-file {
        font-weight: bold;
    }
    .btn {
        margin-bottom: 15px;
        width:100%;
        background-color: #2c3e50;
        cursor: pointer;

    }
    .download-icon {
        color: #FFF;
    }
    .text {
        color: #FFF;
        /*margin-bottom: 200px;*/
    }
}
</style>
