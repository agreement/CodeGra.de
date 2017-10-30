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

        const ret = cmpOneNull(first, second);
        if (ret !== null) return ret;

        return cmpNoCase(formatGrade(first), formatGrade(second));
    }

    return 0;
}
