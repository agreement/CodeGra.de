<template>
    <div id="newCourse">
        <div class="justify-content-md-center">
            <loader class="text-center" v-if="loading"></loader>
            <div v-if="done && error == ''">
                <b-alert variant="success" show>
                    <center><span>Succesfully created course!</span></center>
                </b-alert>
            </div>

            <div v-else v-on:keyup.enter="submit()">
                <div class="form-group">
                    <b-input-group left="Course Name">
                        <b-form-input  type="text" v-model="name"></b-form-input>
                    </b-input-group>
                    <div v-show="done && error.length !== 0" class="help alert-danger">
                        {{ error }}
                    </div>
                </div>

                <div class="btn-group btn-group-justified pull-right">
                    <div class="btn-group">
                        <button type="cancel" class="btn btn-primary" @click="reset()">Cancel</button>
                    </div>
                    <div class="btn-group">
                        <button type="submit" class="btn btn-primary" @click="submit()">Submit</button>
                    </div>
                </div>
            </div>
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
            this.loading = true;
            this.done = true;
            this.$http.post('/api/v1/courses/', { name: this.name }).catch(
                () => {
                    this.error = 'An error occurred adding the course, try again please!';
                    this.loading = false;
                },
            );
            this.loading = false;
        },
    },
};
</script>
