<template>
    <div class="assignment-state">
        <b-form-fieldset label="Assignment name">
            <b-input-group>
                <b-form-input v-model="name"></b-form-input>
            </b-input-group>
        </b-form-fieldset>
        <b-form-fieldset label="Deadline & state">
            <b-input-group>
                <b-input-group-button>
                    <b-popover placement="top" triggers="hover" :content="error" show v-if="error">
                        <b-button variant="danger">
                            <icon name="times"/>
                        </b-button>
                    </b-popover>
                    <b-button :variant="success ? 'success' : 'primary'" @click="submitAssignment" v-else>
                        <icon name="refresh" spin v-if="sending"></icon>
                        <span v-else>Submit</span>
                    </b-button>
                </b-input-group-button>
                <b-form-input type="datetime-local" v-model="deadline"></b-form-input>
                <b-input-group-button @click.native="updateState">
                    <b-popover placement="top" triggers="hover" content="Hidden">
                        <b-button :variant="state === assignmentState.HIDDEN ? 'danger' : 'outline-danger'" :value="assignmentState.HIDDEN">
                            <icon name="eye-slash"></icon>
                        </b-button>
                    </b-popover>
                </b-input-group-button>
                <b-input-group-button @click.native="updateState">
                    <b-popover placement="top" triggers="hover" content="Open">
                        <b-button :variant="state === 'open' ? 'warning' : 'outline-warning'" value="open">
                            <icon name="clock-o"></icon>
                        </b-button>
                    </b-popover>
                </b-input-group-button>
                <b-input-group-button @click.native="updateState">
                    <b-popover placement="top" triggers="hover" content="Done">
                        <b-button :variant="state === assignmentState.DONE ? 'success' : 'outline-success'" :value="assignmentState.DONE">
                            <icon name="check"></icon>
                        </b-button>
                    </b-popover>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import * as assignmentState from '../store/assignment-states';

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
            assignmentState,
            name: this.assignment ? this.assignment.name : '',
            deadline: this.assignment ? this.assignment.deadline : 0,
            state: this.assignment ? this.convertState(this.assignment.state) : 'hidden',
            sending: false,
            success: false,
            error: false,
        };
    },

    watch: {
        name() {
            this.$emit('nameUpdated', this.name);
        },
    },

    methods: {
        convertState(state) {
            switch (state) {
            case assignmentState.GRADING:
            case assignmentState.SUBMITTING:
                return 'open';
            default: return state;
            }
        },

        submitAssignment() {
            this.sending = true;
            const d = new Date(this.deadline);
            const assignment = {
                name: this.name,
                deadline: `${d.getUTCFullYear()}-${d.getUTCMonth() + 1}-${d.getUTCDate()}T${d.getUTCHours()}:${d.getUTCMinutes()}`,
                state: this.convertState(this.state),
            };
            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, assignment).then(() => {
                this.sending = false;
                this.success = true;
                setTimeout(() => { this.success = false; }, 1000);
                this.$emit('submit', assignment);
            }).catch((err) => {
                this.error = err.response.data.message;
                this.sending = false;
                this.success = false;
                this.$emit('submit', assignment);
                this.$nextTick(() => setTimeout(() => { this.error = false; }, 2000));
            });
        },

        updateState(event) {
            const button = event.target.closest('button');
            if (button != null) {
                this.state = button.getAttribute('value');
                this.$emit('stateUpdated', this.state);
            }
        },
    },

    components: {
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
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }

    & > :not(:last-child) button {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }
}
</style>
