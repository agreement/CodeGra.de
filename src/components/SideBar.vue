<template>
    <nav class="side-bar">
        <ul v-if="loggedIn">
            <li>
                <a v-bind:href="userBaseURL">{{ username }}</a>
            </li>
            <li>
                <a v-bind:href="userOpenURL">Open assignments</a>
            </li>
            <li>
                <a v-bind:href="userGradedURL">Graded assignments</a>
            </li>
            <li>
                <a href="#/settings">Settings</a>
            </li>
            <li>
                <a href="#/login" @click="logout()">Logout</a>
            </li>
        </ul>
        <ul v-else>
            <li>
                <a href="#/login">login</a>
            </li>
        </ul>
    </nav>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
    name: 'side-bar',

    computed: {
        userBaseURL() {
            return `#/users/${this.userid}`;
        },

        userOpenURL() {
            return `${this.userBaseURL}/assignments?graded=0`;
        },

        userGradedURL() {
            return `${this.userBaseURL}/assignments?graded=1`;
        },

        ...mapGetters('user', {
            loggedIn: 'loggedIn',
            userid: 'id',
            username: 'name',
        }),
    },

    methods: {
        ...mapActions('user', {
            logout: 'logout',
        }),
    },
};
</script>
