// eslint-disable-next-line
export function formatGrade(grade) {
    const g = parseFloat(grade);
    return Number.isNaN(g) ? null : g.toFixed(2);
}
