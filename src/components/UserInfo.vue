<template>
    <div id="userinfo">
        {{ username }}

    </div>
</template>

<script>
export default {
    name: 'hello',
    data() {
        return {
            name: '',
            email: '',
        };
    },

    mounted() {
        this.$http.get(`/api/v1/login`).then((data) => {
            this.name = data.body.name;
            this.email = data.body.email;
        });
    },


};
</script>
