<template>
    <div class="file-tree">
        <ol>
            <li v-for="f in entries">
                <span class="glyphicon"
                      v-bind:class="{ 'glyphicon-folder-close': isCollapsed, 'glyphicon-folder-open': !isCollapsed }"
                      v-if="f.entries"></span>
                <span class="glyphicon glyphicon-file"
                      v-else></span>

                <a href="#">{{ f.name }}</a>

                <file-tree v-bind:class="{ collapsed: isCollapsed }"
                           v-bind:collapsed="true"
                           v-bind:entries="f.entries"
                           v-if="f.entries"></file-tree>
            </li>
        </ol>
    </div>
</template>

<script>
export default {
    name: 'file-tree',

    props: ['hidden', 'collapsed', 'entries'],

    data() {
        return {
            path: this.$route.params.path,
        };
    },

    mounted() {
        if (!this.entries) {
            this.getEntries();
        }
    },

    methods: {
        getEntries() {
            this.$http.get(`/api/dir/${this.path}`).then((data) => {
                Object.assign(this, data.body);
            });
        },
    },
};
</script>

<style lang="less">
ol {
    list-style: none;
    margin: 0;
    padding: 0;

    ol {
        margin-left: 1.5em;
    }
}

li {
    .glyphicon {
        margin-right: .25em;
    }
}
</style>
