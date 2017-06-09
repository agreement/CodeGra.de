<template>
    <div class="page home">
        <login v-if="!loggedIn"></login>
    </div>
</template>

<script>
import { Login } from '@/components';

export default {
    name: 'home-page',

    data() {
        return {
            loggedIn: 1,
            userid: 0,
            username: 'Henk',
        };
    },

    components: {
        Login,
    },
};
</script>

<style lang="less">
</style>
