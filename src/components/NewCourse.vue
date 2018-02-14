<template>
    <div id="newCourse">
        <div @keyup.ctrl.enter="submit">
            <b-form-fieldset class="add-course">
                <b-input-group>
                    <input type="text"
                           class="form-control"
                           placeholder="New course name"
                           v-model="name"/>
                    <b-button-group>
                        <submit-button ref="submit"
                                       @click="submit"
                                       label="Add"
                                       popover-placement="top"/>
                    </b-button-group>
                </b-input-group>
            </b-form-fieldset>
        </div>
    </div>
</template>

<script>
import Loader from './Loader';
import SubmitButton from './SubmitButton';

export default {
    name: 'new-course',
    data() {
        return {
            name: '',
            submitted: false,
        };
    },
    components: {
        SubmitButton,
        Loader,
    },

    methods: {
        submit() {
            const button = this.$refs.submit;

            if (this.name === '' || this.name == null) {
                button.fail('Please select a course name');
                return;
            }

            const req = this.$http.post('/api/v1/courses/', { name: this.name })
                .then(({ data: assig }) => {
                    window.location.href = `/courses/${assig.id}?created=true`;
                }).catch((err) => {
                    throw err.response.data.message;
                });
            button.submit(req);
        },
    },
};
</script>

<style lang="less">
.add-course {
    .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        height: 100%;
    }
}
</style>
