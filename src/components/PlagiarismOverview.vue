<template>
<loader v-if="this.assignment == null || this.overview == null"/>
<div class="plagiarism-overview" v-else>
    <local-header :title="`Plagiarism overview for assignment &quot;${assignment.name}&quot;`">
        <input v-model="filter"
                class="form-control"/>
    </local-header>

    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th class="col-student-1-name">Student 1</th>
                <th class="col-student-2-name">Student 2</th>
                <th class="col-average" v-if="hasAvg">Average similarity</th>
                <th class="col-maximum" v-if="hasMax">Maximum similarity</th>
            </tr>
        </thead>

        <tbody>
            <tr v-for="pair in filteredEntries"
                @click="showDetailView(pair.student_1.user_id, pair.student_2.user_id)">
                <td class="col-student-1-name">{{ pair.student_1.name }}</td>
                <td class="col-student-2-name">{{ pair.student_2.name }}</td>
                <td class="col-average" v-if="hasAvg">{{ pair.average }}</td>
                <td class="col-maximum" v-if="hasMax">{{ pair.maximum }}</td>
            </tr>
        </tbody>
    </table>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import { Loader, LocalHeader } from '@/components';

export default {
    name: 'plagiarism-overview',

    data() {
        return {
            overview: [
                {
                    student_1: {
                        user_id: 0,
                        name: 'Student1',
                    },
                    student_2: {
                        user_id: 1,
                        name: 'Student2',
                    },
                    average: 25,
                    maximum: 50,
                    files: [
                        {
                            self: 'file.py',
                            other: 'bestandje.py',
                            match: 50,
                        },
                        {
                            self: 'wow.py',
                            other: 'dir/wowsers.py',
                            match: 10,
                        },
                    ],
                },
                {
                    student_1: {
                        user_id: 0,
                        name: 'Student1',
                    },
                    student_2: {
                        user_id: 2,
                        name: 'Student3',
                    },
                    average: 5,
                    maximum: 100,
                    files: [
                        {
                            self: 'wow.py',
                            other: 'dir2/wowsers.py',
                            match: 100,
                        },
                    ],
                },
            ],
            sortKey: 'average',
            filter: '',
        };
    },

    computed: {
        ...mapGetters('courses', ['assignments']),

        assignmentId() {
            return this.$route.params.assignmentId;
        },

        assignment() {
            return this.assignments[this.assignmentId];
        },

        hasAvg() {
            return this.overview.some(pair => pair.average != null);
        },

        hasMax() {
            return this.overview.some(pair => pair.maximum != null);
        },

        sortedEntries() {
            return this.overview.sort((a, b) => a[this.sortKey] - b[this.sortKey]);
        },

        filteredEntries() {
            return this.sortedEntries.filter(entry =>
                entry.student_1.name.match(this.filter) || entry.student_2.name.match(this.filter));
        },
    },

    methods: {
        ...mapActions('courses', ['loadCourses']),

        showDetailView(userId1, userId2) {
            console.log(Object.assign({}, this.$route, {
                params: Object.assign(this.$route.params, {
                    userId1,
                    userId2,
                }),
            }));
            this.$router.push({
                name: 'plagiarism_detail',
                params: Object.assign(this.$route.params, {
                    userId1,
                    userId2,
                }),
            });
        },
    },

    async mounted() {
        await this.loadCourses();

        // this.overview = await this.$http.get(`/api/v1/assignment/
        // ${this.assignmentId}/plagiarism/`);
    },

    components: {
        LocalHeader,
        Loader,
    },
};
</script>

<style lang="less">
.col-average,
.col-maximum {
    width: 1px;
    white-space: nowrap;
    text-align: center;
}
</style>
