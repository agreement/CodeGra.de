<template>
    <div id="app" class="container-fluid">
        <nav-bar class="row"></nav-bar>
        <router-view></router-view>
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
