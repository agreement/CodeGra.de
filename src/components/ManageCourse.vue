<template>
    <b-list-group class="manage-course">
        <b-list-group-item v-for="a in assignments">
            <manage-assignment :assignment="a"></manage-assignment>
        </b-list-group-item>
    </b-list-group>
</template>

<script>
import { bListGroup, bListGroupItem } from 'bootstrap-vue/lib/components';

import ManageAssignment from './ManageAssignment';

export default {
    name: 'manage-course',

    props: {
        assignments: {
            type: Array,
            default: [],
        },
    },

    components: {
        ManageAssignment,
        bListGroup,
        bListGroupItem,
    },
};
</script>
