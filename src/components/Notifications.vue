<template>
<div class="notifications">
    <div>
        <b-form-checkbox v-model="graders">
            <b>Graders</b>
            <description-popover
                description="Toggle this checkbox to send a reminder to the
                             graders that are causing the grading to not be done
                             at the given time."
                placement="right"/>
        </b-form-checkbox>
        <b-collapse :visible="graders" :id="`collapse-${Math.random()}`">
            <b-input-group prepend="Time to send"
                           class="extra-box">
                <input type="datetime-local"
                       @keyup.ctrl.enter="updateReminder"
                       class="form-control"
                       v-model="reminderTime"/>
            </b-input-group>
        </b-collapse>
    </div>
    <hr/>
    <div>
        <b-form-checkbox v-model="finished">
            <b>Finished</b>
            <description-popover
                description="Toggle this checkbox to send the given email
                             address a reminder when the grading is done. You
                             can select multiple address in the same as in your
                             email client."
                placement="right"/>
        </b-form-checkbox>
        <b-collapse :visible="finished" :id="`collapse-${Math.random()}`">
            <b-input-group prepend="Send to"
                           class="extra-box">
                <input type="text"
                       @keyup.ctrl.enter="updateReminder"
                       class="form-control"
                       v-model="doneEmail"/>
            </b-input-group>
        </b-collapse>
    </div>
    <hr/>
    <b-collapse :visible="graders || finished"
                class="grade-options"
                :id="`collapse-${Math.random()}`">
        <b-form-radio-group v-model="doneType">
            <b-form-radio v-for="item in options"
                          :key="item.value"
                          :value="item.value">
                {{ item.text }}
                <description-popover
                    :description="item.help"
                    hug-text
                    placement="right"/>
            </b-form-radio>
        </b-form-radio-group>
        <hr style="width: 100%"/>
    </b-collapse>

    <submit-button ref="updateReminder" @click="updateReminder"/>
</div>
</template>

<script>
import { mapActions } from 'vuex';
import moment from 'moment';

import { convertToUTC, parseWarningHeader } from '@/utils';

import SubmitButton from './SubmitButton';
import DescriptionPopover from './DescriptionPopover';

export default {
    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    computed: {
        assignmentUrl() {
            return `/api/v1/assignments/${this.assignment.id}`;
        },
    },

    data() {
        return {
            graders: this.assignment.has_reminder_time,
            reminderTime: this.assignment.reminder_time,
            finished: this.assignment.done_email != null,
            doneEmail: this.assignment.done_email,
            doneType: this.assignment.done_type,
            options: [
                {

                    text: 'Assigned graders only',
                    value: 'assigned_only',
                    help: `
Only send to graders that have work assigned to them. This can be because they were
divided or because they were assigned work manually.`,
                },
                {
                    text: 'All graders',
                    value: 'all_graders',
                    help: 'Send a reminder e-mail to all graders.',
                },
            ],
        };
    },

    watch: {
        finished(val) {
            if (!val && !this.graders) {
                this.doneType = null;
            }
        },

        graders(val) {
            if (!val && !this.finished) {
                this.doneType = null;
            }
        },
    },

    methods: {
        ...mapActions('courses', ['updateAssignment']),

        updateReminder() {
            const type = this.graders || this.finished ? String(this.doneType) : null;
            const time = this.graders ? convertToUTC(this.reminderTime) : null;
            const email = this.finished ? this.doneEmail : null;
            const button = this.$refs.updateReminder;

            if ((this.graders || this.finished) && !type) {
                let msg = 'Please select when grading on this assignment should be considered finished.';
                if (this.graders) {
                    msg += ' This also indicates who should get a notification when they are not yet done grading.';
                }
                button.fail(msg);
                return;
            }

            const props = {
                done_type: type,
                done_email: email,
                reminder_time: time,
            };

            const req = this.$http.patch(this.assignmentUrl, props).then((res) => {
                if (type != null) {
                    props.reminder_time = moment.utc(time).local().format('YYYY-MM-DDTHH:mm');
                }

                this.updateAssignment({
                    assignmentId: this.assignment.id,
                    assignmentProps: props,
                });

                if (res.headers.warning) {
                    button.cancel();
                    button.warn(parseWarningHeader(res.headers.warning).text);
                }
            }, (err) => {
                throw err.response.data.message;
            });

            button.submit(req);
        },
    },

    components: {
        SubmitButton,
        DescriptionPopover,
    },
};
</script>

<style lang="less" scoped>
hr {
    margin-top: .5rem;
    margin-bottom: .5rem;
}

.grade-options {
    padding-left: 3px;

    & > .custom-control:last-child {
        margin-bottom: 0;
    }
}

label {
    margin-bottom: 0;
}

.extra-box {
    padding: 0.75em 0;
}

.submit-button {
    display: flex;
    justify-content: flex-end;
}
</style>
