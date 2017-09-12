<template>
    <loader v-if="loading"/>
    <div v-else class="page user">
        <div class="row">
            <div :class="snippets ? 'col-6' : 'col-12'">
                <b-card header="User info">
                    <user-info></user-info>
                </b-card>
            </div>
            <div class="col-6" v-if="snippets">
                <b-card header="Snippets" style="margin-bottom: 15px;">
                    <snippet-manager></snippet-manager>
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
import { mapGetters, mapActions } from 'vuex';
import { UserInfo, SnippetManager, PermissionsManager, Loader } from '@/components';

import { setPageTitle } from './title';

export default {
    name: 'user-page',

    components: {
        UserInfo,
        SnippetManager,
        PermissionsManager,
        Loader,
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
        Promise.all([
            this.hasPermission({ name: 'can_manage_site_users' }),
            this.hasPermission({ name: 'can_use_snippets' }),
        ]).then(([manage, snippets]) => {
            this.manage = manage;
            this.snippets = snippets;
            this.loading = false;
        });
    },

    methods: {
        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },
};
</script>

<style lang="less" scoped>
.row:not(:last-child) {
    margin-bottom: 15px;
}
</style>
