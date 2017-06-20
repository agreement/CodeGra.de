<template>
    <div id="app">
        <nav-bar></nav-bar>
        <router-view class="container-fluid"></router-view>
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
