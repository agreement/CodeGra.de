<template>
    <b-navbar class="lti-navbar navbar" v-if="lti">
        <img class="logo" src="/static/img/codegrade.svg" v-if="hasDarkMode">
        <img class="logo" src="/static/img/codegrade-inv.svg" v-else>
    </b-navbar>
    <b-navbar toggleable type="inverse" sticky="true" class="navbar" v-else>
        <b-nav-toggle target="nav_collapse"></b-nav-toggle>

        <b-link class="navbar-brand" to="#">
            <router-link :to="{ name: 'home', }">
                <img class="logo" src="/static/img/codegrade.svg">
            </router-link>
        </b-link>

        <b-collapse is-nav id="nav_collapse">
            <div v-if="loggedIn" class="nav-container justify-content-md-between">
                <b-nav is-nav-bar>
                    <b-nav-item :to="{ name: 'me', params: { userId: userid, }, }" active-class="active">
                        {{ name }}
                    </b-nav-item>
                    <b-nav-item :to="{ name: 'assignments', }"  active-class="active">
                        Assignments
                    </b-nav-item>
                    <b-nav-item :to="{ name: 'courses', }"  active-class="active">
                        Courses
                    </b-nav-item>
                </b-nav>
                <b-nav is-nav-bar>
                    <b-nav-item :to="{ name: 'logout', }" @click.native.capture="logoutAndRedirect"  active-class="active">
                        Logout
                    </b-nav-item>
                </b-nav>
            </div>
            <div v-else class="nav-container justify-content-md-end">
                <b-nav is-nav-bar>
                    <b-nav-item :to="{ name: 'login', }"  active-class="active">
                        Login
                    </b-nav-item>
                </b-nav>
            </div>
        </b-collapse>
    </b-navbar>
</template>

<script scoped>
import { mapGetters, mapActions } from 'vuex';
import { parseBool } from '@/utils';

export default {
    name: 'nav-bar',

    computed: {
        hasDarkMode() {
            return this.$store.getters['pref/darkMode'];
        },
        lti() {
            if (this.$route.query.inLTI !== undefined) {
                window.inLTI = parseBool(this.$route.query.inLTI, false);
            }
            return window.inLTI || false;
        },
        ...mapGetters('user', {
            loggedIn: 'loggedIn',
            userid: 'id',
            name: 'name',
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

<style lang="less" scoped>
@import "~mixins.less";

.navbar-collapse .nav-container {
    display: flex;
    flex-grow: 1;
}

.lti-navbar {
    background-color: transparent;
    .logo {
        margin: 0 auto;
    }
    padding-top: 15px;
    padding-bottom: 15px;
}

@media-medium {
    .navbar-left {
        float: left;
    }

    .navbar-right {
        float: right;
    }
}

.logo {
    width: 10em;
}
</style>

<style lang="less">
@import "~mixins.less";

.navbar .navbar-nav .nav-item a {
    display: block;
    padding: 0.5em;
    margin: -.5em -.25em;
    text-decoration: none;
    text-align: right;
    color: #cbcbcb;
    border-bottom: 3px solid transparent;

    @media-small {
        padding-bottom: 0;
        margin-bottom: 0;
    }


    &:hover {
        color: white;
    }

    &.active {
        border-color: white;
        color: white;
    }

}

@media-small {
    .navbar .navbar-nav:first-child {
        margin-left: 0.25em;
    }
    .navbar .navbar-nav:last-child {
        flex: 1
    }
}
</style>
