<template>
    <div id="app" class="container-fluid">
        <header-bar class="navbar"></header-bar>
        <main class="row">
            <side-bar class="col-lg-2"></side-bar>
            <router-view class="col-lg-10"></router-view>
        </main>
        <footer-bar></footer-bar>
    </div>
</template>

<script>
import { FooterBar, HeaderBar, SideBar } from '@/components';

export default {
    name: 'app',

    components: {
        FooterBar,
        HeaderBar,
        SideBar,
    },
};
</script>
