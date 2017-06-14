<template>
    <header>
        <router-link :to="{ name: 'home', }">
            <img class="logo" src="/static/img/codegrade.png">
        </router-link>
    </header>
</template>

<script>
export default {
    name: 'header-bar',
};
</script>
