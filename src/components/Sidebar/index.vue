<template>
<div class="sidebar" id="global-sidebar" :class="{ floating, inLTI: $inLTI }">
    <div class="main-menu" :class="{ show: mobileVisible }">
        <div class="sidebar-top">
            <router-link class="sidebar-top-item logo"
                         :to="{ name: 'home' }"
                         @click.native="closeSubMenu(true)">
                <img src="/static/img/logo.svg" v-if="showRegularLogo"/>
                <img src="/static/img/logo-inv.svg" v-else-if="showInvertedLogo"/>
                <img src="/static/img/codegrade.svg" v-else/>
            </router-link>

            <hr class="separator">

            <a v-for="entry in entries"
               v-if="maybeCall(entry.condition)"
               @click="openUpperSubMenu(entry, true)"
               class="sidebar-top-item"
               :class="{ selected: currentEntry && entry.name === currentEntry.name }">
                <icon :name="entry.icon"
                      :scale="mobileVisible ? 1.5 : 3"
                      :label="maybeCall(entry.title || entry.header)"/>
                <small class="name">
                    {{ maybeCall(entry.title || entry.header) }}
                </small>
            </a>
        </div>

        <div v-if="canManageSite">
            <hr class="separator"/>

            <div class="sidebar-bottom">
                <router-link :to="{ name: 'admin' }"
                class="sidebar-bottom-item"
                v-b-popover.hover.top="'Manage site'">
                    <icon name="tachometer"/>
                </router-link>
            </div>
        </div>

        <hr class="separator"/>

        <div class="sidebar-bottom">
            <a :href="`https://docs.codegra.de/?v=${version}`"
               target="_blank"
               class="sidebar-bottom-item"
               v-b-popover.hover.top="'Documentation'">
                <icon name="question"/>
            </a>

            <a href="#" @click="logout"
               class="sidebar-bottom-item"
               v-b-popover.hover.top="'Log out'"
               v-if="loggedIn && !$inLTI">
                <icon name="power-off"/>
            </a>
        </div>
    </div>

    <div class="submenu-container"
         :class="{ 'use-space': dimmingUseSpace, }"
         ref="subMenuContainer"
         v-if="subMenus.length">
        <div class="submenus">
            <div v-for="subMenu, i in subMenus"
                 class="submenu"
                 :id="`submenu-${i}`"
                 :style="subMenuStyle(subMenu)">
                <header>
                    <div class="action back-button"
                         v-b-popover.hover.bottom="i ? maybeCall(subMenus[i - 1].header) : 'Close submenu'"
                         @click="closeSubMenu()">
                        <icon :name="i ? 'arrow-left' : 'times'"/>
                    </div>

                    <h4 class="submenu-header">
                        {{ maybeCall(subMenu.header) }}
                    </h4>

                    <div v-if="subMenu.reload || loading"
                         @click="refreshItems"
                         class="action refresh-button"
                         v-b-popover.hover.bottom="'Refresh'">
                        <icon name="refresh"
                              :spin="loading"/>
                    </div>
                    <div v-else-if="loading"
                         class="action refresh-button"
                         v-b-popover.hover.bottom="'Refresh'">
                        <icon name="refresh"
                              spin/>
                    </div>
                </header>

                <hr class="separator"/>

                <component :is="subMenu.component"
                            v-show="!loading"
                            :data="maybeCall(subMenu.data)"
                            @loading="loading = true"
                            @loaded="loading = false"
                            @open-menu="openSubMenu"
                            @close-menu="closeSubMenu(true)"/>
            </div>
        </div>
    </div>

    <div class="page-overlay"
         v-if="dimPage"
         @click="closeSubMenu(true)"/>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/arrow-left';
import 'vue-awesome/icons/book';
import 'vue-awesome/icons/edit';
import 'vue-awesome/icons/graduation-cap';
import 'vue-awesome/icons/power-off';
import 'vue-awesome/icons/rocket';
import 'vue-awesome/icons/question';
import 'vue-awesome/icons/tachometer';
import 'vue-awesome/icons/refresh';

import { Loader } from '@/components';

import Login from './Login';
import UserInfo from './UserInfo';
import CourseList from './CourseList';
import AssignmentList from './AssignmentList';
import Register from './Register';

import { MANAGE_SITE_PERIMSSIONS } from '../../constants';


const floatingRoutes = new Set([
    'home',
    'submission',
    'submission_file',
]);
const hideRoutes = floatingRoutes;

Icon.register({
    'bolt-o': {
        width: 1792,
        height: 1792,
        raw: '<path d="m 1175.6954,707.84 q 11.52,12.8 4.48,28.16 l -345.60002,740.48 q -8.32,16 -26.88,16 -2.56,0 -8.96,-1.28 -10.88,-3.2 -16.32,-12.16 -5.44,-8.96 -2.88,-19.2 l 126.08,-517.12 -259.84,64.64 q -2.56,0.64 -7.68,0.64 -11.52,0 -19.84,-7.04 -11.52,-9.6 -8.32,-24.96 l 128.64,-528 q 2.56,-8.96 10.24,-14.72 7.68,-5.76 17.92,-5.76 h 209.92 q 12.16,0 20.48,8 8.32002,8 8.32002,18.88 0,5.12 -3.2,11.52 L 892.81538,762.24 1146.2554,699.52 q 5.12,-1.28 7.68,-1.28 12.16,0 21.76,9.6 z" style="stroke-width:0.63999999" /> <circle cx="896" cy="896" style="fill:none;stroke:#ffffff;stroke-width:150.50743103;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" r="800.24628" />',
    },
});

export default {
    name: 'sidebar',

    data() {
        return {
            loading: false,
            canManageSite: false,
            entries: [
                {
                    name: 'login',
                    icon: 'bolt-o',
                    iconStyle: 'border: 3px solid; border-radius: 50%;',
                    title: 'Login',
                    header: () => {
                        if (this.$route.hash === '#forgot') {
                            return 'Reset password';
                        } else {
                            return 'Login';
                        }
                    },
                    width: '600px',
                    component: 'login',
                    condition: () => !this.loggedIn,
                },
                {
                    name: 'register',
                    icon: 'rocket',
                    header: 'Register',
                    width: '600px',
                    component: 'register',
                    condition: () => !this.loggedIn,
                },
                {
                    name: 'user',
                    icon: 'graduation-cap',
                    title: () => this.name,
                    header: 'User',
                    width: '600px',
                    component: 'user-info',
                    condition: () => this.loggedIn,
                },
                {
                    name: 'courses',
                    icon: 'book',
                    header: 'Courses',
                    component: 'course-list',
                    condition: () => this.loggedIn && !this.$inLTI,
                    reload: true,
                },
                {
                    name: 'assignments',
                    icon: 'edit',
                    header: 'Assignments',
                    component: 'assignment-list',
                    condition: () => this.loggedIn && !this.$inLTI,
                    reload: true,
                },
                {
                    name: 'ltiAssignments',
                    icon: 'edit',
                    title: 'Assignments',
                    header: () => {
                        const { course } = this.assignments[this.$LTIAssignmentId];
                        return course ? course.name : 'Assignments';
                    },
                    component: 'assignment-list',
                    condition: () => {
                        if (this.loggedIn && this.$inLTI && this.$LTIAssignmentId) {
                            const { course } = this.assignments[this.$LTIAssignmentId];
                            if (course) {
                                return course.canManage ||
                                    course.assignments.some(a => a.canManage);
                            }
                        }
                        return false;
                    },
                    reload: true,
                    data: () => ({
                        course: this.assignments[this.$LTIAssignmentId].course,
                    }),
                },
            ],
            currentEntry: null,
            subMenus: [],
            mobileVisible: false,
            dimmingUseSpace: true,
            version: UserConfig.version,
        };
    },

    computed: {
        ...mapGetters('courses', ['assignments']),

        ...mapGetters('user', ['loggedIn', 'name']),

        floating() {
            return this.$inLTI ||
                !this.$root.$isMediumWindow ||
                this.mobileVisible ||
                floatingRoutes.has(this.$route.name);
        },

        dimPage() {
            // Make sure all properties are accessed so vue's caching works correctly.
            const isFloating = this.floating;
            const isMenuOpen = this.subMenus.length > 0 || this.mobileVisible;
            const customWidth = this.currentEntry && this.currentEntry.width;

            return !!((isFloating && isMenuOpen) || customWidth);
        },

        hideInitialEntries() {
            const route = this.$route.name;
            return this.$inLTI || !this.$root.$isMediumWindow || hideRoutes.has(route);
        },

        showRegularLogo() {
            return !(this.mobileVisible || (this.$inLTI && !this.$store.getters['pref/darkMode']));
        },

        showInvertedLogo() {
            return !this.mobileVisible && this.$inLTI && !this.$store.getters['pref/darkMode'];
        },
    },

    watch: {
        loggedIn(newVal) {
            if (newVal) {
                this.$hasPermission(MANAGE_SITE_PERIMSSIONS).then((perms) => {
                    this.canManageSite = perms.every(x => x);
                });
            } else {
                this.canManageSite = false;
            }
        },

        $route(newVal, oldVal) {
            if (newVal.name === oldVal.name) {
                return;
            }
            if (this.hideInitialEntries) {
                this.closeSubMenu(true);
            } else {
                this.setInitialEntry();
            }
        },
    },

    async mounted() {
        const [, perms] = await Promise.all([
            this.loadCourses(),
            this.$hasPermission(MANAGE_SITE_PERIMSSIONS),
        ]);

        this.canManageSite = perms.every(x => x);

        this.$root.$on('sidebar::show', () => {
            this.toggleMobileSidebar();
        });

        this.$on('sidebar::close', () => {
            if (this.floating || this.mobileVisible) {
                this.closeSubMenu(true);
            }
        });

        this.setInitialEntry();
    },

    methods: {
        ...mapActions('courses', ['loadCourses']),

        ...mapActions('user', {
            logoutUser: 'logout',
        }),

        logout() {
            this.logoutUser();
            this.closeSubMenu(true);
            this.$router.push({ name: 'home' });
        },

        refreshItems() {
            this.loading = true;
            this.$root.$emit('sidebar::reload');
        },

        findEntry(name) {
            return this.entries.find(entry => entry.name === name);
        },

        setInitialEntry() {
            if (this.$route.query.sbloc === 'm') {
                this.openMenuStack([this.findEntry('user')]);
            } else if (this.$route.query.sbloc === 'l' && !this.loggedIn) {
                this.openMenuStack([this.findEntry('login')]);
            } else if (this.$route.query.sbloc === 'r' && !this.loggedIn) {
                this.openMenuStack([this.findEntry('register')]);
            } else if (this.hideInitialEntries) {
                // NOOP
            } else if (this.$route.query.sbloc === 'a') {
                this.openMenuStack([this.findEntry('assignments')]);
            } else {
                const assignment = this.assignments[this.$route.params.assignmentId];
                const menuStack = [this.findEntry('courses')];
                if (assignment != null) {
                    menuStack.push({
                        header: assignment.course.name,
                        component: 'assignment-list',
                        data: assignment,
                        reload: true,
                    });
                }
                this.openMenuStack(menuStack);
            }
        },

        openMenuStack(stack) {
            if (stack.length === 0) {
                return;
            }

            this.openUpperSubMenu(stack[0]);

            const subMenus = stack.slice(1);
            for (let i = 0; i < subMenus.length; i++) {
                this.openSubMenu(subMenus[i]);
            }
        },

        openUpperSubMenu(entry, toggle = false) {
            if (toggle && this.currentEntry &&
                entry.name === this.currentEntry.name) {
                this.closeSubMenu(true);
            } else {
                const hadSubMenuOpen = this.subMenus.length > 0;

                this.currentEntry = entry;
                this.subMenus = [];
                this.openSubMenu(entry);

                this.dimmingUseSpace = (this.dimPage && hadSubMenuOpen) || !entry.width;
            }
        },

        openSubMenu(entry) {
            this.loading = false;
            this.subMenus.push(entry);
        },

        closeSubMenu(closeAll = false) {
            this.loading = false;

            this.$root.$emit('sidebar::submenu-closed');

            if (closeAll) {
                this.currentEntry = null;
                this.subMenus = [];
            } else {
                this.subMenus.pop();
            }

            if (this.subMenus.length === 0) {
                this.currentEntry = null;
            }

            if ((closeAll || this.subMenus.length === 0) && this.mobileVisible) {
                this.toggleMobileSidebar();
            }
        },

        toggleMobileSidebar() {
            this.mobileVisible = !this.mobileVisible;

            // Make document (un)scrollable
            if (this.mobileVisible) {
                document.body.style.height = '100%';
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.height = '';
                document.body.style.overflow = '';
            }
        },

        maybeCall(fun) {
            switch (typeof fun) {
            case 'function':
                return fun.bind(this)();
            default:
                return fun;
            }
        },

        subMenuStyle(subMenu) {
            const style = {};

            if (subMenu.width) {
                style.width = '100vw';
                style.maxWidth = subMenu.width;
            }

            return style;
        },
    },

    components: {
        Icon,
        Loader,
        Login,
        UserInfo,
        CourseList,
        AssignmentList,
        Register,
    },
};
</script>

<style lang="less" scoped>
@import "~mixins.less";

.sidebar {
    position: relative;
    position: sticky;
    z-index: 10;
    top: 0;
    height: 100vh;

    &:not(.floating) {
        display: flex;
        flex-direction: row;
    }

    a {
        text-decoration: none;
        color: inherit;
    }
}

.main-menu {
    display: flex;
    flex-direction: column;
    min-width: 6rem;
    height: 100%;

    color: white;
    background-color: @color-primary;
    @{lti-colors} & {
        background-color: white;
        color: @text-color;
    }

    box-shadow: 0 0 10px rgba(0, 0, 0, .5);

    @media @media-no-small {
        width: 6em;
    }

    @media @media-small {
        position: absolute;
        right: 100%;
        transform: none;

        &.show {
            transform: translateX(100%);
        }

        &:not(.show) {
            box-shadow: none;
        }
    }

    .sidebar-top {
        flex: 1 1 auto;
    }

    .sidebar-top-item {
        display: flex;
        flex-direction: column;
        padding: .75rem;

        @media @media-small {
            flex-direction: row;
            padding: .5rem;
        }

        &.logo {
            display: block;

            img {
                width: 100%;
            }
        }

        .fa-icon {
            @media @media-no-small {
                display: block;
                margin: 0 auto;
            }

            @media @media-small {
                margin-right: .5rem;
            }
        }

        .name {
            text-align: center;
        }
    }

    .sidebar-bottom {
        display: flex;
        flex-direction: row;
        flex: 0 0 auto;
    }

    .sidebar-bottom-item {
        flex: 1 1 auto;
        padding: .5rem .25rem .25rem;
        text-align: center;
    }
}

.submenu-container {
    z-index: -1;
    width: 16rem;
    height: 100%;

    @media @media-small {
        z-index: 1;
    }

    .sidebar.floating & {
        position: absolute;
        top: 0;
        left: 100%;
    }

    .sidebar:not(.floating) &:not(.use-space) {
        width: 0;
    }

    header {
        display: flex;
        flex: 0 0 auto;

        .action {
            display: flex;
            align-items: center;
            flex: 0 0 auto;
            padding: .5rem .75rem;
            cursor: pointer;
        }

        .submenu-header {
            flex: 1 1 auto;
            margin: 0;
            padding: .5rem 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    }

    .submenus {
        position: relative;
        height: 100%;
    }

    .submenu {
        display: flex;
        flex-direction: column;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;

        background-color: @color-primary;
        color: white;
        @{lti-colors} & {
            background-color: white;
            color: @color-primary;
        }

        &:first-child {
            box-shadow: 0 0 10px rgba(0, 0, 0, .75);
        }

        &:not(:last-child) {
            display: none;
        }
    }
}

.page-overlay {
    background-color: rgba(0, 0, 0, .33);
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: -2;
}
</style>

<style lang="less">
@import "~mixins.less";

.sidebar {
    & &-list-wrapper {
        display: flex;
        flex-direction: column;
        flex: 1 1 auto;
        max-height: 100%;
        margin: 0;
        padding: 0;
        overflow-y: hidden;
    }

    & &-footer {
        flex: 0 0 auto;
        display: flex;
        flex-direction: row;
    }

    & &-footer-button {
        flex: 1 1 auto;
        border: 0;
        border-radius: 0;

        background-color: transparent !important;
        color: @text-color-dark;

        &:hover {
            background-color: @color-primary-darker !important;

            @{lti-colors} & {
                background-color: @color-light-gray !important;
            }
        }

        @{lti-colors} & {
            color: @text-color;
        }

        &.active {
            background-color: white !important;
            color: @color-primary !important;

            @{lti-colors} & {
                background-color: @color-primary !important;
                color: white !important;
            }
        }
    }

    & &-list {
        list-style: none;
        margin: 0;
        padding: 0;
        flex: 1 1 auto;
        overflow-y: auto;

        .separator {
            margin: .5rem;
        }

        &.no-items-text {
            color: @color-light-gray;
            padding: 0 .75rem;
        }
    }

    & &-list-section-header {
        padding: 0 .75rem;
        color: @color-light-gray;
    }

    & &-list-item {
        display: flex;
        flex-direction: row;
    }

    & &-top-item,
    & &-bottom-item,
    & &-list-item {
        cursor: pointer;

        &:hover {
            background-color: lighten(@color-primary-darker, 2%);
            @{lti-colors} & {
                background-color: @color-lighter-gray;
            }
        }
        &:not(.light-selected) a:hover {
            background-color: @color-primary-darkest;
            @{lti-colors} & {
                background-color: @color-light-gray;
            }
        }

        &.light-selected {
            background-color: lightgray;
            color: @color-primary;
            @{lti-colors} & {
                background-color: lighten(@color-primary, 5%);
                color: white;
            }

            a:hover:not(.selected) {
                background-color: darken(lightgray, 7.9%);
                @{lti-colors} & {
                    background-color: @color-primary-darkest;
                }
            }
        }

        .selected,
        &.selected {
            background-color: white;
            color: @color-primary;
            @{lti-colors} & {
                color: white;
                background-color: @color-primary;
            }

            &:hover,
            a:hover {
                background-color: darken(white, 7.9%);
                color: @color-primary;
                @{lti-colors} & {
                    background-color: darken(@color-primary, 2%);
                    color: white;
                }
            }
        }
    }

    & &-item {
        padding: .5rem .75rem;
    }

    & &-filter {
        margin: .5rem;
    }

    hr.separator {
        margin: 0 .5rem;
        border-top: 1px solid @color-primary-darkest;
    }

    .submenu hr.separator {
        position: relative;
        z-index: 100;
    }
}
</style>
