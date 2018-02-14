<template>
<div class="center loader" v-if="center">
    <icon name="refresh" :scale="scale" spin></icon>
</div>
<icon class="loader" v-else name="refresh" :scale="scale" spin></icon>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/refresh';

export default {
    name: 'loader',

    props: {
        center: {
            type: Boolean,
            default: true,
        },
        scale: {
            type: Number,
            default: 4,
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
.center.loader {
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
