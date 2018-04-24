<template>
<loader class="rubric-editor" v-if="loading"/>
<div v-else class="rubric-editor" :class="{ editable }">
    <b-tabs no-fade
            v-model="currentCategory">
        <b-nav-item slot="tabs" @click.prevent="appendRow" href="#"
                    v-if="editable">
            +
        </b-nav-item>

        <b-tab class="rubric"
               v-for="(rubric, i) in rubrics"
               :title="rubricCategoryTitle(rubric)"
               :key="`rubric-${rubric.id}-${i}`">

            <b-card no-block>
                <div class="card-header rubric-header">
                    <b-input-group style="margin-bottom: 1em;"
                                   v-if="editable">
                        <b-input-group-prepend is-text>
                            Category name
                        </b-input-group-prepend>
                        <input class="form-control"
                               placeholder="Category name"
                               v-model="rubric.header"/>
                        <b-input-group-append>
                            <b-btn size="sm" variant="danger" class="float-right" @click="(e)=>deleteRow(i, e)">
                                Remove category
                            </b-btn>
                        </b-input-group-append>
                    </b-input-group>
                    <textarea class="form-control"
                              placeholder="Category description"
                              :tabindex="currentCategory === i ? null: -1"
                              v-model="rubric.description"
                              v-if="editable"/>
                    <p v-else>{{ rubric.description }}</p>
                </div>
                <b-card-group class="rubric-items-container">
                    <b-card class="rubric-item"
                            v-for="(item, j) in rubric.items"
                            :key="`rubric-item-${item.id}-${j}-${i}`">
                        <b-input-group class="item-header-row">
                            <input v-if="editable"
                                   type="number"
                                   class="form-control item-points"
                                   step="any"
                                   :tabindex="currentCategory === i ? null: -1"
                                   placeholder="Points"
                                   @change="item.points = parseFloat(item.points)"
                                   @keydown.native="editable && addItem(i, j)"
                                   @keydown.native.ctrl.enter="editable && submit()"
                                   v-model="item.points"/>
                            <span v-else
                                  class="item-points input disabled">
                                {{ item.points }}
                            </span>
                            <input type="text"
                                   v-if="editable"
                                   class="form-control item-header"
                                   placeholder="Header"
                                   :tabindex="currentCategory === i ? null: -1"
                                   @keydown="editable && addItem(i, j)"
                                   @keydown.ctrl.enter="editable && submit()"
                                   v-model="item.header"/>
                            <span v-else class="input item-header disabled">
                                {{ item.header }}
                            </span>
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
                        </b-input-group>
                        <textarea v-model="item.description"
                                  class="item-description form-control"
                                  v-if="editable"
                                  :rows="8"
                                  :tabindex="currentCategory === i ? null: -1"
                                  @keydown="editable && addItem(i, j)"
                                  @keydown.ctrl.enter="editable && submit()"
                                  placeholder="Description"/>
                        <p v-else
                           class="form-control input item-description disabled">
                            {{ item.description }}
                        </p>
                    </b-card>
                </b-card-group>
            </b-card>
        </b-tab>

        <div slot="empty" class="text-center text-muted empty" v-if="editable">
            This assignment does not have rubric yet. Click the '+' to add a category.
        </div>
    </b-tabs>

    <b-modal id="modal_delete_rubric" title="Are you sure?" :hide-footer="true">
        <p style="text-align: center;">
            By deleting a rubric the rubric and all grades given with it will be
            lost forever! So are you really sure?
        </p>
        <b-button-toolbar justify>
            <submit-button default="outline-danger"
                           label="Yes"
                           ref="deleteButton"
                           @click="deleteRubric"/>
            <b-btn class="text-center"
                   variant="success"
                   @click="$root.$emit('bv::hide::modal', 'modal_delete_rubric')">
                No!
            </b-btn>
        </b-button-toolbar>
    </b-modal>

    <b-card class="button-bar" v-if="editable">
        <b-button-group class="danger-buttons">
            <submit-button default="danger"
                           show-inline
                           :label="false"
                           v-b-popover.top.hover="'Delete rubric'"
                           @click="$root.$emit('bv::show::modal','modal_delete_rubric')">
                <icon name="times"/>
            </submit-button>
            <submit-button show-inline
                           class="reset-button"
                           default="danger"
                           :label="false"
                           ref="resetButton"
                           @click="resetRubric"
                           v-b-popover.top.hover="'Reset rubric'">
                <icon name="reply"/>
        </submit-button>
        </b-button-group>
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
                                   v-b-popover.top.hover="internalFixedMaxPoints == null ? '' : 'Reset to the default value.'"
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
import { waitAtLeast } from '../utils';

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
            this.getAndSetRubrics();
        },
    },

    mounted() {
        if (this.defaultRubric) {
            this.setRubricData(this.defaultRubric);
            this.loading = false;
        } else {
            this.getAndSetRubrics().then(() => {
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

        getEmptyRow() {
            return {
                header: '',
                description: '',
                items: [this.getEmptyItem()],
            };
        },

        resetRubric() {
            const btn = this.$refs.resetButton;
            this.loading = true;
            btn.submit(this.getAndSetRubrics().then(() => {
                this.loading = false;
            }));
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
        },

        getAndSetRubrics() {
            if (!this.assignmentId) return Promise.resolve();

            return this.$http.get(
                `/api/v1/assignments/${this.assignmentId}/rubrics/`,
            ).then(({ data: rubrics }) => {
                this.setRubricData(rubrics);
            }, () => {
                this.rubrics = [];
            });
        },

        createRow() {
            this.rubrics.push(this.getEmptyRow());
        },

        deleteRubric() {
            const success = () => {
                this.rubrics = [];
                setTimeout(() => {
                    this.$root.$emit('bv::hide::modal', 'modal_delete_rubric');
                }, 1000);
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

        getCheckedRubricRows() {
            const wrongCategories = [];
            const wrongItems = [];
            let hasUnnamedCategories = false;

            const rows = [];
            for (let i = 0, len = this.rubrics.length; i < len; i += 1) {
                const row = this.rubrics[i];

                const res = {
                    header: row.header,
                    description: row.description,
                    items: [],
                };

                if (res.header.length === 0) {
                    hasUnnamedCategories = true;
                }

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

            if (hasUnnamedCategories) {
                this.$refs.submitButton.fail('There are unnamed categories!');
                return undefined;
            }

            if (wrongItems.length > 0) {
                const multiple = wrongItems.length > 2;
                this.$refs.submitButton.fail(`
For the following item${multiple ? 's' : ''} please make sure "points" is
a number: ${arrayToSentence(wrongItems)}.`);
                return undefined;
            }

            if (wrongCategories.length > 0) {
                const multiple = wrongCategories.length > 2;
                this.$refs.submitButton.fail(`
The following categor${multiple ? 'ies have' : 'y has'} a no items:
${arrayToSentence(wrongCategories)}.`);
                return undefined;
            }

            if (rows.length === 0) {
                this.$refs.submitButton.fail(
                    'You cannot submit an empty rubric.',
                );
                return undefined;
            }

            return rows;
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

            this.$refs.maxPointsButton.submit(waitAtLeast(500, req).catch(({ response }) => {
                throw response.data.message;
            }));
        },

        submit() {
            const rows = this.getCheckedRubricRows();

            const err = this.checkFixedMaxPoints();
            if (err) {
                this.$refs.maxPointsButton.fail(err);
                return;
            }

            if (rows == null) {
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

        appendRow() {
            this.rubrics.push(this.getEmptyRow());
            this.$nextTick(() => {
                this.currentCategory = this.rubrics.length - 1;
            });
        },

        deleteRow(i, e) {
            this.rubrics.splice(i, 1);
            e.preventDefault();
            e.stopPropagation();
        },

        rubricCategoryTitle(category) {
            return category.header || '<span class="unnamed">Unnamed category</span>';
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

@rubric-items-per-row: 4;
@rubric-items-fixed-offset: @rubric-items-per-row + 1;
@rubric-item-min-width: 100% / @rubric-items-per-row;

.rubric-editor {
    margin-bottom: 0;

    .card.rubric-item {
        min-width: @rubric-item-min-width;
        padding: .5rem;
        border-bottom: 0;
        border-top: 0;
        border-left: 0;
        border-radius: 0;

        &:nth-child(n + @{rubric-items-fixed-offset}) {
            flex: 0 0 @rubric-item-min-width;
        }

        &:last-child {
            border-right: 0;
        }
    }

    .rubric-items-container {
        border-bottom: 0;
    }

    .rubric-header {
        padding: 0 !important;
        margin-bottom: 1em;
        .default-background;
        p {
            font-size: 1.1rem;
            line-height: 1.25;
            .default-text-colors;
            min-height: 2em;
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

    .rubric {
        padding: 1em;
        border: 1px solid transparent !important;

        .item-description {
            background-color: @color-lightest-gray;
        }

        .input.disabled {
            #app.dark & {
                color: @text-color-dark !important;
            }

            &.item-description {
                height: 10em;
            }
        }

        .rubric-items-container input,
        .rubric-items-container span.input {
            font-weight: bold;
            background: transparent;

            border: 1px solid transparent !important;
            margin-bottom: .2em;

            &:hover:not(.disabled) {
                border-bottom: 1px solid @color-primary-darkest !important;
            }

            &:focus:not(.disabled) {
                border-color: #5cb3fd !important;
                cursor: text;
            }

            &.item-points,
            &.item-header {
                min-width: 0;
                padding: .375rem .1rem;
            }

            &.item-points {
                flex: 0 0 4rem;
                margin-right: .2rem;
                text-align: left;

                &:not(:focus) {
                    border-radius: 0;
                }

                &.disabled {
                    flex-basis: auto;
                    padding-left: 10px;
                }
            }

            &.item-header {
                flex: 1 1 auto;
                margin-left: 0.1rem;

                &:focus {
                    border-top-right-radius: 0.25rem;
                    border-bottom-right-radius: 0.25rem;
                }
            }
        }
    }

    .item-delete-button,
    .item-info-button {
        color: @color-border-gray;
        padding: 0.5rem;
    }

    .item-delete-button:hover {
        .default-text-colors;
        cursor: pointer;
    }

    .item-info-button:hover {
        .default-text-colors;
        cursor: help;
    }

}

.empty {
    padding: 2em;
}

.button-bar,
.card.extra-bar {
    border: 0;
    .card-body {
        justify-content: space-between;
        display: flex;
        flex-direction: row;
        align-items: center;
    }
}
.button-bar {
    margin-top: 2em;
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

.card-body {
    padding: 0;
}

.danger-buttons {
    .btn {
        width: 50%;
    }
    .btn:first-child {
        border-right: 1px solid white;
    }
    .btn:last-child {
        border-left: 1px solid white;
    }
    #app.dark & .btn {
        border-color: @color-primary;
    }
}
</style>

<style lang="less">
@import "~mixins.less";

.rubric-editor {
    &:not(.editable) {
        .nav-tabs {
            background: @color-lighter-gray;
            padding-top: 15px;
            .nav-item:first-child {
                margin-left: 15px;
            }
            .nav-link:hover {
                border-color: @color-light-gray;
            }
        }
    }
    .rubric-items-container .card.rubric-item > .card-block {
        border: 0;
    }

    .nav-tabs {
        .nav-link {
            border-bottom: 0;

            .unnamed {
                color: @color-light-gray;
            }
        }
    }

    .tab-content {
        #app.dark & {
            border-color: @color-primary-darker;
        }
        border: 1px solid #dee2e6;
        border-top: 0;
        border-bottom-right-radius: 0.25rem;
        border-bottom-left-radius: 0.25rem;
    }
}
</style>
