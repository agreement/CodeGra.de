<template>
<b-form-fieldset class="password-input">
    <b-input-group>
        <slot name="prepend">
            <b-input-group-prepend is-text v-if="label">{{ label }}</b-input-group-prepend>
        </slot>
        <input v-if="visible"
               :tabindex="tabindex"
               type="text"
               v-model="password"
               class="form-control"/>
        <input v-else
               :tabindex="tabindex"
               type="password"
               v-model="password"
               class="form-control"/>
        <b-input-group-append>
            <b-button @click="visible = !visible"
                      variant="primary">
                <icon v-if="visible" name="eye-slash"></icon>
                <icon v-else name="eye"></icon>
            </b-button>
        </b-input-group-append>
    </b-input-group>
</b-form-fieldset>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye';
import 'vue-awesome/icons/eye-slash';

export default {
    name: 'password-input',

    props: {
        value: {
            default: '',
        },

        label: {
            default: '',
            type: String,
        },

        tabindex: {
            default: undefined,
        },
    },

    data() {
        return {
            visible: false,
            password: this.value,
        };
    },

    watch: {
        value(val) {
            this.password = val;
        },

        password() {
            this.$emit('input', this.password);
        },
    },

    components: {
        Icon,
    },
};
</script>
