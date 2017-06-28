export const titleSep = '»';

export function setTitle(title = '') {
    let s = title;
    if (s) s += ` ${titleSep} `;
    document.title = `${s}CodeGra.de`;
}
