<template>
    <loader v-if="loading"/>
    <b-form-fieldset class="rubric-editor" v-else>
        <div class="outer-container">
            <b-card-group class="tab-container">
                <b-card v-for="(row, i) in rubrics"
                        :key="`rubric-row-${row.id}-${i}`"
                        style="flex-basis: 20%;"
                        :class="{active: i === currentCategory, tab: true}"
                        @click="gotoItem(i)">
                    <input type="text"
                           class="row-header form-control"
                           placeholder="Category name"
                           @click.native="editable && addRow(i)"
                           @focus="focusOnRow(i)"
                           v-model="row.header"
                           v-if="editable"/>
                    <b class="row-header" v-else>{{ row.header }}</b>
                    <div class="row-info-button"
                            v-b-popover.top.hover="'Select this category to create a new category.'"
                            v-if="editable && rubrics.length - 1 === i">
                        <icon name="info"/>
                    </div>
                    <div class="row-delete-button"
                         v-else-if="editable"
                         @click="(event) => { editable && deleteRow(i, event) }">
                        <icon name="times"/>
                    </div>
                </b-card>
            </b-card-group>
            <div class="inner-container"
                 ref="rubricContainer">
                <div class="rubric"
                     v-for="(rubric, i) in rubrics"
                     :key="`rubric-${rubric.id}-${i}`">
                    <b-card no-block>
                        <div class="card-header rubric-header">
                            <textarea class="form-control"
                                      :disabled="!editable"
                                      placeholder="Category description"
                                      :tabindex="currentCategory === i ? null: -1"
                                      @focus="focusOnRow(i)"
                                      v-model="rubric.description"
                                      v-if="editable"/>
                            <p v-else>{{ rubric.description }}</p>
                        </div>
                        <b-card-group class="rubric-items-container">
                            <b-card class="rubric-item"
                                    v-for="(item, j) in rubric.items"
                                    :key="`rubric-item-${item.id}-${j}-${i}`">
                                <b-input-group>
                                    <input v-if="editable"
                                           :disabled="!editable"
                                           type="number"
                                           class="form-control item-points"
                                           step="any"
                                           :tabindex="currentCategory === i ? null: -1"
                                           placeholder="Points"
                                           @focus="focusOnRow(i)"
                                           @change="item.points = parseFloat(item.points)"
                                           @keydown.native="editable && addItem(i, j)"
                                           @keydown.native.ctrl.enter="editable && submit()"
                                           v-model="item.points"/>
                                    <input v-else
                                           :disabled="!editable"
                                           type="text"
                                           class="form-control item-points"
                                           step="any"
                                           :tabindex="currentCategory === i ? null: -1"
                                           placeholder="Points"
                                           @focus="focusOnRow(i)"
                                           @change="item.points = parseFloat(item.points)"
                                           @keydown.native="editable && addItem(i, j)"
                                           @keydown.native.ctrl.enter="editable && submit()"
                                           v-model="item.points"/>
                                    <input type="text"
                                           class="form-control item-header"
                                           placeholder="Header"
                                           :disabled="!editable"
                                           :tabindex="currentCategory === i ? null: -1"
                                           @focus="focusOnRow(i)"
                                           @keydown="editable && addItem(i, j)"
                                           @keydown.ctrl.enter="editable && submit()"
                                           v-model="item.header"/>
                                </b-input-group>
                                <div class="item-info-button"
                                        v-if="rubric.items.length - 1 === j && editable"
                                        v-b-popover.top.hover="'Simply start typing to add a new item.'">
                                    <icon name="info"/>
                                </div>
                                <div class="item-delete-button"
                                     v-else-if="editable"
                                     @click="editable && deleteItem(i, j)">
                                    <icon name="times"/>
                                </div>
                                <textarea v-model="item.description"
                                          class="item-description form-control"
                                          :disabled="!editable"
                                          :rows="8"
                                          :tabindex="currentCategory === i ? null: -1"
                                          @focus="focusOnRow(i)"
                                          @keydown="editable && addItem(i, j)"
                                          @keydown.ctrl.enter="editable && submit()"
                                          placeholder="Description"/>
                            </b-card>
                        </b-card-group>
                    </b-card>
                </div>
            </div>
            <b-card class="button-bar" v-if="editable">
                <submit-button default="danger"
                               label="Delete"
                               ref="deleteButton"
                               @click="deleteRubric"/>
                <div class="override-checkbox">
                    <b-input-group>
                        <b-input-group-prepend is-text>
                            Max points<description-popover
                                          placement="top"
                                          description="The maximum amount of
                                                       points a user can get for
                                                       this rubric. You can set
                                                       this to a higher or lower
                                                       value manually, by
                                                       default it is the sum of
                                                       the max value in each
                                                       category."/>
                        </b-input-group-prepend>
                        <input type="number"
                               min="0"
                               step="1"
                               v-model="internalFixedMaxPoints"
                               @keydown.ctrl.enter="submitMaxPoints"
                               class="form-control"
                               :placeholder="curMaxPoints"/>
                        <b-input-group-append>
                            <submit-button @click="resetFixedMaxPoints()"
                                           class="round"
                                           ref="maxPointsButton"
                                           :disabled="internalFixedMaxPoints == null"
                                           v-b-popover.top.hover="'Reset to the default value.'"
                                           :label="false"
                                           default="warning">
                                <icon name="reply"/>
                            </submit-button>
                        </b-input-group-append>
                    </b-input-group>
                </div>
                <submit-button ref="submitButton"
                               @click="submit"/>
            </b-card>
            <b-card class="extra-bar" v-else>
                <span>
                    To get a full mark you need to score
                    {{ internalFixedMaxPoints || curMaxPoints }} points in this
                    rubric.
                </span>
                <slot/>
            </b-card>
        </div>
    </b-form-fieldset>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/plus';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/info';
import 'vue-awesome/icons/reply';
import arrayToSentence from 'array-to-sentence';

import SubmitButton from './SubmitButton';
import Loader from './Loader';
import DescriptionPopover from './DescriptionPopover';

export default {
    name: 'rubric-editor',
    data() {
        return {
            rubrics: [],
            selected: null,
            loading: true,
            currentCategory: 0,
            assignmentId: this.assignment.id,
            internalFixedMaxPoints: this.assignment.fixed_max_rubric_points,
        };
    },

    props: {
        assignment: {
            default: null,
        },

        editable: {
            type: Boolean,
            default: true,
        },

        fixedMaxPoints: {
            type: Number,
            default: null,
        },

        defaultRubric: {
            default: null,
        },
    },

    watch: {
        assignmentId() {
            this.getRubrics();
        },
    },

    mounted() {
        if (this.defaultRubric) {
            this.setRubricData(this.defaultRubric);
            this.loading = false;
        } else {
            this.getRubrics().then(() => {
                this.loading = false;
            });
        }
    },

    computed: {
        curMaxPoints() {
            return this.rubrics.reduce(
                (cur, row) => {
                    const extra = Math.max(...row.items.map(
                        val => Number(val.points),
                    ).filter(
                        item => !Number.isNaN(item),
                    ));
                    if (extra === -Infinity) {
                        return cur;
                    }
                    return cur + extra;
                },
                0,
            );
        },
    },

    methods: {
        getEmptyItem() {
            return {
                points: '',
                header: '',
                description: '',
            };
        },

        resetFixedMaxPoints() {
            this.internalFixedMaxPoints = null;
            this.submitMaxPoints();
        },

        focusOnRow(rowIndex) {
            if (this.editable && this.rubrics.length - 1 === rowIndex) {
                this.rubrics.push(this.getEmptyRow());
            }
            this.gotoItem(0);
            this.gotoItem(rowIndex);
        },

        getEmptyRow() {
            return {
                header: '',
                description: '',
                items: [this.getEmptyItem()],
            };
        },

        setRubricData(serverRubrics) {
            this.rubrics = serverRubrics.map((origRow) => {
                const row = Object.assign({}, origRow);

                // We slice here so we have a complete new object to sort.
                row.items = row.items.slice().sort((a, b) => a.points - b.points);

                if (this.editable) {
                    row.items.push(this.getEmptyItem());
                }

                return row;
            });

            if (this.editable) {
                this.rubrics.push(this.getEmptyRow());
            }
        },

        getRubrics() {
            if (!this.assignmentId) return Promise.resolve();

            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}/rubrics/`,
            ).then(({ data: rubrics }) => {
                this.setRubricData(rubrics);
            }, () => {
                this.rubrics = [this.getEmptyRow()];
            });
        },

        createRow() {
            this.rubrics.push(this.getEmptyRow());
        },

        deleteRubric() {
            const success = () => {
                this.gotoItem(0);
                this.rubrics = [this.getEmptyRow()];
            };

            const req = this.$http.delete(`/api/v1/assignments/${this.assignmentId}/rubrics/`).then(() => {
                success();
            });

            this.$refs.deleteButton.submit(req.catch(({ response }) => {
                if (response.status === 404) {
                    success();
                } else {
                    throw response.data.message;
                }
            }));
        },

        checkFixedMaxPoints() {
            if (this.internalFixedMaxPoints === '' || this.internalFixedMaxPoints == null) {
                this.internalFixedMaxPoints = null;
            } else if (Number.isNaN(Number(this.internalFixedMaxPoints))) {
                return `The given max points "${this.internalFixedMaxPoints}" is not a number`;
            } else {
                this.internalFixedMaxPoints = Number(this.internalFixedMaxPoints);
            }

            return undefined;
        },

        submitMaxPoints() {
            const err = this.checkFixedMaxPoints();
            if (err) {
                this.$refs.maxPointsButton.fail(err);
                return;
            }

            const req = this.$http.put(
                `/api/v1/assignments/${this.assignmentId}/rubrics/`,
                {
                    max_points: this.internalFixedMaxPoints,
                },
            );
            this.$refs.maxPointsButton.submit(req.catch(({ response }) => {
                throw response.data.message;
            }));
        },

        submit() {
            const wrongCategories = [];
            const wrongItems = [];

            const rows = [];
            for (let i = 0, len = this.rubrics.length - 1; i < len; i += 1) {
                const row = this.rubrics[i];

                const res = {
                    header: row.header,
                    description: row.description,
                    items: [],
                };

                for (let j = 0, len2 = row.items.length - 1; j < len2; j += 1) {
                    if (Number.isNaN(parseFloat(row.items[j].points))) {
                        wrongItems.push(`'${row.header || '[No name]'} - ${row.items[j].header || '[No name]'}'`);
                    }
                    row.items[j].points = parseFloat(row.items[j].points);

                    res.items.push(row.items[j]);
                }
                if (res.items.length === 0) {
                    wrongCategories.push(row.header || '[No name]');
                }

                if (row.id !== undefined) res.id = row.id;

                rows.push(res);
            }

            if (wrongItems.length > 0) {
                const multiple = wrongItems.length > 2;
                this.$refs.submitButton.fail(`
For the following item${multiple ? 's have' : ' has'} please make sure points is
a number: ${arrayToSentence(wrongItems)}.`);
                return;
            }

            if (wrongCategories.length > 0) {
                const multiple = wrongCategories.length > 2;
                this.$refs.submitButton.fail(`
The following categor${multiple ? 'ies have' : 'y has'} a no items:
${arrayToSentence(wrongCategories)}.`);
                return;
            }

            const err = this.checkFixedMaxPoints();
            if (err) {
                this.$refs.maxPointsButton.fail(err);
                return;
            }

            const req = this.$http.put(
                `/api/v1/assignments/${this.assignmentId}/rubrics/`,
                {
                    rows,
                    max_points: this.internalFixedMaxPoints,
                },
            ).then(({ data }) => {
                this.setRubricData(data);
            });
            this.$refs.submitButton.submit(req.catch(({ response }) => {
                throw response.data.message;
            }));
        },

        gotoItem(i) {
            this.currentCategory = i;
            this.slide();
        },

        slide() {
            this.$refs.rubricContainer.style.transform =
                `translateX(-${100 * this.currentCategory}%)`;
        },

        addRubricRow() {
            this.$set(this.rubrics, this.rubrics.length, {
                header: '',
                description: '',
                items: [this.getEmptyItem()],
            });
        },

        addItem(i, j) {
            if (this.rubrics[i].items.length - 1 === j) {
                this.$set(this.rubrics[i].items, j + 1, this.getEmptyItem());
            }
        },

        deleteItem(i, j) {
            this.rubrics[i].items.splice(j, 1);
        },

        addRow(i) {
            if (this.rubrics.length - 1 === i) {
                this.rubrics.push(this.getEmptyRow());
            }
        },

        deleteRow(i, e) {
            this.rubrics.splice(i, 1);
            e.preventDefault();
            e.stopPropagation();
        },
    },

    components: {
        Icon,
        SubmitButton,
        Loader,
        DescriptionPopover,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.rubric-editor {
    margin-bottom: 0;

    .tab-container {
        .add-button {
            max-width: 5em;
            height: 100%;
        }
        b.row-header {
            padding: 0.5rem 0.75rem;
            display: block;
            cursor: pointer;
            font-size: 1.1rem;
            line-height: 1.25;
            .default-secondary-text-colors;
        }
        .card {
            &:nth-child(5n + 5), &:last-child {
                border-right: 0;
            }
            input {
                border-top: 0;
                border-radius: 0;
            }
            &:first-child input {
                border-left: 0;
            }
            &:last-child input {
                border-right: 0;
            }
        }
    }

    .card.rubric-item {
        border-bottom: 0;
        border-top: 0;
        padding: .5rem;
        &:last-child {
            border-right: 0;
        }
        border-left: 0;
        border-radius: 0;
    }

    .card:hover, .card.active {
        background: #e6e6e6;
        #app.dark & {
            background: darken(@color-primary, 2%);
            border-color: @color-primary-darkest !important;
            .rubric-item input, .rubric-item textarea {
                background: transparent;
            }
        }
    }

    .card.active, .card:hover .row-header {
        #app.dark & {
            background: @color-primary-darker;
            input {
                background: @color-primary-darker;
            }
        }
    }

    .rubric-items-container {
        border-bottom: 0;
    }

    .inner-container {
        display: flex;
        flex-direction: row;
        transition: transform 500ms;
        align-items: baseline;
    }

    .outer-container {
        overflow: hidden;
        padding: 0;
        border: 1px solid rgba(0, 0, 0, 0.125) !important;
        #app.dark & {
            border: 1px solid @color-primary-darker !important;
        }
        border-radius: 0.25em;
    }

    .rubric-header {
        #app.dark & {
            background-color: darken(@color-primary, 1%);
            textarea {
                background-color: transparent;
            }
        }
        padding: 0 !important;
        p {
            font-size: 1.1rem;
            line-height: 1.25;
            .default-secondary-text-colors;
            min-height: 2em;
        }
        textarea, p {
            padding: 1rem .75rem;
            border-radius: 0;
            border: 0;
            margin: 0;
        }
        border-bottom: 0;
        input:focus {
            background: #f7f7f9;
        }
    }

    .card, card-header {
        border-radius: 0;
        &:not(.tab) {
            border-bottom: 0 !important;
            border-right: 0 !important;
        }
        border-top: 0 !important;
        border-left: 0 !important;
    }

    .rubric {
        flex: 1 1 0;
        min-width: 100%;
    }

    .rubric-editor {
        .card-header,
        .card-block {
            padding: .5rem .75rem;
            .rubric-item-wrapper {
                margin: -0.5em;
                padding: 0.5em;
                align-items: center;
            }
        }
    }

    .inner-container,
    .tab-container {
        input,
        textarea {
            cursor: pointer;
            &:disabled {
                cursor: default;
            }
            background: transparent;

            border: 1px solid transparent !important;

            &:hover:not(:disabled) {
                border: 1px solid @color-primary-darkest !important;
            }
            &:focus:not(:disabled) {
                border-color: #5cb3fd !important;
                cursor: text;
            }

            &.row-header,
            &.row-description {
                width: 100%;
            }

            &.row-header {
                font-weight: bold;
            }

            &.item-points {
                font-weight: bold;
                max-width: 25%;
                text-align: left;
                float: left;
                margin-right: .2rem;
            }

            &.item-points,
            &.item-header,
            &.item-description {
                padding: .375rem .1rem;
            }

            &.item-header {
                font-weight: bold;
                text-align: left;
                margin-left: 0.1rem;
                float: left;
            }
        }
    }

    .item-delete-button,
    .row-delete-button,
    .row-info-button,
    .item-info-button {
        color: #989898;
        position: absolute;
        top: .7rem;
        right: .7rem;
        z-index: 100;
        padding: 0 0.5rem;
    }
    .row-delete-button, .row-info-button {
        top: 0;
        right: 0;
        margin: 0.4rem;
    }
    .item-delete-button:hover,
    .row-delete-button:hover {
        .default-text-colors;
        cursor: pointer;
    }
    .item-info-button:hover,
    .row-info-button:hover {
        .default-text-colors;
        cursor: help;
    }

    .card.button-bar,
    .card.extra-bar {
        border-top: 0;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
        background: #f7f7f9;
        .card-body {
            justify-content: space-between;
            display: flex;
            flex-direction: row;
            align-items: center;
        }
    }
    .card.button-bar {
        .override-checkbox {
            justify-content: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        input {
            width: 5em;
        }
    }
    .card.extra-bar {
        padding: 1em;
    }
}


.card-body {
    padding: 0;
}
</style>

<style lang="less">
.rubric-editor {
    .tab-container > .submission-popover > span {
        display: block;
        height: 100%;
        > button {
            height: 100%;
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }

    }

    .tab-container > .card > .card-block {
        padding: 0;
    }

    .rubric-items-container .card.rubric-item > .card-block {
        border: 0;
    }

    .card.button-bar .submit-button {
        &:not(.round) .btn {
            border-top-left-radius: 0;
            border-top-right-radius: 0;
        }
        &:last-child:not(.round) .btn {
            border-bottom-left-radius: 0;
        }
        &:first-child:not(.round) .btn {
            border-bottom-right-radius: 0;
        }
    }
}
</style>
