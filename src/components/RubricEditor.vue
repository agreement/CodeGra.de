<template>
    <div class="rubric-editor">
        <b-card no-block
            v-for="(rubric, i) in rubrics"
            :key="`rubric-${i}`"
            class="rubric"
            @keyup.native.ctrl.enter="submit">
            <div class="card-header rubric-header">
                <span class="title">
                    <input
                        class="row-header"
                        placeholder="Rubric title"
                        v-model="rubric.header">
                    <br>
                    <textarea
                        :rows="1"
                        class="row-description"
                        placeholder="Rubric description"
                        v-model="rubric.description">
                    </textarea>
                </span>
                <span class="index">{{ i + 1 }} / {{ rubrics.length }}</span>
            </div>

            <b-card-group class="rubric-row">
                <div
                    v-for="(item, j) in rubric.items"
                    :key="`rubric-${i}-${j}`"
                    @click.native="selected = item"
                    :class="{ selected: selected === item, }"
                    class="card rubric-item">
                    <div class="card-block">
                        <input
                            type="number"
                            class="item-points"
                            placeholder="Item points"
                            v-model="item.points">
                        <span class="sep">-</span>
                        <textarea
                            :rows="1"
                            class="item-description"
                            placeholder="Item description"
                            v-model="item.description">
                        </textarea>
                    </div>
                </div>

                <b-button
                    variant="success"
                    size="sm"
                    class="add-col-button"
                    @click.native="createCol(i)">
                    <icon name="plus"/>
                </b-button>

                <b-button
                    variant="danger"
                    size="sm"
                    class="del-row-button"
                    @click.native="deleteRow(i)">
                    <icon name="times"/>
                </b-button>
            </b-card-group>
        </b-card>

        <b-form-fieldset>
            <b-button-toolbar justify>
                <submit-button
                    @click.native="submit"
                    ref="submitButton"/>

                <b-popover placement="bottom" triggers="hover"
                    content="Create new row">
                    <b-button
                        variant="success"
                        size="sm"
                        style="height: 100%"
                        class="row-button"
                        @click.native="createRow">
                        <icon name="plus"/>
                    </b-button>
                </b-popover>
            </b-button-toolbar>
        </b-form-fieldset>
    </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/times';

import SubmitButton from './SubmitButton';

export default {
    name: 'rubric-editor',

    data() {
        return {
            rubrics: [],
            selected: null,
        };
    },

    props: {
        assignmentId: {
            type: Number,
            default: undefined,
        },
    },

    watch: {
        assignmentId() {
            this.getRubrics();
        },
    },

    mounted() {
        this.getRubrics();
    },

    methods: {
        getRubrics() {
            if (!this.assignmentId) return;

            this.$http.get(
                `/api/v1/assignments/${this.assignmentId}/rubrics/`,
            ).then(({ data: rubrics }) => {
                this.rubrics = rubrics;
            }, (err) => {
                // eslint-disable-next-line
                console.dir(err);
                this.rubrics = [];
            });
        },

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
                this.$http.put(`/api/v1/assignments/${this.assignmentId}/rubrics/`, {
                    rows: this.rubrics,
                }),
            ).catch((err) => {
                // eslint-disable-next-line
                console.dir(err);
            });
        },

        deleteRow(row) {
            const [rubric] = this.rubrics.splice(row, 1);
            this.$http.delete(
                `/api/v1/assignments/${this.assignmentId}/rubrics/${rubric.id}`,
            ).catch(() => this.rubrics.splice(row, 0, rubric));
        },
    },

    components: {
        Icon,
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

.rubric-row {
    position: relative;
}

.rubric-item {
    border-width: 0;
    border-top-width: 1px;
    margin-top: -1px;

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
}

.add-col-popover {
    > span {
        display: block;
        height: 100%;
    }
}

.add-col-button {
    border-top-right-radius: 0;
    border-top-left-radius: 0;
    border-bottom-right-radius: 0;

    &:not(:first-child) {
        border-bottom-left-radius: 0;
    }
}

.del-row-button {
    border-top-right-radius: 0;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}

input,
textarea {
    font-family: initial;
    background: transparent;
    border-width: 0;

    &:focus {
        border-width: 1px;
    }

    &.row-header,
    &.row-description {
        width: 100%;
    }

    &.row-header {
        font-weight: bold;
    }

    &.row-description {

    }

    &.item-points {
        width: 2em;
        padding-right: 0;
    }

    &.item-description {

    }
}

.sep {
    padding: 0 .33em;
}
</style>
