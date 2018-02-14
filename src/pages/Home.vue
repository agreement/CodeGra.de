<template>
    <div class="page home col-12">
        <b-jumbotron fluid
                     header="Code grading made intuitive"
                     lead="The best code grader &amp; feedback tool on the web">
            <b-btn variant="primary"
                   size="lg"
                   v-if="!loggedIn && UserConfig.features.register"
                   @click="$router.push('register')">
                Sign up
            </b-btn>
        </b-jumbotron>
        <div class="row justify-content-center content-container">
            <div class="content col-10">
                <h3>Made with ❤️ &amp; 🍺</h3>
                <p>
                    Getting feedback as computer science students was frustating
                    and non-intuitive. All online feedback systems where
                    designed for the less technically focused majors. We decided
                    to fill the gap with our revolutionary new grading tool.
                    This project started as a school assignment for the course
                    "Project Software Engineering" (year 2016-2017). With our
                    tool one can grade code line-by-line. The tool is compatible
                    with the LTI protocol, which makes it possible to easily
                    integrate it in LMS of choice such as Canvas or
                    Blackboard.
                </p>
                <div class="row text-center">
                    <div class="col-sm-4">
                        <p>
                            <strong>Line per line feedback</strong>
                        </p>
                        <div class="rounded-circle feature-img">
                            <img src="/static/img/feature-1.png">
                        </div>
                    </div>
                    <div class="col-sm-4">
                        <p>
                            <strong>Easy course management</strong>
                        </p>
                        <div class="rounded-circle feature-img">
                            <img src="/static/img/feature-2.png">
                        </div>
                    </div>
                    <div class="col-sm-4">
                        <p>
                            <strong>File browser</strong>
                        </p>
                        <div class="rounded-circle feature-img">
                            <img src="/static/img/feature-3.png">
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapGetters } from 'vuex';

import { setPageTitle } from './title';

export default {
    name: 'home-page',

    data() {
        return {
            UserConfig,
        };
    },

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

    mounted() {
        setPageTitle('Home');
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.jumbotron {
    color: white;

    .default-background;
    background-image: url('/static/img/screenshot.png');

    h1 {
        font-size: 50px;
        text-transform: uppercase;
        font-weight: 700;
        font-family: Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;
    }

    position: fixed;
    left: 0;
    width: 100%;
    height: 50vh;
}

.feature-img {
    display: inline-block;
    @size: 255px;
    max-width: @size;
    max-height: @size;
    height: auto;
    width: auto;
    overflow: hidden;
    border: 1px solid #2c3e50;

    img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
}

.content-container {
    .default-background;
    margin-top: 50vh;
    width: 100%;
    padding: 30px;
    z-index: 1;
    margin-left: 0;
    margin-right: 0;
    position: relative;
}

.page {
    margin-top: -2em;
    padding: 0;
}
</style>
