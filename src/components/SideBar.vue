<template>
    <nav class="side-bar">
        <ul v-if="loggedIn">
            <li><a v-bind:href="userBaseURL">{{ username }}</a></li>
            <li><a v-bind:href="userOpenURL">Open assignments</a></li>
            <li><a v-bind:href="userGradedURL">Graded assignments</a></li>
            <li><a href="#/settings">Settings</a></li>
            <li><a href="#/logout">Logout</a></li>
        </ul>
        <ul v-else>
            <li><a href="#/login">login</a></li>
        </ul>
    </nav>
</template>

<script>
export default {
    name: 'side-bar',

    data() {
        return {
            loggedIn: 1,
            userid: 0,
            username: 'Henk',
        };
    },

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
    },
};
</script>

<style lang="less">
</style>
