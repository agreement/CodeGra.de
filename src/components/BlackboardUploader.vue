<template>
    <b-form method="post" :action="action" enctype="multipart/form-data">
        <b-form-fieldset>
            <b-form-file name="file" v-model="file"></b-form-file>
        </b-form-fieldset>
        Selected file: {{ file && file.name }}
        <b-button variant="primary" type="submit">Submit</b-button>
    </b-form>
</template>

<script>
import { bForm, bFormFieldset, bFormFile, bFormButton, bButton } from 'bootstrap-vue/lib/components';

export default {
    name: 'blackboard-uploader',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    computed: {
        action: function action() {
            return this.assignment ? `/api/v1/assignments/${this.assignment.id}/submissions/` : null;
        },
    },

    data() {
        return {
            file: null,
        };
    },

    components: {
        bForm,
        bFormFieldset,
        bFormFile,
        bFormButton,
        bButton,
    },
};
</script>
