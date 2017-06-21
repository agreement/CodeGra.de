<template>
    <div id="app">
        <nav-bar></nav-bar>
        <main class="container-fluid">
            <div class="row justify-content-center">
                <router-view class="col-10"></router-view>
            </div>
        </main>
        <footer-bar></footer-bar>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { FooterBar, NavBar } from '@/components';

export default {
    name: 'app',

    components: {
        FooterBar,
        NavBar,
    },

    computed: {
        ...mapGetters('user', {
            loggedIn: 'loggedIn',
        }),
    },

};
</script>

<style lang="less" scoped>
main {
    display: flex;
    flex-direction: row;
    flex-grow: 1;
    flex-shrink: 1;
    width: 100%;

    > .row {
        flex-grow: 1;
        flex-shrink: 1;
    }
}
</style>
