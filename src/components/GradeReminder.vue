<template>
<div>
    <b-input-group left="Time to send">
        <b-form-input type="datetime-local" v-model="assignment.reminder_time"/>
    </b-input-group>
    <b-form-radio v-model="assignment.reminder_type"
                  class="grade-options"
                  stacked
                  :options="[
                            {text: 'No graders', value: 'none'},
                            {text: 'Assigned graders only', value: 'assigned_only'},
                            {text: 'All graders', value: 'all_graders'},
                            ]"/>
    <submit-button @click="updateReminder" ref="updateReminder" label="Set reminder"/>
</div>
</template>

<script>
import { convertToUTC } from '@/utils';

import SubmitButton from './SubmitButton';

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

    methods: {
        updateReminder() {
            const req = this.$http.patch(this.assignmentUrl, {
                reminder_type: this.assignment.reminder_type,
                reminder_time: convertToUTC(this.assignment.reminder_time),
            });
            this.$refs.updateReminder.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less">
.grade-options {
    margin: .75em 0;

    & > .custom-control:last-child {
        margin-bottom: 0;
    }
}
</style>
