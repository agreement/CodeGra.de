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
                <a v-bind:href="fileURL(f)" v-else>
                    <icon name="file"></icon> {{ f.name }}
                </a>
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
        };
    },

    methods: {
        toggle(event) {
            event.stopPropagation();
            this.isCollapsed = !this.isCollapsed;
        },

        fileURL(file) {
            const path = this.$route.path.replace(/\/files\/\d+/, '');
            return `#${path}/files/${file.id}`;
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
}
</style>
