<template>
    <b-popover :placement="placement"
               :content="description"
               triggers="hover"
               class="description-popover"
               style="{ float: hugText ? 'none' : 'right' }">
        <sup v-if="hugText" class="desc-pop-span">
            <icon name="info" scale="0.75"/>
        </sup>
        <span v-else class="desc-pop-span">
            <icon name="info" scale="0.75"/>
        </span>
    </b-popover>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/info';

export default {
    name: 'description-popover',

    props: {
        description: {
            type: String,
        },

        hugText: {
            type: Boolean,
            default: false,
        },

        placement: {
            type: String,
            default: 'left',
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less">
.desc-pop-span {
    padding: 0 0.5em;
    height: 100%;
    display: inline-block;
}

.description-popover {
    display: inline;
    cursor: help;
}
</style>
