<template>
    <div id="app">
        <header-bar></header-bar>
        <main>
            <side-bar></side-bar>
            <router-view></router-view>
        </main>
    </div>
</template>

<script>
import { HeaderBar, SideBar } from '@/components';

export default {
    name: 'app',

    components: {
        HeaderBar,
        SideBar,
    },
};
</script>

<style lang="less">
@sidebar-width: 10em;

#app {
    box-sizing: border-box;
}

* {
    box-sizing: inherit;
}

main {
    display: flex;
}

.side-bar {
    flex: 0 0 @sidebar-width;
}

.page {
    flex-grow: 1;
    flex-shrink: 1;
}
</style>
