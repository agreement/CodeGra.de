<template>
    <div class="file-tree" :class="{ collapsed: isCollapsed, }">
        <div class="directory" :class="{ faded: depth > 0 && !dirHasRevision(tree) }" @click="toggle($event)">
            <span class="label">
                <icon name="caret-right" class="caret-icon" v-if="isCollapsed"/>
                <icon name="caret-down" class="caret-icon" v-else/>
                <icon name="folder" class="dir-icon" v-if="isCollapsed"/>
                <icon name="folder-open" class="dir-icon" v-else/>
                {{ tree.name }}
                <span v-if="depth > 0 && dirHasRevision(tree)"
                      v-b-popover.hover.top="'This directory has a file with a teacher\'s revision'"
                      class="rev-popover">
                    *
                </span>
            </span>
        </div>
        <ol v-show="!isCollapsed">
            <li v-for="f in tree.entries"
                class="file"
                :class="{ faded: diffMode && !fileHasRevision(f), active: fileIsSelected(f) }">
                <file-tree :tree="f"
                           :collapsed="!fileInTree($route.params.fileId, f)"
                           :depth="depth + 1"
                           v-if="f.entries"/>
                <router-link :to="getFileRoute(f)"
                             class="label"
                             v-else>
                    <icon name="file" class="file-icon"/>{{ f.name }}
                </router-link>
                <span v-if="fileHasRevision(f)"
                      v-b-popover.hover.top="'This file has a teacher\'s revision'"
                      class="rev-popover">
                    *
                </span>
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
        depth: {
            type: Number,
            default: 0,
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

    computed: {
        diffMode() {
            return this.$route.query.revision === 'diff';
        },
    },

    methods: {
        toggle(event) {
            event.stopPropagation();
            this.isCollapsed = !this.isCollapsed;
        },

        getFileRoute(file) {
            const fileId = file.id || file.ids[0] || file.ids[1];
            return {
                name: 'submission_file',
                params: {
                    courseId: this.courseId,
                    assignmentId: this.assignmentId,
                    submissionId: this.submissionId,
                    fileId,
                },
                query: this.$route.query,
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

        fileIsSelected(f) {
            const selectedId = this.$route.params.fileId;
            const fileId = f.id || (f.ids && (f.ids[0] || f.ids[1]));
            return Number(selectedId) === Number(fileId);
        },

        hasRevision(f) {
            if (f.entries) {
                return this.dirHasRevision(f);
            }
            return this.fileHasRevision(f);
        },

        fileHasRevision(f) {
            return f.revision !== undefined ||
                (f.ids && f.ids[0] !== f.ids[1]);
        },

        dirHasRevision(d) {
            for (let i = 0; i < d.entries.length; i += 1) {
                if (this.hasRevision(d.entries[i])) {
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
@import "~mixins.less";

.file-tree a,
.file-tree {
    user-select: none;
    cursor: default;
    color: @color-primary;

    #app.dark & {
        color: @text-color-dark;
    }

    a:hover {
        cursor: pointer;
        text-decoration: underline;
    }

    .active-file {
    }

    .directory .label:hover {
        cursor: pointer;
    }

    ol {
        list-style: none;
        margin: 0;
        padding: 0;
        padding-left: 1.5em;
        overflow: hidden;
    }

    .file, .directory {
        &.faded > .label {
            opacity: .6;
        }

        &.active > .label {
            opacity: 1;
            font-weight: bold;
        }
    }

    .caret-icon {
        width: 1em;
    }

    .dir-icon {
        width: 1.5em;
    }

    .file-icon {
        width: 1em;
        margin-right: .5em;
    }

    .rev-popover {
        display: inline;
        cursor: pointer;
    }
}
</style>
