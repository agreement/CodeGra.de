<template>
    <nav class="side-bar">
        <ul v-if="loggedIn">
            <li>
                <router-link :to="`/users/${this.userid}`">{{username}}</router-link>
            </li>
            <li>
                <router-link to="/assignments">Assignments</router-link>
            </li>
            <li>
                <router-link to="/login" @click="logout">Logout</router-link>
            </li>
        </ul>
        <ul v-else>
            <li>
                <router-link to="/login">Login</router-link>
            </li>
        </ul>
    </nav>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
    name: 'side-bar',

    computed: {
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
