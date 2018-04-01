<template>
<div class="toggle-container"
     :class="{ disabled, colors }"
     :checked="current == valueOn">
    <div :id="toggleId">
        <div class="label-off"
            @click="toggle(false)">
            {{ labelOff }}
        </div>
        <div class="toggle"
             @click="toggle()"/>
        <div class="label-on"
             @click="toggle(true)">
            {{ labelOn }}
        </div>
    </div>
    <b-popover placement="top"
               v-if="disabled"
               triggers="hover"
               :target="toggleId">
        {{ disabledText }}
    </b-popover>
</div>
</template>

<script>
let i = 0;

export default {
    name: 'toggle',

    props: {
        value: {
            default: false,
        },
        labelOn: {
            type: String,
            default: 'on',
        },
        labelOff: {
            type: String,
            default: 'off',
        },
        valueOn: {
            default: true,
        },
        valueOff: {
            default: false,
        },
        disabled: {
            default: false,
        },
        disabledText: {
            default: '',
            type: String,
        },
        colors: {
            default: true,
            type: Boolean,
        },
    },

    data() {
        return {
            current: this.value === this.valueOn,
            toggleId: `toggle-${i++}`,
        };
    },

    watch: {
        value(to) {
            this.current = to;
        },
    },

    methods: {
        toggle(to) {
            if (this.disabled) return;

            const newState = to == null ? !this.current : to;

            if (newState !== this.current) {
                this.current = newState;
                this.$emit('input', this.current ? this.valueOn : this.valueOff);
            }
        },
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

@transition-duration: 300ms;
@unchecked-opacity: .5;

.toggle-container {
    cursor: default;

    &.disabled {
        cursor: not-allowed;
    }
}

.label-off,
.label-on,
.toggle {
    display: inline-block;
    vertical-align: middle;
    cursor: pointer;

    .disabled & {
        opacity: @unchecked-opacity;
        cursor: not-allowed;
    }
}

.toggle {
    position: relative;
    width: 2.1rem;
    height: 1.2rem;
    margin: 0 .5rem;
    border-radius: .6rem;

    background-color: @color-light-gray;
    transition: background-color @transition-duration;

    &::before {
        content: '';
        display: block;
        width: 1rem;
        height: 1rem;
        transform: translate(.1rem, .1rem);
        border-radius: 50%;

        background-color: white;
        transition: transform @transition-duration;
    }
}

.label-on,
.label-off {
    transition: opacity @transition-duration;
}

.label-on {
    opacity: @unchecked-opacity;
}

[checked] {
    &.colors .toggle {
        background-color: @color-primary;

        #app.dark & {
            background-color: @color-primary-darkest;
        }

    }
    .toggle::before {
        transform: translate(100%, .1rem);
    }

    .label-on {
        opacity: 1;
    }

    .label-off {
        opacity: @unchecked-opacity;
    }
}
</style>
