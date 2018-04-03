<template>
<div class="submit-input">
    <div @keyup.ctrl.enter="submit">
        <b-form-fieldset>
            <b-input-group>
                <input type="text"
                       class="form-control"
                       :placeholder="placeholder"
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
    name: 'submit-input',

    props: {
        placeholder: {
            default: undefined,
        },
    },

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
                button.fail('Please give a name');
                return;
            }

            const req = new Promise((resolve, reject) => {
                this.$emit('create', this.name, resolve, reject);
            }).then(() => {
                this.name = '';
            });

            button.submit(req);
        },
    },
};
</script>

<style lang="less">
.submit-input .btn {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    height: 100%;
}
</style>
