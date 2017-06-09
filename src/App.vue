<template>
    <div id="app">
        <header-bar></header-bar>
        <side-bar></side-bar>
        <router-view></router-view>
    </div>
</template>

<script>
import { HeaderBar, SideBar } from '@/components';

export default {
    name: 'app',

    components: {
        HeaderBar,
        SideBar,
    },
};
</script>

<style>
#app {
        font-family: 'Avenir', Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        box-sizing: border-box;
}

* {
        box-sizing: inherit;
}
</style>
