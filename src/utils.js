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
    let latestSubs = submissions;

    // BLAZE IT: R y a n C e l s i u s ° S o u n d s
    if (latest) {
        latestSubs = submissions.filter((item) => {
            if (l.has(item.user.id)) {
                return callback(item);
            } else {
                l.add(item.user.id);
                return true;
            }
        });
    }

    const filterAssignee = latestSubs.some(s => s.assignee &&
                                            s.assignee.id === userId);


    return latestSubs.filter((item) => {
        if (filterAssignee && mine &&
             (item.assignee == null || item.assignee.id !== userId)) {
            return callback(item);
        } else if (!filter) {
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
    return first.toLocaleLowerCase().localeCompare(second.toLocaleLowerCase());
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

export function partial(func, ...boundArgs) {
    return function partialFn(...args) {
        return func(...boundArgs, ...args);
    };
}

export function formatDate(date) {
    return moment.utc(date, moment.ISO_8601).local().format('YYYY-MM-DDTHH:mm');
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

export function waitAtLeast(time, ...promises) {
    const timeout = new Promise(resolve => setTimeout(resolve, time));

    return Promise.all([timeout, ...promises]).then((vals) => {
        if (promises.length === 1) {
            return vals[1];
        } else {
            return vals.slice(1);
        }
    });
}

//
const eightSpaces = `<span class="whitespace space" data-whitespace="${Array(8 + 1).join('&middot;')}">${Array(8 + 1).join(' ')}</span><wbr>`;

export function visualizeWhitespace(line) {
    const newLine = [];

    for (let i = 0; i < line.length;) {
        const start = i;
        if (line[i] === '<') {
            while (line[i] !== '>' && i < line.length) i += 1;
            newLine.push(line.slice(start, i + 1));
            i += 1;
        } else if (line[i] === ' ') {
            while (line[i] === ' ' && i < line.length) i += 1;

            let n = i - start;
            while (n >= 8) {
                newLine.push(eightSpaces);
                n -= 8;
            }
            if (n > 0) {
                const arr = Array(n + 1);
                newLine.push(`<span class="whitespace space" data-whitespace="${arr.join('&middot;')}">${arr.join(' ')}</span><wbr>`);
            }
        } else if (line[i] === '\t') {
            while (line[i] === '\t' && i < line.length) i += 1;

            const arr = Array((i - start) + 1);
            newLine.push(`<span class="whitespace tab" data-whitespace="${arr.join('&#8594;\t')}">${arr.join('\t')}</span><wbr>`);
        } else {
            while (line[i] !== '<' && line[i] !== ' ' && line[i] !== '\t' && i < line.length) i += 1;
            newLine.push(line.slice(start, i));
        }
    }
    return newLine.join('');
}

export function getExtension(name) {
    const fileParts = name.split('.');
    return fileParts.length > 1 ? fileParts[fileParts.length - 1] : null;
}

export function last(arr) {
    return arr[arr.length - 1];
}

export function range(start, end) {
    const len = end - start;
    const res = Array(len);
    for (let i = 0; i < len; ++i) {
        res[i] = start + i;
    }
    return res;
}
