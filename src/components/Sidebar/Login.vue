<template>
<div class="sidebar-login">
    <login @login="$emit('close-menu')"/>
</div>
</template>

<script>
import Login from '../Login';

export default {
    name: 'sidebar-login',

    components: {
        Login,
    },

    data() {
        return {
            oldSbloc: null,
        };
    },

    async created() {
        await this.$nextTick();
        this.oldSbloc = this.$route.query.sbloc || undefined;
        if (this.oldSbloc === 'l') {
            this.oldSbloc = undefined;
        }
        this.$router.replace(this.getNewRoute('l'));
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
};
</script>

<style lang="less" scoped>
.sidebar-login {
    padding: 1rem;
}
</style>
