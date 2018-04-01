<template>
<div class="sidebar-register">
    <register/>
</div>
</template>

<script>
import Register from '../Register';

export default {
    name: 'sidebar-register',

    components: {
        Register,
    },

    data() {
        return {
            oldSbloc: null,
        };
    },

    async created() {
        await this.$nextTick();
        this.oldSbloc = this.$route.query.sbloc || undefined;
        if (this.oldSbloc === 'r') {
            this.oldSbloc = undefined;
        }
        this.$router.replace(this.getNewRoute('r'));
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
.sidebar-register {
    padding: 1rem;
}
</style>
