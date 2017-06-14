<template>
    <nav class="side-bar">
        <ul v-if="loggedIn">
            <li>
                <a v-bind:href="userBaseURL">{{ username }}</a>
            </li>
            <li>
                <a v-bind:href="userAssignmentsURL">Assignments</a>
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

        userAssignmentsURL() {
            return '#/assignments';
        },

        ...mapGetters('user', {
            loggedIn: 'loggedIn',
            userid: 'id',
            username: 'name',
        }),
    },

    methods: {
        ...mapActions('user', [
            'logout',
        ]),
    },
};
</script>
