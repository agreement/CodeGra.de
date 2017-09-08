<template>
    <div id="newCourse">
        <loader class="text-center" v-if="loading"></loader>

        <div v-else @keyup.enter="submit">
            <b-form-fieldset>
                <b-input-group left="Course Name">
                    <b-form-input  type="text" v-model="name"></b-form-input>
                </b-input-group>
                <b-alert variant="danger" :show="true" v-if="error.length != 0">
                    {{ error }}
                </b-alert>
            </b-form-fieldset>

            <b-button-toolbar justify>
                <b-button variant="danger" @click="reset()">Cancel</b-button>
                <b-button :variant="error.length != 0 ? 'danger' : done ? 'success' : 'primary'" @click="submit()">
                    <icon name="refresh" spin v-if="submitted"></icon>
                    <span v-else>Submit</span>
                </b-button>
            </b-button-toolbar>
        </div>
    </div>
</template>

<script>
import Loader from './Loader';

export default {
    name: 'new-course',
    data() {
        return {
            name: '',
            done: false,
            error: '',
            loading: false,
        };
    },
    components: {
        Loader,
    },

    methods: {
        reset() {
            this.done = false;
            this.name = '';
            this.error = '';
        },
        submit() {
            if (this.name === '') {
                this.error = 'Please select a course name';
                return;
            }
            this.loading = true;
            this.$http.post('/api/v1/courses/', { name: this.name }).then(({ data }) => {
                this.loading = false;
                this.assignments = data;
                window.location.href = `/courses/${data.id}?created=true`;
            }).catch(
                () => {
                    this.error = 'An error occurred adding the course, try again please!';
                    this.loading = false;
                    this.done = false;
                },
            );
            this.loading = false;
        },
    },
};
</script>
