<template>
    <div v-if="editable && permissions.can_edit_assignment_info">
        <b-button-group @click.native="updateState">
            <b-popover placement="top" triggers="hover"
                    content="Hidden or open, managed by LTI"
                    v-if="assignment.is_lti">
                <b-button class="state-button larger"
                        :size="size"
                        :variant="ltiHiddenOpenVariant"
                        :disabled="true">
                    <icon :name="icons[states.HIDDEN]"/>
                    <icon :name="icons[states.OPEN]"/>
                </b-button>
            </b-popover>

            <b-button-group v-else>
                <b-popover placement="top" triggers="hover"
                        :content="labels[states.HIDDEN]">
                    <b-button class="state-button"
                            :size="size"
                            value="hidden"
                            :variant="hiddenVariant">
                        <loader :scale="1" v-if="isLoadingHidden"/>
                        <icon :name="icons[states.HIDDEN]" v-else/>
                    </b-button>
                </b-popover>

                <b-popover placement="top" triggers="hover"
                        :content="labels[states.OPEN]">
                    <b-button class="state-button"
                            :size="size"
                            value="open"
                            :variant="openVariant">
                        <loader :scale="1" v-if="isLoadingOpen"/>
                        <icon :name="icons[states.OPEN]" v-else/>
                    </b-button>
                </b-popover>
            </b-button-group>

            <b-popover placement="top" triggers="hover"
                    :content="labels[states.DONE]">
                <b-button class="state-button"
                        :size="size"
                        value="done"
                        :variant="doneVariant">
                    <loader :scale="1" v-if="isLoadingDone"/>
                    <icon :name="icons[states.DONE]" v-else/>
                </b-button>
            </b-popover>
        </b-button-group>
    </div>
    <b-popover placement="top"
               triggers="hover"
               :content="labels[assignment.state]"
               v-else>
        <icon :name="icons[assignment.state]" class="state-icon"/>
    </b-popover>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

import * as states from '../store/assignment-states';

import Loader from './Loader';

export default {
    name: 'assignment-state',

    props: {
        assignment: {
            type: Object,
            default: null,
        },

        editable: {
            type: Boolean,
            default: false,
        },

        size: {
            type: String,
            default: 'md',
        },

        permissions: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            pendingState: '',
            states,
            labels: {
                [states.HIDDEN]: 'Hidden',
                [states.SUBMITTING]: 'Submitting',
                [states.GRADING]: 'Grading',
                [states.OPEN]: 'Open',
                [states.DONE]: 'Done',
            },
            icons: {
                [states.HIDDEN]: 'eye-slash',
                [states.SUBMITTING]: 'clock-o',
                [states.GRADING]: 'pencil',
                [states.OPEN]: 'clock-o',
                [states.DONE]: 'check',
            },
        };
    },

    computed: {
        ltiHiddenOpenVariant() {
            return this.assignment.state !== states.DONE ? 'primary' : 'outline-primary';
        },

        hiddenVariant() {
            return this.assignment.state === states.HIDDEN ? 'danger' : 'outline-danger';
        },

        openVariant() {
            const st = this.assignment.state;
            return st === states.SUBMITTING || st === states.GRADING ?
                'warning' : 'outline-warning';
        },

        doneVariant() {
            return this.assignment.state === states.DONE ? 'success' : 'outline-success';
        },

        isLoadingHidden() {
            return this.pendingState === states.HIDDEN;
        },

        isLoadingOpen() {
            const st = this.pendingState;
            return st === states.SUBMITTING || st === states.GRADING;
        },

        isLoadingDone() {
            return this.pendingState === states.DONE;
        },
    },

    methods: {
        updateState({ target }) {
            const button = target.closest('button');
            if (!button) return;

            this.pendingState = button.getAttribute('value');

            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                state: this.pendingState,
            }).then(() => {
                this.assignment.state = this.pendingState;
                this.pendingState = '';
            }, (err) => {
                // TODO: visual feedback
                // eslint-disable-next-line
                console.dir(err);
            });
        },
    },

    components: {
        Icon,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.state-button, .state-icon {
    width: 1.75em;
    margin-top: .5em;
    margin-left: .375em;
}

.state-icon {
    margin-top: .6em;
}

.state-button {
    height: 1.75em;
    border-radius: 50%;
    border: 0;
    padding-left: .375rem;

    svg {
        width: 1em;
        height: 1em;
    }

    &.larger {
        width: 3.5em;
        margin-left: 0;

        .btn-group {
            display: block;
        }

        .fa-icon {
            margin-left: 0;
        }
    }
}
</style>
