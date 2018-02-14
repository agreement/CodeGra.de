<template>
    <loader v-if="loading"/>
    <div v-else class="page user">
        <div class="row">
            <div :class="snippets ? 'col-md-6' : 'col-12'">
                <b-card header="User info">
                    <user-info></user-info>
                </b-card>
            </div>
            <div :class="snippets ? 'col-md-6' : 'col-12'">
                <b-card header="Snippets" v-if="snippets">
                    <snippet-manager></snippet-manager>
                </b-card>
                <b-card header="Preferences">
                    <preference-manager :show-language="false"
                                        :show-whitespace="false"
                                        :show-revision="false"/>
                </b-card>
            </div>
        </div>

        <div class="row" v-if="manage">
            <div class="col-12">
                <b-card header="Manage site permissions">
                    <permissions-manager :showAddRole="false"
                                         fixedPermission="can_manage_site_users"
                                         :showDeleteRole="false"
                                         :getChangePermUrl="(_, roleId) => `/api/v1/roles/${roleId}`"
                                         :getRetrieveUrl="() => '/api/v1/roles/'"/>
                </b-card>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { UserInfo, SnippetManager, PermissionsManager, Loader, PreferenceManager } from '@/components';

import { setPageTitle } from './title';

export default {
    name: 'user-page',

    components: {
        UserInfo,
        SnippetManager,
        PermissionsManager,
        Loader,
        PreferenceManager,
    },

    data() {
        return {
            manage: false,
            loading: true,
            snippets: false,
        };
    },

    mounted() {
        setPageTitle('User info');
        this.$hasPermission([
            'can_manage_site_users',
            'can_use_snippets',
        ]).then(([manage, snippets]) => {
            this.manage = manage;
            this.snippets = snippets;
            this.loading = false;
        });
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

.row > div:not(.col-12) .card:not(:first-child) {
    margin-top: 15px;

    @media-no-medium {
        .card {
            margin-top: 15px;
        }
    }
}

.card {
    margin-bottom: 15px;
}
</style>
