<template>
<div class="local-header">
    <b-button-toolbar class="toolbar" justify>
        <div class="sidebar-toggle">
            <img src="/static/img/bars.svg"
                 @click="toggleSidebar()">
        </div>

        <h4 v-if="title || $slots.title" class="title">
            <slot name="title">{{ title }}</slot>
        </h4>

        <slot/>

        <b-input-group-append v-if="hasExtraSlot"
                              class="extra-button"
                              v-b-popover.bottom.hover="`${showExtra ? 'Hide' : 'Show'} more options`">
            <b-button v-b-toggle.local-header-extra
                      style="margin-left: 15px;"
                      @click="showExtra = !showExtra">
                <icon name="angle-double-up" v-if="showExtra"/>
                <icon name="angle-double-down" v-else/>
            </b-button>
        </b-input-group-append>
    </b-button-toolbar>

    <b-collapse id="local-header-extra" v-if="hasExtraSlot">
        <hr class="separator">
        <slot name="extra"/>
    </b-collapse>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-double-down';
import 'vue-awesome/icons/angle-double-up';

export default {
    name: 'local-header',

    props: {
        title: {
            type: String,
            default: '',
        },
    },

    computed: {
        hasExtraSlot() {
            return !!this.$slots.extra;
        },
    },

    data() {
        return {
            showExtra: false,
        };
    },

    methods: {
        toggleSidebar() {
            this.$root.$emit('sidebar::show');
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.local-header {
    position: sticky;
    top: 0;
    z-index: 3;
    margin: 0 -15px 15px;
    border: 0;
    padding: 1rem;
    .default-footer-colors;
    box-shadow: 0 0 4px rgba(0, 0, 0, .75);
    color: @text-color;
}

.sidebar-toggle {
    cursor: pointer;
    margin-right: 1rem;

    img {
        width: 2rem;
    }

    @media @media-no-small {
        display: none;
    }
}

.title {
    display: inline-block;
    margin-bottom: 0;
}

.toolbar {
    flex: 1 1 auto;
    flex-shrink: 0;
    align-items: center;
    margin-top: -.25rem;
}

.separator {
    margin: 1em 0;
    border-color: @color-border-gray;

    #app.dark & {
        border-color: @color-primary-darkest;
    }
}
</style>

<style lang="less">
.local-header > .toolbar > div {
        margin-top: .25rem;
}
</style>
