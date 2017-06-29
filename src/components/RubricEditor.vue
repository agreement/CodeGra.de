<template>
    <div class="rubric-editor">
        <b-form-fieldset>
            <b-button-toolbar justify>
                <submit-button
                    @click.native="submit"
                    ref="submitButton"/>

                <submit-button
                    class="submit-button row-button"
                    size="sm"
                    @click.native="createRow"
                    ref="createRowButton"
                    label="+"/>
            </b-button-toolbar>
        </b-form-fieldset>

        <b-card no-block
            v-for="(rubric, i) in rubrics"
            :key="`rubric-${rubric.id}`"
            class="rubric"
            @keyup.native.ctrl.enter="submit">
            <div class="card-header rubric-header">
                <span class="title">
                    <b contenteditable>{{ rubric.header }}</b>
                    -
                    <span contenteditable>{{ rubric.description }}</span>
                </span>
                <span class="index">
                    {{ i + 1 }} / {{ rubrics.length }}
                </span>
            </div>

            <b-card-group>
                <div
                    v-for="item in rubric.items"
                    :key="`rubric-${rubric.id}-${item.id}`"
                    @click.native="selected = item"
                    :class="{ selected: selected === item, }"
                    class="card rubric-item">
                    <div class="card-block">
                        <b contenteditable>{{ item.points }}</b>
                        -
                        <span contenteditable>{{ item.description }}</span>
                    </div>
                </div>
            </b-card-group>

            <submit-button
                class="submit-button col-button"
                label="+"
                size="sm"
                @click.native="createCol(i)"
                :ref="`createColButton_${rubric.id}`"/>
        </b-card>
    </div>
</template>

<script>
import SubmitButton from './SubmitButton';

export default {
    name: 'rubric-editor',

    data() {
        return {
            rubrics: [
                {
                    description: 'The style of the code is conform the styleguide.',
                    header: 'Style',
                    id: 4,
                    items: [
                        {
                            col: 1,
                            description: 'Expert',
                            id: 10,
                            points: 3.0,
                        },
                        {
                            col: 2,
                            description: 'Competent',
                            id: 11,
                            points: 2.0,
                        },
                        {
                            col: 3,
                            description: 'Novice',
                            id: 12,
                            points: 1.0,
                        },
                    ],
                },
                {
                    description: 'The documentation of the code is well written and complete.',
                    header: 'Documentation',
                    id: 5,
                    items: [
                        {
                            col: 1,
                            description: 'Expert',
                            id: 13,
                            points: 2.0,
                        },
                        {
                            col: 2,
                            description: 'Competent',
                            id: 14,
                            points: 1.5,
                        },
                        {
                            col: 3,
                            description: 'Novice',
                            id: 15,
                            points: 1.0,
                        },
                    ],
                },
                {
                    description: 'The code is well-strutured and design choices are logical.',
                    header: 'Code structure',
                    id: 6,
                    items: [
                        {
                            col: 1,
                            description: 'Expert',
                            id: 16,
                            points: 4.0,
                        },
                        {
                            col: 2,
                            description: 'Competent',
                            id: 17,
                            points: 2.5,
                        },
                        {
                            col: 3,
                            description: 'Novice',
                            id: 18,
                            points: 1.0,
                        },
                    ],
                },
            ],
            selected: null,
        };
    },

    mounted() {
        this.$http.get(
            `/api/v1/assignments/${this.assignmentId}/rubrics/`,
        ).then(({ data: { rubrics } }) => {
            this.rubrics = rubrics;
        }, (err) => {
            // eslint-disable-next-line
            console.dir(err);
        });
    },

    methods: {
        createRow() {
            this.rubrics.push({
                header: '',
                description: '',
                items: [],
            });
        },

        createCol(row) {
            this.rubrics[row].items.push({
                description: '',
                points: 0,
            });
        },

        submit() {
            this.$refs.submitButton.submit(
                this.$http.patch(`/api/v1/assignments/${this.assignmentId}/rubrics/`, {
                    rubrics: this.rubrics,
                }),
            ).catch((err) => {
                // eslint-disable-next-line
                console.dir(err);
            });
        },
    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
.rubric {
    flex: 1 1 0;
    margin-bottom: 1rem;
}

.card-header,
.card-block {
    padding: .5rem .75rem;
}

.rubric-header {
    display: flex;
    flex-direction: row;

    .title {
        flex: 1 1 0;
    }

    .index {
        flex: 0 0 auto;
        margin-left: 1rem;
    }
}

.rubric-item {
    border-width: 0;

    &:not(:last-child) {
        border-right-width: 1px;
    }

    &.selected {
        background: rgba(0, 0, 0, 0.05);
    }

    &:hover {
        background: rgba(0, 0, 0, 0.075);
    }

    .card-block {
        display: flex;

        :not(:last-child) {
            flex: 0 0 auto;
        }

        :last-child {
            flex: 1 1 0;
        }
    }

    .submit-button {
        position: absolute;

        &.col-button {
            top: 50%;
            left: 100%;
        }
    }
}

[contenteditable] {
    margin: -.5rem 0;
    padding: .5rem .75rem;

    &:focus {
        background: white;
    }
}
</style>
