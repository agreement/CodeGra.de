<template>
    <b-button :href="link">Export feedback</b-button>
</template>

<script>
export default {
    name: 'feedback-exporter',

    props: ['id'],

    computed: {
        link: function link() {
            return `/api/v1/submissions/${this.id}?type=feedback`;
        },
    },
};
</script>
