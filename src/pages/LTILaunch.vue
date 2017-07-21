<template>
    <b-alert variant="danger" show v-if="error" class="box">
        <p style="text-align: center; font-size: 1.3em;">
            Something went wrong during the LTI launch!
            <br>
            Please try again.
        </p>
    </b-alert>
    <loader v-else/>
</template>

<script>
import { Loader } from '@/components';

import * as types from '../store/mutation-types';
import { setTitle } from './title';

export default {
    name: 'lti-launch-page',

    data() {
        return {
            error: false,
        };
    },

    mounted() {
        this.$set(window, 'inLTI', true);

        setTitle('LTI is launching, please wait');

        this.$http.get('/api/v1/lti/launch/2', {
            headers: {
                Jwt: this.$route.query.jwt,
            },
        }).then(({ data }) => {
            if (data.access_token) {
                this.$store.commit(`user/${types.UPDATE_ACCESS_TOKEN}`, data);
            }
            this.$router.replace({
                name: 'assignment_submissions',
                params: {
                    courseId: data.assignment.course.id,
                    assignmentId: data.assignment.id,
                },
            });
        }).catch(() => {
            this.error = true;
        });
    },

    components: {
        Loader,
    },
};
</script>

<style>
.box {
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
