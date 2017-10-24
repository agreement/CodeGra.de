export function formatGrade(grade) {
    const g = parseFloat(grade);
    return Number.isNaN(g) ? null : g.toFixed(2);
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
