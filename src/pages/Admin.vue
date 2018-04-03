<template>
<div class="page admin">
    <local-header title="Admin"/>
    <loader v-if="loading"/>
    <div class="row" v-else-if="manage">
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
import { LocalHeader, PermissionsManager, Loader } from '@/components';

import { setPageTitle } from './title';

export default {
    name: 'user-page',

    components: {
        PermissionsManager,
        Loader,
        LocalHeader,
    },

    data() {
        return {
            manage: false,
            loading: true,
        };
    },

    mounted() {
        setPageTitle('Admin page');
        // Do not forget to add new permissions to constants file
        this.$hasPermission('can_manage_site_users').then((manage) => {
            this.manage = manage;
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

    @media @media-no-medium {
        .card {
            margin-top: 15px;
        }
    }
}

.card {
    margin-bottom: 15px;
}

.permissions-manager {
    margin: -1.25rem;
}
</style>
