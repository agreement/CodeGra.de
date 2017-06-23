<template>
    <b-navbar toggleable type="inverse" sticky="true">
        <b-nav-toggle target="nav_collapse"></b-nav-toggle>

        <b-link class="navbar-brand" to="#">
            <router-link :to="{ name: 'home', }">
                <img class="logo" src="/static/img/codegrade.svg">
            </router-link>
        </b-link>

        <b-collapse is-nav id="nav_collapse">
            <div v-if="loggedIn" class="nav-container justify-content-md-between">
                <b-nav is-nav-bar>
                    <b-nav-item>
                        <router-link :to="{ name: 'me', params: { userId: this.userid, }, }" active-class="active">
                            {{username}}
                        </router-link>
                    </b-nav-item>
                    <b-nav-item>
                        <router-link :to="{ name: 'assignments', }"  active-class="active">
                            Assignments
                        </router-link>
                    </b-nav-item>
                    <b-nav-item>
                        <router-link :to="{ name: 'courses', }"  active-class="active">
                            Courses
                        </router-link>
                    </b-nav-item>
                </b-nav>
                <b-nav is-nav-bar>
                    <b-nav-item>
                        <router-link :to="{ name: 'logout', }" @click.native.capture="logoutAndRedirect"  active-class="active">
                            Logout
                        </router-link>
                    </b-nav-item>
                </b-nav>
            </div>
            <div v-else class="nav-container justify-content-md-end">
                <b-nav is-nav-bar>
                    <b-nav-item>
                        <router-link :to="{ name: 'login', }"  active-class="active">
                            Login
                        </router-link>
                    </b-nav-item>
                </b-nav>
            </div>
        </b-collapse>
    </b-navbar>
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
.navbar-collapse .nav-container {
    display: flex;
    flex-grow: 1;
}

.navbar {
    margin-bottom: 2em;

}

.nav-item a {
    display: block;
    padding: 0.5em;
    margin: -.5em -.25em;
    text-decoration: none;
    text-align: right;
    color: white;

    &:hover {
        color: #cbcbcb;
    }

    &.active {
        border-bottom: 3px solid white;
    }
}

.logo {
    width: 10em;
}
</style>
