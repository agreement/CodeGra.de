<template>
    <div class="file-tree" v-bind:class="{ collapsed: isCollapsed, }">
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
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less">
.file-tree {
    user-select: none;
    cursor: default;

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
}
</style>
