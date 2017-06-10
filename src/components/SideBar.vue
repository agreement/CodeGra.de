<template>
    <nav class="side-bar">
        <ul v-if="user.loggedIn">
            <li><a v-bind:href="userBaseURL">{{ user.name }}</a></li>
            <li><a v-bind:href="userOpenURL">Open assignments</a></li>
            <li><a v-bind:href="userGradedURL">Graded assignments</a></li>
            <li><a href="#/settings">Settings</a></li>
            <li><a href="#/login" @click="logout()">Logout</a></li>
        </ul>
        <ul v-else>
            <li>
                <a href="#/login">login</a>
            </li>
        </ul>
    </nav>
</template>

<script>
export default {
    name: 'side-bar',

    computed: {
        userBaseURL() {
            return `#/users/${this.user.id}`;
        },

        userOpenURL() {
            return `${this.userBaseURL}/assignments?graded=0`;
        },

        userGradedURL() {
            return `${this.userBaseURL}/assignments?graded=1`;
        },
    },

    methods: {
        logout() {
            this.user.loggedIn = false;

            this.user.id = 0;
            this.user.email = '';
            this.user.name = '';
        },
    },

    store: {
        user: 'user',
    },
};
</script>
