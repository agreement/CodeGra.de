<template>
    <div class="loader" v-if="center">
        <icon name="refresh" :scale="scale" spin></icon>
    </div>
    <icon v-else name="refresh" :scale="scale" spin></icon>
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
.loader {
    display: -webkit-flex; /* Safari */
    display: flex;
    -webkit-align-items: center; /* Safari 7.0+ */
    align-items: center;
    -webkit-justify-content: center;
    justify-content: center;
}
</style>
