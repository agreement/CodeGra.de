import localforage from 'localforage';

export default class PermissionStore {
    constructor(axios, config, maxAge = 1000 * 60 * 60 * 24) {
        this.store = localforage.createInstance(
            Object.assign({}, config, {
                name: 'permissions',
            }),
        );
        this.onGoingRequests = {};
        this.maxAge = maxAge;
        this.http = axios;
    }

    static getCacheKey(courseId) {
        return `${courseId || 'GLOBAL_PERMS'}`;
    }

    clearCache() {
        this.onGoingRequests = {};
        return this.store.clear();
    }

    async hasPermission(permission, courseId, asMap) {
        function wrapArray(val) {
            if (asMap) {
                return Object.values(val);
            } else if (val instanceof Array) {
                return val;
            } else {
                return [val];
            }
        }
        function getValues(permsGetter) {
            if (typeof permission === 'string') {
                return permsGetter(permission);
            } else if (asMap) {
                return permission.reduce((res, val) => {
                    res[val] = permsGetter(val);
                    return res;
                }, {});
            } else {
                return permission.map(permsGetter);
            }
        }


        const cacheKey = PermissionStore.getCacheKey(courseId);
        const cached = await this.store.getItem(cacheKey);
        if (cached != null) {
            const { map, expiration } = cached;
            const res = getValues(val => map[val]);

            if (Date.now() < expiration &&
                wrapArray(res).every(i => i != null)
            ) {
                return res;
            }
        }

        let cont = this.onGoingRequests[cacheKey];

        if (cont == null) {
            if (courseId == null) {
                cont = this.http.get('/api/v1/permissions/', {
                    params: { type: 'global' },
                });
            } else {
                cont = this.http.get(`/api/v1/courses/${courseId}/permissions/`);
            }

            this.onGoingRequests[cacheKey] = cont;
        }

        try {
            const { data } = await cont;
            const res = getValues(val => data[val]);

            // Only delete the request if the data has been saved.
            const cacheData = {
                map: data,
                expiration: Date.now() + this.maxAge,
            };
            this.store.setItem(cacheKey, cacheData).then(() => {
                delete this.onGoingRequests[cacheKey];
            });
            return res;
        } catch (_) {
            delete this.onGoingRequests[cacheKey];
            throw Error(getValues(() => false));
        }
    }
}
