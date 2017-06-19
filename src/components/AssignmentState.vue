<template>
    <div class="assignment-state">
        <b-form-fieldset label="Assignment name">
            <b-input-group>
                <b-form-input v-model="name"></b-form-input>
            </b-input-group>
        </b-form-fieldset>
        <b-form-fieldset label="Date & state">
            <b-input-group>
                <b-input-group-button>
                    <b-button :variant="success ? 'success' : 'primary'" @click="submitAssignment">
                        <icon name="refresh" spin v-if="sending"></icon>
                        <span v-else>Submit</span>
                    </b-button>
                </b-input-group-button>
                <b-form-input type="datetime-local" v-model="date"></b-form-input>
                <b-input-group-button @click.native="updateState">
                    <b-button-group>
                        <b-tooltip placement="bottom" content="Hidden">
                            <b-button :variant="state_name == 'hidden' ? 'danger' : 'outline-danger'" value="hidden"><icon name="eye-slash"></icon></b-button>
                        </b-tooltip>
                        <b-tooltip placement="bottom" content="Open">
                            <b-button :variant="state_name == 'submitting' || state_name == 'grading' ? 'warning' : 'outline-warning'" value="open"><icon name="clock-o"></icon></b-button>
                        </b-tooltip>
                        <b-tooltip placement="bottom" content="Done">
                            <b-button :variant="state_name == 'done' ? 'success' : 'outline-success'" value="done"><icon name="check"></icon></b-button>
                        </b-tooltip>
                    </b-button-group>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bFormFieldset, bFormInput, bInputGroup, bPopover, bTooltip } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';

export default {
    name: 'assignment-state',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            name: this.assignment ? this.assignment.name : '',
            date: this.assignment ? this.assignment.date : 0,
            state_name: this.assignment ? this.assignment.state_name : 'hidden',
            sending: false,
            success: false,
        };
    },

    watch: {
        name() {
            this.$emit('updateName', this.name);
        },
    },

    methods: {
        submitAssignment() {
            this.sending = true;
            const d = new Date(this.date);
            const assignment = {
                name: this.name,
                date: `${d.getUTCFullYear()}-${d.getUTCMonth() + 1}-${d.getUTCDate()}T${d.getUTCHours()}:${d.getUTCMinutes()}`,
                state: this.state_name,
            };
            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, { assignment }).then(() => {
                this.sending = false;
                this.success = true;
                setTimeout(() => { this.success = false; }, 1000);
                this.$emit('submit', assignment);
            });
        },

        updateState(event) {
            const button = event.target.closest('button');
            if (button != null) {
                this.state_name = button.getAttribute('value');
                this.$emit('updateState', this.state_name);
            }
        },
    },

    components: {
        bButton,
        bButtonGroup,
        bFormFieldset,
        bFormInput,
        bInputGroup,
        bPopover,
        bTooltip,
        Icon,
    },
};
</script>

<style lang="less" scoped>
input.form-control {
     flex-direction: row;
}

.btn-group {
    button {
        cursor: pointer;
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }

    & > :not(:last-child) button {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }
}
</style>
