<template>
<div class="sidebar-user-info">
    <b-card header="Preferences">
        <preference-manager :show-language="false"
                            :show-whitespace="false"
                            :show-revision="false"/>
    </b-card>

    <b-card header="User info">
        <user-info/>
    </b-card>

    <b-card header="Snippets" v-if="snippets">
        <snippet-manager/>
    </b-card>
</div>
</template>

<script>
import { mapGetters } from 'vuex';

import UserInfo from '../UserInfo';
import SnippetManager from '../SnippetManager';
import PreferenceManager from '../PreferenceManager';

import { waitAtLeast } from '../../utils';

export default {
    name: 'sidebar-user-info',

    components: {
        UserInfo,
        SnippetManager,
        PreferenceManager,
    },

    data() {
        return {
            snippets: false,
            oldSbloc: null,
        };
    },

    mounted() {
        this.$emit('loading');
        const done = this.$hasPermission(
            'can_use_snippets',
        ).then((snippets) => {
            this.snippets = snippets;
        });

        // Most components should be loaded by now.
        waitAtLeast(250, done).then(() => {
            this.$emit('loaded');
        });
    },

    async created() {
        await this.$nextTick();
        this.oldSbloc = this.$route.query.sbloc || undefined;
        if (this.oldSbloc === 'm') {
            this.oldSbloc = undefined;
        }
        this.$router.replace(this.getNewRoute('m'));
    },

    destroyed() {
        this.$router.replace(this.getNewRoute(this.oldSbloc));
    },

    methods: {
        getNewRoute(sbloc) {
            return Object.assign({}, this.$route, {
                query: Object.assign({}, this.$route.query, {
                    sbloc,
                }),
            });
        },
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";
.card {
    margin-bottom: 15px;

    &:last-child {
        margin-bottom: 0;
    }
}

.sidebar-user-info {
    overflow-y: auto;
    padding: 1rem;
}
</style>
