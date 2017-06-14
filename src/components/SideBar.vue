<template>
    <nav class="side-bar">
        <ul v-if="loggedIn">
            <li>
                <router-link :to="{ name: 'me', params: { userId: this.userid, }, }">
                    {{username}}
                </router-link>
            </li>
            <li>
                <router-link :to="{ name: 'assignments', }">
                    Assignments
                </router-link>
            </li>
            <li>
                <a href="#" @click="logout">
                    Logout
                </a>
            </li>
        </ul>
        <ul v-else>
            <li>
                <router-link :to="{ name: 'login', }">
                    Login
                </router-link>
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
