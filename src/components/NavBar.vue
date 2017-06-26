<template>
    <div class="lti-navbar navbar" v-if="lti">
        <img class="logo" src="/static/img/codegrade-inv.svg">
    </div>
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

    data() {
        return {
            lti: this.$route.query.lti || window.inLTI,
        };
    },

    mounted() {
        window.inLTI = this.lti;
    },

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

<style lang="less" scoped>
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
    border-bottom: #eceeef solid 1px;
    margin-bottom: 1em;
}

@media (min-width: 768px) {
    .navbar-left {
        float: left;
    }

    .navbar-right {
        float: right;
    }
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
