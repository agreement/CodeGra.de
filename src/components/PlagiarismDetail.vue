<template>
<loader v-if="this.assignment == null || this.detail == null"/>
<div class="plagiarism-detail" v-else>
    <local-header :title="`Plagiarism comparison for assignment &quot;${assignment.name}&quot;`">
        <!-- <icon name="arrow-left" -->
        <!--       scale="2" -->
        <!--       @click="$emit('close-detail')"/> -->
    </local-header>

    <table class="range-table table table-striped table-hover">
        <thead>
            <tr>
                <th class="col-student-name">{{ detail.student_1.name }}</th>
                <th class="col-student-range">Lines</th>
                <th class="col-student-name">{{ detail.student_2.name }}</th>
                <th class="col-student-range">Lines</th>
            </tr>
        </thead>

        <tbody>
            <tr v-for="range in sortedRanges"
                @click="gotoRange(range)">
                <td class="col-student-name">{{ range.self.file_name }}</td>
                <td class="col-student-range">{{ range.self.range[0] + 1 }} - {{ range.self.range[1] + 1 }}</td>
                <td class="col-student-name">{{ range.other.file_name }}</td>
                <td class="col-student-range">{{ range.other.range[0] + 1 }} - {{ range.other.range[1] + 1 }}</td>
            </tr>
        </tbody>
    </table>

    <div class="code-viewer form-control"
            v-if="contentLoaded">
        <div class="student-files"
                v-for="key in ['self', 'other']"
                :ref="`file-comparison-${key}`">
            <b-card class="student-file"
                    v-for="file in filesPerStudent[key]"
                    :key="`file-comparison-${key}-${file.file_name}`"
                    :header="file.file_name"
                    :ref="`file-comparison-${key}-${file.file_name}`">
                <router-link slot="header"
                             :to="fileRoute(file)">
                             {{ file.file_name }}
                </router-link>
                <ol class="form-control"
                    :style="{
                        paddingLeft: `${3 + Math.log10(file.content.length) * 2/3}em`,
                        fontSize: `${fontSize}px`,
                    }">
                    <li v-for="line in file.content">
                        <code v-html="line"/>
                    </li>
                </ol>
            </b-card>
        </div>
    </div>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/arrow-left';

import { Loader, LocalHeader } from '@/components';

export default {
    name: 'plagiarism-detail',

    data() {
        return {
            detail: {
                student_1: {
                    user_id: 0,
                    name: 'Student1',
                    submission_id: 1,
                },
                student_2: {
                    user_id: 1,
                    name: 'Student2',
                    submission_id: 2,
                },
                average: 25,
                maximum: 50,
                files: [
                    {
                        self: {
                            file_id: 51,
                            file_name: 'file.py',
                            lines: [[0, 20], [40, 50]],
                        },
                        other: {
                            file_id: 59,
                            file_name: 'bestandje.py',
                            lines: [[5, 25], [80, 90]],
                        },
                    },
                    {
                        self: {
                            file_id: 48,
                            file_name: 'wow.py',
                            lines: [[5, 15]],
                        },
                        other: {
                            file_id: 43,
                            file_name: 'dir/wowsers.py',
                            lines: [[10, 15]],
                        },
                    },
                ],
            },
            contentLoaded: false,
        };
    },

    computed: {
        ...mapGetters('pref', ['fontSize']),

        ...mapGetters('courses', ['assignments']),

        assignmentId() {
            return this.$route.params.assignmentId;
        },

        assignment() {
            return this.assignments[this.assignmentId];
        },

        userIds() {
            return [
                this.$route.params.userId1,
                this.$route.params.userId2,
            ];
        },

        sortedFiles() {
            return this.detail.files.sort((a, b) => b.match - a.match);
        },

        filesPerStudent() {
            const self = [];
            const other = [];

            this.sortedFiles.forEach((file) => {
                self.push(file.self);
                other.push(file.other);
            });

            return { self, other };
        },

        sortedRanges() {
            return this.sortedFiles.reduce(
                (ranges, file) => ranges.concat(file.self.lines.map(
                    (range, i) => ({
                        self: {
                            file_name: file.self.file_name,
                            range,
                        },
                        other: {
                            file_name: file.other.file_name,
                            range: file.other.lines[i],
                        },
                        match: file.match,
                    }),
                )),
                [],
            );
        },
    },

    watch: {
        detail(detail) {
            const { files } = detail;

            for (let i = 0; i < files.length; i++) {
                files[i].self.submission_id = detail.student_1.submission_id;
                files[i].other.submission_id = detail.student_2.submission_id;
            }

            this.getFileContents();
        },
    },

    methods: {
        ...mapActions('courses', ['loadCourses']),

        closeDetailView() {
            this.detail = null;
        },

        getFileContents() {
            this.contentLoaded = false;

            Promise.all(this.sortedFiles.map(async (file) => {
                const [self, other] = await Promise.all([
                    this.$http.get(`/api/v1/code/${file.self.file_id}`),
                    this.$http.get(`/api/v1/code/${file.other.file_id}`),
                ]);

                file.self.content = this.highlightLines(self.data.split('\n'), file.self.lines);
                file.other.content = this.highlightLines(other.data.split('\n'), file.other.lines);
            })).then(() => {
                this.contentLoaded = true;
            });
        },

        highlightLines(lines, ranges) {
            const colors = [
                [255, 0, 0],
                [0, 0, 255],
                [255, 0, 255],
            ];

            let colorIndex = 0;

            ranges.forEach((range) => {
                for (let i = range[0]; i <= range[1]; i++) {
                    lines[i] = `<span style="color: rgb(${colors[colorIndex]}); background: rgba(${colors[colorIndex]}, .1);">${lines[i]}</span>`;
                }
                colorIndex = (colorIndex + 1) % colors.length;
            });

            return lines;
        },

        fileRoute(file) {
            return {
                name: 'submission_file',
                params: {
                    courseId: this.$route.params.courseId,
                    assignmentId: this.$route.params.assignmentId,
                    submissionId: file.submission_id,
                    fileId: file.file_id,
                },
            };
        },

        gotoRange(range) {
            this.gotoRangeInTarget(range, 'self');
            this.gotoRangeInTarget(range, 'other');
        },

        // target must be 'self' or 'other'.
        gotoRangeInTarget(range, target) {
            const ref = `file-comparison-${target}`;
            const container = this.$refs[ref][0];
            const codeViewer = this.$refs[`${ref}-${range[target].file_name}`][0];

            const containerOffset = codeViewer.offsetTop - container.offsetTop;

            const line = range[target].range[0];
            let lineOffset = 0;

            if (line > 0) {
                lineOffset = container.querySelectorAll('li')[line - 1].offsetTop;
            }

            container.scrollTo({ top: containerOffset + lineOffset });
        },
    },

    async mounted() {
        await this.loadCourses();

        this.detail = { ...this.detail };

        // this.detail = await this.$http.get(
        //     `/api/v1/assignments/${this.assignmentId}/plagiarism/
        // ?user_ids=${this.userIds.join(',')}`,
        // );

        this.getFileContents();
    },

    components: {
        Icon,
        Loader,
        LocalHeader,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.plagiarism-detail {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin-bottom: 0 !important;
}

.local-header {
    flex: 0 0 auto;
}

.range-table {
    flex: 1 1 auto;
    margin-bottom: .75rem;

    .col-student-name,
    .col-student-name {
        width: 50%;
    }

    .col-student-range,
    .col-student-range {
        width: 1px;
        white-space: nowrap;
        text-align: center;
    }

    th,
    td {
        padding-top: .25rem;
        padding-bottom: .25rem;
    }
}

.code-viewer {
    flex: 4 4 auto;
}

.code-viewer {
    display: flex;
    flex-direction: row;
    padding: 0;
    margin-bottom: 1rem;
}

.student-files {
    flex: 0 0 50%;
    max-height: 100vh;
    overflow: auto;
}

.student-file {
    margin-top: 0 !important;
    border-left: 0;
    border-right: 0;
    border-top: 0;

    &:last-child {
        border-bottom: 0;
    }

    &:not(:first-child) {
        margin-top: -1px;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }

    &:not(:last-child) {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }

    .student-files:not(:first-child) & {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }

    .student-files:not(:last-child) & {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }
}

ol {
    min-height: 5em;
    margin: 0;
    padding-top: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 0 !important;
    background: @linum-bg;
    font-family: monospace;
    font-size: small;

    #app.dark & {
        background: @color-primary-darkest;
        color: @color-secondary-text-lighter;
    }

    &:not(:last-child) {
        border-right: 1px solid @color-light-gray;
    }
}

li {
    position: relative;
    padding-left: .75em;
    padding-right: .75em;

    background-color: lighten(@linum-bg, 1%);
    border-left: 1px solid darken(@linum-bg, 5%);

    #app.dark & {
        background: @color-primary-darker;
        border-left: 1px solid darken(@color-primary-darkest, 5%);
    }
}

code {
    border-bottom: 1px solid transparent;
    color: @color-secondary-text;
    white-space: pre-wrap;

    word-wrap: break-word;
    word-break: break-word;
    -ms-word-break: break-all;

    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    -ms-hyphens: auto;
    hyphens: auto;

    #app.dark & {
        color: #839496;
    }
}
</style>
