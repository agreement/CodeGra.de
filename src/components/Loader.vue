<template>
    <div class="loader">
        <icon name="refresh" :scale="scale" spin></icon>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';

export default {
    name: 'loader',

    props: {
        scale: {
            type: Number,
            default: 1,
        },
    },

    components: {
        Icon,
    },
};
</script>
