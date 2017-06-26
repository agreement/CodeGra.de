<template>
    <div class="rubric-viewer">
        <b-card-group
            v-for="(row, i) in rows" :key="`row-${i}`">
            <b-card
                v-for="(col, j) in row" :key="`row-${i}-col-${j}`"
                @click.native="select(i, j)"
                :class="{ selected: selected[i] == j }">
                {{ col }}
            </b-card>
        </b-card-group>
    </div>
</template>

<script>
import { bCard, bCardGroup } from 'bootstrap-vue/lib/components';

export default {
    name: 'rubric-viewer',

    props: {
        rows: {
            type: Array,
            default() {
                return [
                    [
                        'stupid',
                        'meh',
                        'alright',
                        'good',
                        'excellent',
                    ],
                    [
                        'stupid',
                        'meh',
                        'alright',
                        'good',
                        'excellent',
                    ],
                ];
            },
        },
    },

    data() {
        return {
            selected: this.rows.map(() => -1),
        };
    },

    methods: {
        select(row, col) {
            this.$set(this.selected, row, col);
        },
    },

    components: {
        bCard,
        bCardGroup,
    },
};
</script>

<style lang="less" scoped>
.card {
    cursor: pointer;

    &:hover {
        background: rgba(0, 0, 0, 0.075);
    }

    &.selected {
        font-weight: bold;
        background: rgba(0, 0, 0, 0.075);
    }
}
</style>
