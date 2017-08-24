export const pageTitleSep = '»';

export function setPageTitle(title = '') {
    let s = title;
    if (s) s += ` ${pageTitleSep} `;
    document.title = `${s}CodeGra.de`;
}
