<template>
<div class="center loader" :class="{ 'page-loader': pageLoader }" v-if="center">
    <icon name="circle-o-notch" :scale="scale" spin></icon>
</div>
<icon class="loader" v-else name="circle-o-notch" :scale="scale" spin></icon>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/circle-o-notch';

export default {
    name: 'loader',

    props: {
        center: {
            type: Boolean,
            default: true,
        },
        pageLoader: {
            type: Boolean,
            default: false,
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
    &.page-loader {
        flex: 1 1 auto;
    }
}
</style>
