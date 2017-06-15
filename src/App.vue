<template>
    <div id="app" class="container-fluid">
        <main class="row">
            <nav-bar class="col-lg-12"></nav-bar>
            <router-view class="col-lg-12"></router-view>
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
