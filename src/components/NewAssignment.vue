<template>
    <div id="newAssignment">
        <div @keyup.ctrl.enter="submit">
            <b-form-fieldset class="add-assignment">
                <b-input-group>
                    <input type="text"
                           class="form-control"
                           placeholder="New assignment name"
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
    name: 'new-assignment',
    props: ['courseId'],

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
                button.fail('Please select a assignment name');
                return;
            }

            const req = this.$http.post(`/api/v1/courses/${this.courseId}/assignments/`, {
                name: this.name,
            }).then(({ data: assig }) => {
                this.name = '';
                this.$emit('created', assig);
            }).catch((err) => {
                throw err.response.data.message;
            });

            button.submit(req);
        },
    },
};
</script>

<style lang="less">
.add-assignment {
    .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        height: 100%;
    }
}
</style>
