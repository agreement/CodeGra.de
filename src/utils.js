import moment from 'moment';

export function formatGrade(grade) {
    const g = parseFloat(grade);
    return Number.isNaN(g) ? null : g.toFixed(2);
}

export function filterSubmissions(
    submissions,
    latest,
    mine,
    userId,
    filter,
    callback = () => false,
) {
    const l = new Set();
    const filterAssignee = submissions.some(s => s.assignee &&
                                            s.assignee.id === userId);

    return submissions.filter((item) => {
        if ((latest && l.has(item.user.id)) ||
            (filterAssignee && mine &&
             (item.assignee == null || item.assignee.id !== userId))) {
            return callback(item);
        } else if (!filter) {
            l.add(item.user.id);
            return true;
        }

        const terms = {
            user_name: item.user.name.toLowerCase(),
            grade: (item.grade || 0).toString(),
            created_at: item.created_at,
            assignee: item.assignee ? item.assignee.name.toLowerCase() : '-',
        };
        const out = filter
            .toLowerCase()
            .split(' ')
            .every(word => Object.keys(terms)
                   .some(key => terms[key].indexOf(word) >= 0));
        if (out) {
            l.add(item.user.id);
        }
        return out || callback(item);
    });
}

export function cmpOneNull(first, second) {
    if (first == null && second == null) {
        return 0;
    } else if (first == null) {
        return -1;
    } else if (second == null) {
        return 1;
    }
    return null;
}

export function cmpNoCase(first, second) {
    return first.toLowerCase().localeCompare(second.toLowerCase());
}

export function sortSubmissions(a, b, sortBy) {
    if (sortBy === 'user' || sortBy === 'assignee') {
        const first = a[sortBy];
        const second = b[sortBy];

        const ret = cmpOneNull(first, second);
        if (ret !== null) return ret;

        return cmpNoCase(first.name, second.name);
    } else if (sortBy === 'created_at') {
        const first = a[sortBy];
        const second = b[sortBy];

        const ret = cmpOneNull(first, second);
        if (ret !== null) return ret;

        return cmpNoCase(first, second);
    } else if (sortBy === 'grade') {
        const first = a[sortBy];
        const second = b[sortBy];

        let ret = cmpOneNull(first, second);
        if (ret !== null) return ret;

        const firstF = parseFloat(first);
        const secondF = parseFloat(second);

        ret = cmpOneNull(firstF, secondF);
        if (ret !== null) return ret;

        return firstF - secondF;
    }

    return 0;
}

/**
 * Parse the given value as a boolean.
 * If it is a boolean return it, if it is 'false' or 'true' convert
 * that to its correct boolean value, otherwise return `dflt`.
 */
export function parseBool(value, dflt = true) {
    if ((typeof value) === 'boolean') return value;
    else if (value === 'false') return false;
    else if (value === 'true') return true;

    return dflt;
}

export function convertToUTC(timeStr) {
    return moment(timeStr, moment.ISO_8601).utc().format('YYYY-MM-DDTHH:mm');
}

export function parseWarningHeader(warningStr) {
    const arr = warningStr.split(' ');

    const code = parseFloat(arr[0]);
    const agent = arr[1];
    const text = arr.slice(2).join(' ').replace(/\\"/g, '"').slice(1, -1);

    return { code, agent, text };
}
