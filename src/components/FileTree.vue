<template>
    <div class="file-tree" v-bind:class="{ collapsed: isCollapsed, }">
        <div v-on:click="toggle($event)">
            <icon name="caret-right" v-if="isCollapsed"/>
            <icon name="caret-down" v-else/>
            <icon name="folder" v-if="isCollapsed"/>
            <icon name="folder-open" v-else/>
            {{ tree.name }}
        </div>
        <ol v-show="!isCollapsed">
            <li v-for="f in tree.entries">
                <file-tree :tree="f"
                           :collapsed="!fileInTree($route.params.fileId, f)"
                           v-if="f.entries"/>
                <router-link :class="{ 'active-file': $route.params.fileId == f.id }"
                             :to="getFileRoute(f.id)"
                             replace
                             v-else>
                    <icon name="file"/>
                    {{ f.name }}
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

        getFileRoute(fileId) {
            return {
                name: 'submission_file',
                params: {
                    courseId: this.courseId,
                    assignmentId: this.assignmentId,
                    submissionId: this.submissionId,
                    fileId,
                },
            };
        },

        fileInTree(fileId, tree) {
            for (let i = 0; i < tree.entries.length; i += 1) {
                if (tree.entries[i].entries) {
                    if (this.fileInTree(fileId, tree.entries[i])) {
                        return true;
                    }
                } else if (Number(tree.entries[i].id) === Number(fileId)) {
                    return true;
                }
            }
            return false;
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
}
</style>
