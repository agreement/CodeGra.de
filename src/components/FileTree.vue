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
            {{ dirName }}
        </div>
        <ol v-show="!isCollapsed">
            <li v-for="f in dirEntries"
                v-bind:class="{ directory: f.entries, file: !f.entries }">
                <file-tree :collapsed="true" v-bind:name="f.name"
                    v-bind:entries="f.entries" v-if="f.entries"></file-tree>
                <a href="#" v-else>
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

    props: ['name', 'entries', 'collapsed'],

    data() {
        return {
            path: this.$route.params.path,
            isCollapsed: this.collapsed,
            dirEntries: this.entries,
            dirName: this.name,
        };
    },

    mounted() {
        if (!this.dirEntries) {
            this.getEntries();
        }
    },

    methods: {
        getEntries() {
            this.$http.get(`/api/dir/${this.path}`).then((data) => {
                console.log(data.body);
                this.dirName = data.body.name;
                this.dirEntries = data.body.entries;
            });
        },

        toggle(event) {
            event.stopPropagation();
            this.isCollapsed = !this.isCollapsed;
        },
    },
};
</script>

<style lang="less">
.file-tree {
    user-select: none;

    .glyphicon {
        margin-right: .25em;
    }

    * {
        cursor: default;
    }
}

ol {
    list-style: none;
    margin: 0;
    padding: 0;
    padding-left: 1.5em;
    overflow: hidden;
}
</style>
