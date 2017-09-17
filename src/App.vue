<template>
    <div id="app" :class="hasDarkMode ? 'dark' : ''">
        <nav-bar/>
        <main class="container-fluid justify-content-center">
            <div class="row justify-content-center">
                <router-view class="page router col-lg-10"/>
            </div>
        </main>
        <footer-bar/>
    </div>
</template>

<script>
import { FooterBar, NavBar } from '@/components';

export default {
    name: 'app',

    components: {
        FooterBar,
        NavBar,
    },

    computed: {
        hasDarkMode() {
            return this.$store.getters['pref/darkMode'];
        },
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
    min-height: 0;

    > .row {
        flex-grow: 1;
        flex-shrink: 1;
        max-width: 100%;
    }
}
</style>

<style lang="less">
@color-primary: #fffff;
</style>
