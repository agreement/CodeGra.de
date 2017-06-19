<template>
    <div class="page home">
        <!-- <login v-if="!loggedIn"></login> -->
        <b-jumbotron fluid="True" header="Code Grade" lead="The best code grader & feedback tool on the web" >
            <b-btn variant="primary" size="lg" class="btn-outline-secondary" href="#">Sign up</b-btn>
        </b-jumbotron>
        <div class="container">
            <h3>THE COMPANY</h3>
            <p><em>Grading!</em></p>
            <p>We have created a fictional band website. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
            <br>
            <div class="row text-center">
                <div class="col-sm-4">
                    <p class="text-center"><strong>Flexibility</strong></p><br>
                    <a href="#demo" data-toggle="collapse">
                    <img src="/static/img/screenshot.png" class="rounded-circle" alt="Random Name" width="255" height="255">
                    </a>
                    <div id="demo" class="collapse">
                        <p>Guitarist and Lead Vocalist</p>
                        <p>Loves long walks on the beach</p>
                        <p>Member since 1988</p>
                    </div>
                </div>
                <div class="col-sm-4">
                    <p class="text-center"><strong>Synergy</strong></p><br>
                    <a href="#demo2" data-toggle="collapse">
                    <img src="/static/img/screenshot.png" class="rounded-circle" alt="Random Name" width="255" height="255">
                    </a>
                    <div id="demo2" class="collapse">
                        <p>Drummer</p>
                        <p>Loves drummin'</p>
                        <p>Member since 1988</p>
                    </div>
                </div>
                <div class="col-sm-4">
                    <p class="text-center"><strong>Responsive</strong></p><br>
                    <a href="#demo3" data-toggle="collapse">
                    <img src="/static/img/screenshot.png" class="rounded-circle" alt="Random Name" width="255" height="255">
                    </a>
                    <div id="demo3" class="collapse">
                        <p>Bass player</p>
                        <p>Loves math</p>
                        <p>Member since 2005</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
    name: 'home-page',

    computed: {
        ...mapGetters('user', [
            'loggedIn',
        ]),
    },

    mounted() {
        if (this.loggedIn) {
            this.$router.push({
                name: 'assignments',
            });
        }
    },
};
</script>

<style>
.jumbotron {
    /* top, transparent, gradient */
    background: linear-gradient(
        rgba(0, 0, 0, 0.6),
        rgba(0, 0, 0, 0.6)
    ),
    /* bottom, image */
    url('/static/img/screenshot.png') no-repeat center center;
    color: white;
}

.jumbotron h1 {
    font-size: 100px;
    text-transform: uppercase;
    font-weight: 700;
    font-family: Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;
}
</style>
