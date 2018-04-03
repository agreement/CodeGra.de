<template>
<div class="home">
    <b-jumbotron fluid
                    lead="Code grading made intuitive"
                    class="row">
        <div slot="header">
            <img src="/static/img/codegrade.svg"/>
        </div>
    </b-jumbotron>

    <div class="row justify-content-center content-container">
        <div class="container">
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
        setPageTitle();
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

@thumb-size: 255px;

.home {
    position: relative;
    margin-top: 0 !important;
}

.jumbotron {
    position: sticky;
    top: 0;
    margin-bottom: 0;
    color: white;
    padding: 1.5rem 1rem;
    align-items: center;

    background-image: url('/static/img/screenshot.png');

    @media @media-no-small {
	height: 50vh;
    }

    p {
        margin-bottom: 0;
        font-size: 2.5em;

        @media @media-small {
            font-size: 1.5em;
        }
    }
}

.content-container {
    .default-background;
    margin: 0 4rem;
    padding-top: 1.5rem;
    position: relative;

    @media @media-small {
        margin: 0 -15px;
    }
}

.feature-img {
    display: inline-block;
    max-width: @thumb-size;
    max-height: @thumb-size;
    overflow: hidden;
    border: 1px solid #2c3e50;

    img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
}
</style>
