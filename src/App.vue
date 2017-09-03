<template>
    <div id="app">
        <nav-bar></nav-bar>
        <div v-if="loading"></div>
        <main class="container-fluid" v-else>
            <div class="row justify-content-center">
                <router-view class="col-md-10"></router-view>
            </div>
        </main>
        <footer-bar></footer-bar>
    </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { FooterBar, NavBar } from '@/components';
import Loader from './components/Loader';

export default {
    name: 'app',

    components: {
        FooterBar,
        NavBar,
        Loader,
    },

    data() {
        return {
            loading: true,
        };
    },

    computed: {
        ...mapGetters('user', {
            loggedIn: 'loggedIn',
        }),
        ...mapGetters('features', {
            features: 'features',
        }),
    },

    mounted() {
        if ((!this.features) || Object.keys(this.features).length === 0 || Math.random() < 0.01) {
            this.refreshFeatures().then(() => { this.loading = false; });
        } else {
            this.loading = false;
        }
    },
    methods: {
        ...mapActions({
            refreshFeatures: 'features/refreshFeatures',
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
