<template>
    <div class="container">
        <b-navbar toggleable type="inverse" sticky="true" class="navbar">

            <b-nav-toggle target="nav_collapse"></b-nav-toggle>

            <b-link class="navbar-brand" to="#">
                <router-link :to="{ name: 'home', }">
                    <img class="logo" src="/static/img/codegrade.svg">
                </router-link>
            </b-link>

            <b-collapse is-nav id="nav_collapse">

                <div v-if="loggedIn" class="loggedin-nav">
                    <b-nav is-nav-bar class="navbar-left">
                        <router-link class="nav-item" tag="li" :to="{ name: 'me', params: { userId: this.userid, }, }" active-class="active">
                            {{username}}
                        </router-link>
                        <router-link class="nav-item" tag="li" :to="{ name: 'assignments', }"  active-class="active">
                            Assignments
                        </router-link>
                    </b-nav>
                    <b-nav is-nav-bar class="navbar-right">
                        <router-link class="nav-item" tag="li" :to="{ name: 'logout', }" @click.native.capture="logout"  active-class="active">
                            Logout
                        </router-link>
                    </b-nav>
                </div>
                <b-nav is-nav-bar class="navbar-right" v-else>
                    <router-link class="nav-item" tag="li" :to="{ name: 'login', }"  active-class="active">
                        Login
                    </router-link>
                </b-nav>

            </b-collapse>
        </b-navbar>
    </div>
</template>

<script scoped>
import { mapGetters, mapActions } from 'vuex';

export default {
    name: 'nav-bar',

    computed: {
        ...mapGetters('user', {
            loggedIn: 'loggedIn',
            userid: 'id',
            username: 'name',
        }),
    },

    methods: {
        logoutAndRedirect() {
            this.logout().then(() => {
                this.$router.push({
                    name: this.loggedIn ? 'assignments' : 'login',
                });
            });
        },

        ...mapActions('user', [
            'logout',
        ]),
    },
};
</script>

<style lang="scss">

.navbar {
    background-color: #2c3e50;
    margin-bottom: 2em;
}

.loggedin-nav {
    width: 100%;
}

@media (min-width: 768px) {
    .navbar-left {
        float: left;
    }

    .navbar-right {
        float: right;
    }
}

.navbar-collapse li {
    text-align: right;
    color: #FFF;
}

.active {
    border-bottom: 3px solid white;
}

.nav-item {
    padding: 0.5em;
}

.nav-item:hover {
    cursor: pointer;
    color: #cbcbcb;
}

.logo {
    width: 10em;
}

</style>
