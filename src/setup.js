import Vue from 'vue';
import axios from 'axios';

let toastVisible = false;
axios.interceptors.response.use(response => response, (error) => {
    if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx

        if (error.status === 500) {
            if (!toastVisible) {
                toastVisible = true;
                Vue.toasted.error('Internal server error encountered', {
                    position: 'bottom-center',
                    duration: 3000,
                    onComplete: () => {
                        toastVisible = false;
                    },
                });
            }
        }

        return Promise.reject(error);
    }

    if (error.request) {
        // The request was made but no response was received
        // `error.request` is an instance of XMLHttpRequest in the browser and an instance of
        // http.ClientRequest in node.js
        if (!toastVisible) {
            toastVisible = true;
            Vue.toasted.error('There was an error connecting to the server... Please try again later', {
                position: 'bottom-center',
                duration: 3000,
                onComplete: () => {
                    toastVisible = false;
                },
            });
        }
        return Promise.reject(error);
    }
    // Something happened in setting up the request that triggered an Error

    // eslint-disable-next-line
    console.error('Error while setting up request', error);
    return Promise.reject(error);
});
