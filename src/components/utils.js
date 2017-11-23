// eslint-disable-next-line
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
            newLine.push(`<span class="whitespace space">${Array((i - start) + 1).join('&middot;')}</span><wbr>`);
        } else if (line[i] === '\t') {
            while (line[i] === '\t' && i < line.length) i += 1;
            newLine.push(`<span class="whitespace tab">${Array((i - start) + 1).join('&#10230;   ')}</span><wbr>`);
        } else {
            while (line[i] !== '<' && line[i] !== ' ' && line[i] !== '\t' && i < line.length) i += 1;
            newLine.push(line.slice(start, i));
        }
    }
    return newLine.join('');
}
