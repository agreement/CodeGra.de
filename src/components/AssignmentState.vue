<template>
    <div class="assignment-state">
        <b-form-fieldset label="Assignment name">
            <b-input-group>
                <b-form-input v-model="name"></b-form-input>
            </b-input-group>
        </b-form-fieldset>
        <b-form-fieldset>
            <b-input-group>
                <b-input-group-button>
                    <b-button variant="primary">Submit</b-button>
                </b-input-group-button>
                <b-form-input type="date" v-model="date"></b-form-input>
                <b-input-group-button @click.native="updateState">
                    <b-button-group>
                        <b-popover placement="top" triggers="hover" content="Hidden">
                            <b-button :variant="state == 0 ? 'default' : 'secondary'" value="0"><icon name="eye-slash"></icon></b-button>
                        </b-popover>
                        <b-popover placement="top" triggers="hover" content="Submitting">
                            <b-button :variant="state == 1 ? 'danger' : 'outline-danger'" value="1"><icon name="download"></icon></b-button>
                        </b-popover>
                        <b-popover placement="top" triggers="hover" content="Grading">
                            <b-button :variant="state == 2 ? 'warning' : 'outline-warning'" value="2"><icon name="pencil"></icon></b-button>
                        </b-popover>
                        <b-popover placement="top" triggers="hover" content="Done">
                            <b-button :variant="state == 3 ? 'success' : 'outline-success'" value="3"><icon name="check"></icon></b-button>
                        </b-popover>
                    </b-button-group>
                </b-input-group-button>
            </b-input-group>
        </b-form-fieldset>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bFormFieldset, bFormInput, bInputGroup, bPopover } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/download';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

export default {
    name: 'assignment-state',

    props: {
        assignment: {
            type: Object,
            default: {},
        },
    },

    data() {
        return {
            name: this.assignment ? this.assignment.name : '',
            date: this.assignment ? this.assignment.date : 0,
            state: this.assignment ? this.assignment.state : -1,
        };
    },

    methods: {
        patchAssignment() {
            this.$http.patch(`/api/v1/courses/${this.courseId}/assignments/${this.assignmentId}`, {
                assignment: this.assignment,
            }).then((res) => {
                // eslint-disable-next-line
                console.log(res);
            });
        },

        updateState(event) {
            const button = event.target.closest('button');
            if (button != null) {
                this.state = Number(button.getAttribute('value'));
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
        Icon,
    },
};
</script>

<style lang="less" scoped>
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
