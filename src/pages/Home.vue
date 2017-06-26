<template>
    <div class="page home">
        <b-jumbotron fluid="True" header="Code grading made intuitive" lead="The best code grader & feedback tool on the web" >
            <b-btn variant="primary" size="lg" class="btn-outline-secondary" href="#">Sign up</b-btn>
        </b-jumbotron>
        <div class="container">
            <h3>Made with ❤️ & 🍺</h3>
            <p>Getting feedback as computer science students was frustating and non-intuitive. All online feedback systems where designed for the less technically focused majors. We decided to fill the gap with our revolutionary new grading tool. This project started as a school assignment for the course "Project Software Engineering" (year 2016-2017). With our tool one can grade code line-by-line. The tool is compatible with the LTI protocol, which makes it possible to easily integrate it in learning environments such as Canvas or Blackboard.</p>
            <br>
            <div class="row text-center">
                <div class="col-sm-4">
                    <p class="text-center"><strong>Line per line feedback</strong></p><br>
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
                    <p class="text-center"><strong>File browser</strong></p><br>
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
                    <p class="text-center"><strong>Easy course management</strong></p><br>
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

    beforeCreate() {
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
    url('/static/img/screenshot4.png') no-repeat center center;
    color: white;
}

.jumbotron h1 {
    font-size: 50px;
    text-transform: uppercase;
    font-weight: 700;
    font-family: Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;
}

.rounded-circle {
    border-width: 1px;
    border-style: solid;
    border-color: @color-primary;
}
</style>
