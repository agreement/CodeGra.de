<template>
    <div class="file-tree" v-bind:class="{ collapsed: isCollapsed, }">
        <div v-on:click="toggle($event)">
            <span class="glyphicon" v-bind:class="{
                'glyphicon-triangle-right': isCollapsed,
                'glyphicon-triangle-bottom': !isCollapsed,
            }"></span>
            <span class="glyphicon" v-bind:class="{
                'glyphicon-folder-close': isCollapsed,
                'glyphicon-folder-open': !isCollapsed,
            }"></span>
            {{ tree.name }}
        </div>
        <ol v-show="!isCollapsed">
            <li v-for="f in tree.entries"
                v-bind:class="{ directory: f.entries, file: !f.entries }">
                <file-tree v-bind:tree="f" v-if="f.entries"></file-tree>
                <a v-bind:href="fileURL(f)" v-else>
                    <span class="glyphicon glyphicon-file"></span>
                    {{ f.name }}
                </a>
            </li>
        </ol>
    </div>
</template>

<script>
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

    .glyphicon {
        margin-right: .25em;
    }
}
</style>
